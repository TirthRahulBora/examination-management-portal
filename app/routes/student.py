from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import (
    User, Course, Examination, ExaminationSlot, Booking, Evaluation
)
from app.routes.decorators import student_required
from app.services import BookingService, ExaminationService

student_bp = Blueprint('student', __name__)

@student_bp.before_request
@login_required
@student_required
def before_student_request():
    pass

# --- Dashboard ---
@student_bp.route('/')
@student_bp.route('/dashboard')
def dashboard():
    ExaminationService.update_status_automatically()
    now = datetime.utcnow()

    # Active bookings
    active_bookings = Booking.query.filter_by(
        student_id=current_user.id,
        status='Booked'
    ).join(ExaminationSlot).order_by(
        ExaminationSlot.examination_date.asc(),
        ExaminationSlot.start_time.asc()
    ).all()

    # Completed bookings
    completed_bookings = Booking.query.filter_by(
        student_id=current_user.id,
        status='Completed'
    ).all()

    # Available examinations open for booking
    open_exams = Examination.query.filter(
        Examination.status.in_(['Booking Open', 'Slot Creation']),
        Examination.slot_booking_start <= now,
        Examination.slot_booking_end >= now
    ).order_by(Examination.slot_booking_end.asc()).all()

    # Published results
    published_evaluations = Evaluation.query.join(Booking).filter(
        Booking.student_id == current_user.id,
        Evaluation.publication_status == 'Published'
    ).order_by(Evaluation.evaluation_date.desc()).all()

    # Active booking exam IDs
    booked_exam_ids = {b.examination_id for b in active_bookings}

    return render_template(
        'student/dashboard.html',
        active_bookings=active_bookings,
        completed_count=len(completed_bookings),
        open_exams=open_exams,
        published_evaluations=published_evaluations,
        booked_exam_ids=booked_exam_ids,
        now=now
    )

# --- Browse Examinations ---
@student_bp.route('/examinations')
def examinations():
    ExaminationService.update_status_automatically()
    q = request.args.get('q', '').strip()
    course_id = request.args.get('course_id', type=int)
    exam_type = request.args.get('type', '')
    now = datetime.utcnow()

    query = Examination.query.filter(Examination.status != 'Draft')
    if q:
        query = query.filter(Examination.examination_name.ilike(f'%{q}%'))
    if course_id:
        query = query.filter_by(course_id=course_id)
    if exam_type:
        query = query.filter_by(examination_type=exam_type)

    exams_list = query.order_by(Examination.created_at.desc()).all()
    courses_list = Course.query.filter_by(status='Active').order_by(Course.course_code.asc()).all()

    # Determine which examinations student has already booked
    student_active_bookings = Booking.query.filter_by(
        student_id=current_user.id,
        status='Booked'
    ).all()
    booked_exam_ids = {b.examination_id for b in student_active_bookings}

    return render_template(
        'student/examinations.html',
        examinations=exams_list,
        courses=courses_list,
        booked_exam_ids=booked_exam_ids,
        q=q,
        course_id=course_id,
        exam_type=exam_type,
        now=now
    )

@student_bp.route('/examinations/<int:exam_id>')
def view_examination(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    now = datetime.utcnow()
    existing_booking = Booking.query.filter_by(
        student_id=current_user.id,
        examination_id=exam.id,
        status='Booked'
    ).first()
    
    available_slots = exam.slots.filter(
        ExaminationSlot.status == 'Available',
        ExaminationSlot.available_seats > 0
    ).order_by(ExaminationSlot.examination_date.asc(), ExaminationSlot.start_time.asc()).all()

    return render_template(
        'student/examination_detail.html',
        exam=exam,
        existing_booking=existing_booking,
        available_slots=available_slots,
        now=now
    )

# --- Slot Booking ---
@student_bp.route('/slots/<int:slot_id>/book', methods=['POST'])
def book_slot(slot_id):
    try:
        booking = BookingService.book_slot(student_id=current_user.id, slot_id=slot_id)
        flash(f"Slot successfully booked for {booking.examination.examination_name}!", 'success')
        return redirect(url_for('student.bookings'))
    except Exception as e:
        flash(f"Booking failed: {str(e)}", 'danger')
        slot = ExaminationSlot.query.get(slot_id)
        if slot:
            return redirect(url_for('student.view_examination', exam_id=slot.examination_id))
        return redirect(url_for('student.examinations'))

# --- Booking Management & History ---
@student_bp.route('/bookings')
def bookings():
    now = datetime.utcnow()
    user_bookings = Booking.query.filter_by(student_id=current_user.id).order_by(
        Booking.booking_date.desc()
    ).all()
    return render_template('student/bookings.html', bookings=user_bookings, now=now)

@student_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
def cancel_booking(booking_id):
    try:
        BookingService.cancel_booking(booking_id=booking_id, user=current_user, is_admin=False)
        flash("Your examination booking has been cancelled successfully.", 'success')
    except Exception as e:
        flash(f"Cancellation failed: {str(e)}", 'danger')
    return redirect(url_for('student.bookings'))

# --- Results ---
@student_bp.route('/results')
def results():
    evaluations = Evaluation.query.join(Booking).filter(
        Booking.student_id == current_user.id,
        Evaluation.publication_status == 'Published'
    ).order_by(Evaluation.evaluation_date.desc()).all()
    return render_template('student/results.html', evaluations=evaluations)

@student_bp.route('/results/<int:eval_id>')
def view_result_card(eval_id):
    evaluation = Evaluation.query.get_or_404(eval_id)
    if evaluation.booking.student_id != current_user.id:
        flash("Access forbidden.", 'danger')
        return redirect(url_for('student.results'))
    if not evaluation.is_published:
        flash("This evaluation result is not yet published.", 'warning')
        return redirect(url_for('student.results'))
    return render_template('student/result_card.html', evaluation=evaluation)

# --- Profile ---
@student_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        department = request.form.get('department', '').strip()
        contact_number = request.form.get('contact_number', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not full_name:
            flash("Full name cannot be blank.", 'warning')
            return render_template('student/profile.html')

        current_user.full_name = full_name
        current_user.department = department or None
        current_user.contact_number = contact_number or None

        if new_password:
            if len(new_password) < 6:
                flash("New password must be at least 6 characters.", 'warning')
                return render_template('student/profile.html')
            if new_password != confirm_password:
                flash("New passwords do not match.", 'danger')
                return render_template('student/profile.html')
            current_user.set_password(new_password)

        db.session.commit()
        flash("Profile updated successfully.", 'success')
        return redirect(url_for('student.profile'))

    return render_template('student/profile.html')
