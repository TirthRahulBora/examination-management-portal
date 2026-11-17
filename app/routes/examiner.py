from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models import (
    Examination, ExaminationSlot, Booking, Evaluation, ExaminationRubric
)
from app.routes.decorators import examiner_required
from app.services import BookingService, EvaluationService, ExaminationService

examiner_bp = Blueprint('examiner', __name__)

@examiner_bp.before_request
@login_required
@examiner_required
def before_examiner_request():
    pass

# --- Dashboard ---
@examiner_bp.route('/')
@examiner_bp.route('/dashboard')
def dashboard():
    ExaminationService.update_status_automatically()
    assigned_exams = current_user.assigned_examinations
    created_slots = ExaminationSlot.query.filter_by(examiner_id=current_user.id).order_by(
        ExaminationSlot.examination_date.asc(), ExaminationSlot.start_time.asc()
    ).all()
    
    slot_ids = [s.id for s in created_slots]
    booked_students_count = Booking.query.filter(Booking.slot_id.in_(slot_ids), Booking.status == 'Booked').count() if slot_ids else 0
    
    # Active bookings in examiner's slots
    active_bookings = Booking.query.filter(
        Booking.slot_id.in_(slot_ids),
        Booking.status.in_(['Booked', 'Completed'])
    ).all() if slot_ids else []

    pending_evaluations = [b for b in active_bookings if not b.evaluation or b.evaluation.publication_status == 'Draft']
    completed_evaluations = [b for b in active_bookings if b.evaluation and b.evaluation.publication_status == 'Published']

    return render_template(
        'examiner/dashboard.html',
        assigned_exams=assigned_exams,
        created_slots=created_slots,
        booked_students_count=booked_students_count,
        pending_evaluations_count=len(pending_evaluations),
        completed_evaluations_count=len(completed_evaluations),
        pending_evaluations=pending_evaluations[:5],
        recent_slots=created_slots[:5]
    )

# --- Assigned Examinations ---
@examiner_bp.route('/examinations')
def examinations():
    ExaminationService.update_status_automatically()
    assigned_exams = current_user.assigned_examinations
    now = datetime.utcnow()
    return render_template('examiner/examinations.html', examinations=assigned_exams, now=now)

# --- Slots Management ---
@examiner_bp.route('/slots')
def slots():
    examiner_slots = ExaminationSlot.query.filter_by(examiner_id=current_user.id).order_by(
        ExaminationSlot.examination_date.desc(), ExaminationSlot.start_time.desc()
    ).all()
    now = datetime.utcnow()
    return render_template('examiner/slots.html', slots=examiner_slots, now=now)

@examiner_bp.route('/examinations/<int:exam_id>/slots/new', methods=['GET', 'POST'])
def new_slot(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    if exam not in current_user.assigned_examinations:
        flash("You are not assigned to this examination.", 'danger')
        return redirect(url_for('examiner.examinations'))

    now = datetime.utcnow()
    if not exam.is_in_slot_creation_period(now):
        flash(f"Slot creation period is not active for this examination (Window: {exam.slot_creation_start.strftime('%Y-%m-%d %H:%M')} to {exam.slot_creation_end.strftime('%Y-%m-%d %H:%M')}).", 'warning')
        return redirect(url_for('examiner.examinations'))

    if request.method == 'POST':
        try:
            date_str = request.form.get('examination_date')
            start_str = request.form.get('start_time')
            end_str = request.form.get('end_time')
            capacity = int(request.form.get('maximum_capacity', 1))

            exam_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_str, '%H:%M').time()
            end_time = datetime.strptime(end_str, '%H:%M').time()

            BookingService.create_slot(
                examiner=current_user,
                exam_id=exam.id,
                exam_date=exam_date,
                start_time=start_time,
                end_time=end_time,
                maximum_capacity=capacity
            )
            flash("Examination slot created successfully.", 'success')
            return redirect(url_for('examiner.slots'))
        except Exception as e:
            flash(f"Error creating slot: {str(e)}", 'danger')

    return render_template('examiner/slot_form.html', action='Create', exam=exam, slot=None)

@examiner_bp.route('/slots/<int:slot_id>/edit', methods=['GET', 'POST'])
def edit_slot(slot_id):
    slot = ExaminationSlot.query.get_or_404(slot_id)
    if slot.examiner_id != current_user.id:
        abort(403)
    exam = slot.examination
    if request.method == 'POST':
        try:
            exam_date = datetime.strptime(request.form.get('examination_date', ''), '%Y-%m-%d').date()
            start_time = datetime.strptime(request.form.get('start_time', ''), '%H:%M').time()
            end_time = datetime.strptime(request.form.get('end_time', ''), '%H:%M').time()
            capacity = int(request.form.get('maximum_capacity', '1'))
            BookingService.update_slot(slot.id, current_user, exam_date, start_time, end_time, capacity)
            flash("Examination slot updated successfully.", 'success')
            return redirect(url_for('examiner.slots'))
        except (ValueError, TypeError, PermissionError) as exc:
            flash(f"Error updating slot: {exc}", 'danger')
    return render_template('examiner/slot_form.html', action='Edit', exam=exam, slot=slot)

@examiner_bp.route('/slots/<int:slot_id>/delete', methods=['POST'])
def delete_slot(slot_id):
    try:
        BookingService.delete_slot(slot_id, examiner=current_user)
        flash("Slot deleted successfully.", 'success')
    except Exception as e:
        flash(f"Error deleting slot: {str(e)}", 'danger')
    return redirect(url_for('examiner.slots'))

@examiner_bp.route('/slots/<int:slot_id>/students')
def slot_students(slot_id):
    slot = ExaminationSlot.query.get_or_404(slot_id)
    if slot.examiner_id != current_user.id and not current_user.is_admin:
        abort(403)
    bookings = slot.bookings.order_by(Booking.booking_date.asc()).all()
    return render_template('examiner/slot_students.html', slot=slot, bookings=bookings)

# --- Student Evaluation ---
@examiner_bp.route('/bookings/<int:booking_id>/evaluate', methods=['GET', 'POST'])
def evaluate_student(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    # Security check: only slot owner can evaluate
    if booking.slot.examiner_id != current_user.id and not current_user.is_admin:
        flash("Access forbidden: You cannot evaluate students booked in another examiner's slot.", 'danger')
        abort(403)

    if booking.status not in ['Booked', 'Completed']:
        flash(f"Cannot evaluate student because booking status is '{booking.status}'.", 'warning')
        return redirect(url_for('examiner.dashboard'))

    exam = booking.examination
    evaluation = booking.evaluation

    # If already published, examiner cannot modify
    if evaluation and evaluation.is_published and not current_user.is_admin:
        flash("This evaluation has been published and finalized.", 'info')

    if request.method == 'POST':
        try:
            scores = {}
            for rubric in exam.rubrics:
                val = request.form.get(f"rubric_{rubric.id}", 0)
                scores[rubric.id] = float(val)

            remarks = request.form.get('remarks', '')
            action = request.form.get('action', 'draft')
            publication_status = 'Published' if action == 'publish' else 'Draft'

            EvaluationService.submit_evaluation(
                examiner=current_user,
                booking_id=booking.id,
                rubric_scores=scores,
                remarks=remarks,
                publication_status=publication_status
            )
            flash(f"Evaluation saved successfully ({publication_status}).", 'success')
            return redirect(url_for('examiner.slot_students', slot_id=booking.slot_id))
        except Exception as e:
            flash(f"Evaluation error: {str(e)}", 'danger')

    # Pre-populate scores if evaluation already exists
    existing_scores = {}
    if evaluation:
        for detail in evaluation.details:
            existing_scores[detail.rubric_id] = detail.marks_awarded

    return render_template(
        'examiner/evaluate_student.html',
        booking=booking,
        exam=exam,
        evaluation=evaluation,
        existing_scores=existing_scores
    )

@examiner_bp.route('/evaluations')
def evaluations():
    """List all evaluations conducted by this examiner."""
    evals = Evaluation.query.filter_by(examiner_id=current_user.id).order_by(
        Evaluation.evaluation_date.desc()
    ).all()
    return render_template('examiner/evaluations.html', evaluations=evals)
