from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models import (
    User, Course, Examination, ExaminationRubric,
    ExaminationSlot, Booking, Evaluation, EvaluationDetail
)
from app.routes.decorators import admin_required
from app.services import ExaminationService, BookingService, EvaluationService

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
@admin_required
def before_admin_request():
    pass

# --- Dashboard ---
@admin_bp.route('/')
@admin_bp.route('/dashboard')
def dashboard():
    ExaminationService.update_status_automatically()
    total_courses = Course.query.count()
    total_examinations = Examination.query.count()
    total_examiners = User.query.filter_by(role='examiner').count()
    pending_examiners = User.query.filter_by(role='examiner', status='pending').count()
    total_students = User.query.filter_by(role='student').count()
    total_slots = ExaminationSlot.query.count()
    total_bookings = Booking.query.count()
    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(8).all()
    recent_examinations = Examination.query.order_by(Examination.created_at.desc()).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        total_courses=total_courses,
        total_examinations=total_examinations,
        total_examiners=total_examiners,
        pending_examiners=pending_examiners,
        total_students=total_students,
        total_slots=total_slots,
        total_bookings=total_bookings,
        recent_bookings=recent_bookings,
        recent_examinations=recent_examinations
    )

# --- Course Management ---
@admin_bp.route('/courses')
def courses():
    q = request.args.get('q', '').strip()
    status = request.args.get('status', '')
    query = Course.query
    if q:
        query = query.filter(
            (Course.course_code.ilike(f'%{q}%')) | (Course.course_name.ilike(f'%{q}%'))
        )
    if status:
        query = query.filter_by(status=status)
    courses_list = query.order_by(Course.course_code.asc()).all()
    return render_template('admin/courses.html', courses=courses_list, q=q, status=status)

@admin_bp.route('/courses/new', methods=['GET', 'POST'])
def new_course():
    if request.method == 'POST':
        code = request.form.get('course_code', '').strip().upper()
        name = request.form.get('course_name', '').strip()
        description = request.form.get('description', '').strip()
        status = request.form.get('status', 'Active')

        if not code or not name:
            flash('Course Code and Course Name are required.', 'warning')
            return render_template('admin/course_form.html', action='Create', course=None)

        if Course.query.filter_by(course_code=code).first():
            flash(f"A course with code '{code}' already exists.", 'danger')
            return render_template('admin/course_form.html', action='Create', course=None)

        course = Course(
            course_code=code,
            course_name=name,
            description=description or None,
            status=status
        )
        db.session.add(course)
        db.session.commit()
        flash(f"Course '{code} - {name}' created successfully.", 'success')
        return redirect(url_for('admin.courses'))

    return render_template('admin/course_form.html', action='Create', course=None)

@admin_bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        code = request.form.get('course_code', '').strip().upper()
        name = request.form.get('course_name', '').strip()
        description = request.form.get('description', '').strip()
        status = request.form.get('status', 'Active')

        if not code or not name:
            flash('Course Code and Course Name are required.', 'warning')
            return render_template('admin/course_form.html', action='Edit', course=course)

        existing = Course.query.filter_by(course_code=code).first()
        if existing and existing.id != course.id:
            flash(f"Another course with code '{code}' already exists.", 'danger')
            return render_template('admin/course_form.html', action='Edit', course=course)

        course.course_code = code
        course.course_name = name
        course.description = description or None
        course.status = status
        db.session.commit()
        flash(f"Course '{course.course_code}' updated successfully.", 'success')
        return redirect(url_for('admin.courses'))

    return render_template('admin/course_form.html', action='Edit', course=course)

@admin_bp.route('/courses/<int:course_id>/toggle-status', methods=['POST'])
def toggle_course_status(course_id):
    course = Course.query.get_or_404(course_id)
    course.status = 'Inactive' if course.status == 'Active' else 'Active'
    db.session.commit()
    flash(f"Course '{course.course_code}' status updated to {course.status}.", 'info')
    return redirect(url_for('admin.courses'))

@admin_bp.route('/courses/<int:course_id>/delete', methods=['POST'])
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    if course.examinations.count() > 0:
        flash(f"Cannot delete course '{course.course_code}' because examinations are associated with it. Deactivate instead.", 'danger')
        return redirect(url_for('admin.courses'))
    db.session.delete(course)
    db.session.commit()
    flash(f"Course '{course.course_code}' deleted successfully.", 'success')
    return redirect(url_for('admin.courses'))

# --- Examination Management ---
@admin_bp.route('/examinations')
def examinations():
    ExaminationService.update_status_automatically()
    q = request.args.get('q', '').strip()
    course_id = request.args.get('course_id', type=int)
    status = request.args.get('status', '')
    exam_type = request.args.get('type', '')

    query = Examination.query
    if q:
        query = query.filter(
            (Examination.examination_name.ilike(f'%{q}%')) |
            (Examination.id == int(q) if q.isdigit() else False)
        )
    if course_id:
        query = query.filter_by(course_id=course_id)
    if status:
        query = query.filter_by(status=status)
    if exam_type:
        query = query.filter_by(examination_type=exam_type)

    exams_list = query.order_by(Examination.created_at.desc()).all()
    courses_list = Course.query.order_by(Course.course_code.asc()).all()
    return render_template(
        'admin/examinations.html',
        examinations=exams_list,
        courses=courses_list,
        q=q,
        course_id=course_id,
        status=status,
        exam_type=exam_type
    )

@admin_bp.route('/examinations/new', methods=['GET', 'POST'])
def new_examination():
    courses_list = Course.query.filter_by(status='Active').order_by(Course.course_code.asc()).all()
    if request.method == 'POST':
        try:
            course_id = int(request.form.get('course_id', 0))
            name = request.form.get('examination_name', '').strip()
            exam_type = request.form.get('examination_type', 'Viva')
            duration = int(request.form.get('duration', 30))
            maximum_marks = float(request.form.get('maximum_marks', 100))
            slot_creation_start = datetime.strptime(request.form.get('slot_creation_start'), '%Y-%m-%dT%H:%M')
            slot_creation_end = datetime.strptime(request.form.get('slot_creation_end'), '%Y-%m-%dT%H:%M')
            slot_booking_start = datetime.strptime(request.form.get('slot_booking_start'), '%Y-%m-%dT%H:%M')
            slot_booking_end = datetime.strptime(request.form.get('slot_booking_end'), '%Y-%m-%dT%H:%M')
            status = request.form.get('status', 'Draft')

            exam = ExaminationService.create_examination(
                course_id=course_id,
                examination_name=name,
                examination_type=exam_type,
                duration=duration,
                maximum_marks=maximum_marks,
                slot_creation_start=slot_creation_start,
                slot_creation_end=slot_creation_end,
                slot_booking_start=slot_booking_start,
                slot_booking_end=slot_booking_end,
                status=status
            )
            flash(f"Examination '{exam.examination_name}' created successfully.", 'success')
            return redirect(url_for('admin.view_examination', exam_id=exam.id))
        except Exception as e:
            flash(f"Error creating examination: {str(e)}", 'danger')

    return render_template('admin/examination_form.html', action='Create', exam=None, courses=courses_list)

@admin_bp.route('/examinations/<int:exam_id>')
def view_examination(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    available_examiners = User.query.filter_by(role='examiner', status='approved').order_by(User.full_name.asc()).all()
    slots = exam.slots.order_by(ExaminationSlot.examination_date.asc(), ExaminationSlot.start_time.asc()).all()
    bookings = exam.bookings.order_by(Booking.booking_date.desc()).all()
    return render_template(
        'admin/examination_detail.html',
        exam=exam,
        available_examiners=available_examiners,
        slots=slots,
        bookings=bookings
    )

@admin_bp.route('/examinations/<int:exam_id>/edit', methods=['GET', 'POST'])
def edit_examination(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    courses_list = Course.query.filter_by(status='Active').order_by(Course.course_code.asc()).all()

    if request.method == 'POST':
        try:
            course_id = int(request.form.get('course_id'))
            name = request.form.get('examination_name', '').strip()
            exam_type = request.form.get('examination_type')
            duration = int(request.form.get('duration'))
            maximum_marks = float(request.form.get('maximum_marks'))
            slot_creation_start = datetime.strptime(request.form.get('slot_creation_start'), '%Y-%m-%dT%H:%M')
            slot_creation_end = datetime.strptime(request.form.get('slot_creation_end'), '%Y-%m-%dT%H:%M')
            slot_booking_start = datetime.strptime(request.form.get('slot_booking_start'), '%Y-%m-%dT%H:%M')
            slot_booking_end = datetime.strptime(request.form.get('slot_booking_end'), '%Y-%m-%dT%H:%M')
            status = request.form.get('status')

            ExaminationService.update_examination(
                exam_id=exam.id,
                course_id=course_id,
                examination_name=name,
                examination_type=exam_type,
                duration=duration,
                maximum_marks=maximum_marks,
                slot_creation_start=slot_creation_start,
                slot_creation_end=slot_creation_end,
                slot_booking_start=slot_booking_start,
                slot_booking_end=slot_booking_end,
                status=status
            )
            flash(f"Examination '{name}' updated successfully.", 'success')
            return redirect(url_for('admin.view_examination', exam_id=exam.id))
        except Exception as e:
            flash(f"Error updating examination: {str(e)}", 'danger')

    return render_template('admin/examination_form.html', action='Edit', exam=exam, courses=courses_list)

@admin_bp.route('/examinations/<int:exam_id>/status', methods=['POST'])
def set_examination_status(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    new_status = request.form.get('status')
    if new_status in ['Draft', 'Slot Creation', 'Booking Open', 'Closed', 'Completed']:
        exam.status = new_status
        db.session.commit()
        flash(f"Status changed to '{new_status}'.", 'success')
    return redirect(url_for('admin.view_examination', exam_id=exam.id))

@admin_bp.route('/examinations/<int:exam_id>/assign-examiners', methods=['POST'])
def assign_examiners(exam_id):
    examiner_ids = request.form.getlist('examiner_ids', type=int)
    try:
        ExaminationService.assign_examiners(exam_id, examiner_ids)
        flash("Assigned examiners updated successfully.", 'success')
    except Exception as e:
        flash(f"Error assigning examiners: {str(e)}", 'danger')
    return redirect(url_for('admin.view_examination', exam_id=exam_id))

@admin_bp.route('/examinations/<int:exam_id>/delete', methods=['POST'])
def delete_examination(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    if exam.bookings.filter_by(status='Booked').count() > 0:
        flash("Cannot delete an examination with active student bookings.", 'danger')
        return redirect(url_for('admin.view_examination', exam_id=exam.id))
    db.session.delete(exam)
    db.session.commit()
    flash("Examination deleted successfully.", 'success')
    return redirect(url_for('admin.examinations'))

# --- Rubric Management ---
@admin_bp.route('/examinations/<int:exam_id>/rubrics/new', methods=['POST'])
def add_rubric(exam_id):
    criterion_name = request.form.get('criterion_name', '').strip()
    maximum_marks = request.form.get('maximum_marks', type=float)
    weightage = request.form.get('weightage', default=1.0, type=float)
    description = request.form.get('description', '').strip()

    if not criterion_name or maximum_marks is None or maximum_marks <= 0:
        flash("Valid criterion name and positive maximum marks are required.", 'warning')
        return redirect(url_for('admin.view_examination', exam_id=exam_id))

    try:
        ExaminationService.add_rubric(
            exam_id=exam_id,
            criterion_name=criterion_name,
            maximum_marks=maximum_marks,
            weightage=weightage,
            description=description or None
        )
        flash(f"Criterion '{criterion_name}' added to rubrics.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding rubric: {str(e)}", 'danger')



    return redirect(url_for('admin.view_examination', exam_id=exam_id))


@admin_bp.route('/rubrics/<int:rubric_id>/edit', methods=['POST'])
def edit_rubric(rubric_id):
    rubric = ExaminationRubric.query.get_or_404(rubric_id)
    exam = rubric.examination
    criterion_name = request.form.get('criterion_name', '').strip()
    maximum_marks = request.form.get('maximum_marks', type=float)
    weightage = request.form.get('weightage', default=1.0, type=float)
    description = request.form.get('description', '').strip()

    if not criterion_name or maximum_marks is None or maximum_marks <= 0:
        flash("Valid criterion name and maximum marks required.", 'warning')
        return redirect(url_for('admin.view_examination', exam_id=exam.id))

    # Check sum of marks
    other_total = sum(r.maximum_marks for r in exam.rubrics if r.id != rubric.id)
    if other_total + maximum_marks > exam.maximum_marks:
        flash(f"Total rubric marks ({other_total + maximum_marks}) cannot exceed exam maximum marks ({exam.maximum_marks}).", 'danger')
        return redirect(url_for('admin.view_examination', exam_id=exam.id))

    rubric.criterion_name = criterion_name
    rubric.maximum_marks = maximum_marks
    rubric.weightage = weightage
    rubric.description = description or None
    db.session.commit()
    flash(f"Criterion '{criterion_name}' updated successfully.", 'success')
    return redirect(url_for('admin.view_examination', exam_id=exam.id))

@admin_bp.route('/rubrics/<int:rubric_id>/delete', methods=['POST'])
def delete_rubric(rubric_id):
    rubric = ExaminationRubric.query.get_or_404(rubric_id)
    exam_id = rubric.examination_id
    try:
        ExaminationService.delete_rubric(rubric_id)
        flash("Rubric criterion deleted successfully.", 'success')
    except Exception as e:
        flash(f"Error deleting rubric: {str(e)}", 'danger')
    return redirect(url_for('admin.view_examination', exam_id=exam_id))

# --- Examiner Management ---
@admin_bp.route('/examiners')
def examiners():
    status = request.args.get('status', '')
    q = request.args.get('q', '').strip()
    query = User.query.filter_by(role='examiner')
    if status:
        query = query.filter_by(status=status)
    if q:
        query = query.filter(
            (User.full_name.ilike(f'%{q}%')) |
            (User.email.ilike(f'%{q}%')) |
            (User.department.ilike(f'%{q}%'))
        )
    examiners_list = query.order_by(User.created_at.desc()).all()
    return render_template('admin/examiners.html', examiners=examiners_list, status=status, q=q)

@admin_bp.route('/examiners/<int:user_id>/approve', methods=['POST'])
def approve_examiner(user_id):
    examiner = User.query.filter_by(id=user_id, role='examiner').first_or_404()
    examiner.status = 'approved'
    db.session.commit()
    flash(f"Examiner {examiner.full_name} ({examiner.email}) has been approved.", 'success')
    return redirect(url_for('admin.examiners'))

@admin_bp.route('/examiners/<int:user_id>/reject', methods=['POST'])
def reject_examiner(user_id):
    examiner = User.query.filter_by(id=user_id, role='examiner').first_or_404()
    examiner.status = 'rejected'
    db.session.commit()
    flash(f"Examiner {examiner.full_name} registration has been rejected.", 'warning')
    return redirect(url_for('admin.examiners'))

@admin_bp.route('/examiners/<int:user_id>/deactivate', methods=['POST'])
def deactivate_examiner(user_id):
    examiner = User.query.filter_by(id=user_id, role='examiner').first_or_404()
    examiner.status = 'deactivated'
    db.session.commit()
    flash(f"Examiner {examiner.full_name} has been deactivated.", 'warning')
    return redirect(url_for('admin.examiners'))

@admin_bp.route('/examiners/<int:user_id>/activate', methods=['POST'])
def activate_examiner(user_id):
    examiner = User.query.filter_by(id=user_id, role='examiner').first_or_404()
    examiner.status = 'approved'
    db.session.commit()
    flash(f"Examiner {examiner.full_name} has been reactivated.", 'success')
    return redirect(url_for('admin.examiners'))

# --- Student Management ---
@admin_bp.route('/students')
def students():
    q = request.args.get('q', '').strip()
    status = request.args.get('status', '')
    query = User.query.filter_by(role='student')
    if q:
        query = query.filter(
            (User.full_name.ilike(f'%{q}%')) |
            (User.email.ilike(f'%{q}%')) |
            (User.department.ilike(f'%{q}%'))
        )
    if status:
        query = query.filter_by(status=status)
    students_list = query.order_by(User.full_name.asc()).all()
    return render_template('admin/students.html', students=students_list, q=q, status=status)

@admin_bp.route('/students/<int:user_id>/toggle-status', methods=['POST'])
def toggle_student_status(user_id):
    student = User.query.filter_by(id=user_id, role='student').first_or_404()
    student.status = 'deactivated' if student.status == 'active' else 'active'
    db.session.commit()
    flash(f"Student {student.full_name} status updated to '{student.status}'.", 'info')
    return redirect(url_for('admin.students'))

# --- Booking Management & Search ---
@admin_bp.route('/bookings')
def bookings():
    q = request.args.get('q', '').strip()
    status = request.args.get('status', '')
    exam_id = request.args.get('exam_id', type=int)

    query = Booking.query.join(User, Booking.student_id == User.id).join(Examination, Booking.examination_id == Examination.id)
    if q:
        query = query.filter(
            (User.full_name.ilike(f'%{q}%')) |
            (User.email.ilike(f'%{q}%')) |
            (Examination.examination_name.ilike(f'%{q}%')) |
            (Booking.id == int(q) if q.isdigit() else False) |
            (User.id == int(q) if q.isdigit() else False)
        )
    if status:
        query = query.filter(Booking.status == status)
    if exam_id:
        query = query.filter(Booking.examination_id == exam_id)

    bookings_list = query.order_by(Booking.booking_date.desc()).all()
    all_exams = Examination.query.order_by(Examination.examination_name.asc()).all()

    return render_template(
        'admin/bookings.html',
        bookings=bookings_list,
        examinations=all_exams,
        q=q,
        status=status,
        exam_id=exam_id
    )

@admin_bp.route('/bookings/<int:booking_id>/reschedule', methods=['GET', 'POST'])
def reschedule_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    exam = booking.examination
    available_slots = exam.slots.filter(
        ExaminationSlot.id != booking.slot_id,
        ExaminationSlot.status == 'Available',
        ExaminationSlot.available_seats > 0
    ).order_by(ExaminationSlot.examination_date.asc(), ExaminationSlot.start_time.asc()).all()

    if request.method == 'POST':
        target_slot_id = request.form.get('target_slot_id', type=int)
        try:
            BookingService.reschedule_booking(booking.id, target_slot_id, current_user)
            flash("Booking rescheduled successfully.", 'success')
            return redirect(url_for('admin.bookings'))
        except Exception as e:
            flash(f"Rescheduling error: {str(e)}", 'danger')

    return render_template('admin/reschedule_booking.html', booking=booking, available_slots=available_slots)

@admin_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
def cancel_booking(booking_id):
    try:
        BookingService.cancel_booking(booking_id, user=current_user, is_admin=True)
        flash("Booking cancelled by administrator.", 'success')
    except Exception as e:
        flash(f"Error cancelling booking: {str(e)}", 'danger')
    return redirect(url_for('admin.bookings'))

# --- Examiner Reassignment ---
@admin_bp.route('/slots/<int:slot_id>/reassign', methods=['POST'])
def reassign_slot_examiner(slot_id):
    new_examiner_id = request.form.get('new_examiner_id', type=int)
    slot = ExaminationSlot.query.get_or_404(slot_id)
    try:
        BookingService.reassign_examiner(slot_id, new_examiner_id, current_user)
        flash("Examiner reassigned successfully.", 'success')
    except Exception as e:
        flash(f"Reassignment error: {str(e)}", 'danger')
    return redirect(url_for('admin.view_examination', exam_id=slot.examination_id))

# --- Evaluation Publication ---
@admin_bp.route('/evaluations/<int:eval_id>/publish', methods=['POST'])
def publish_evaluation(eval_id):
    try:
        EvaluationService.publish_evaluation(eval_id, current_user)
        flash("Evaluation published successfully. Student can now see results.", 'success')
    except Exception as e:
        flash(f"Error: {str(e)}", 'danger')
    return redirect(request.referrer or url_for('admin.bookings'))

@admin_bp.route('/evaluations/<int:eval_id>/unpublish', methods=['POST'])
def unpublish_evaluation(eval_id):
    try:
        EvaluationService.unpublish_evaluation(eval_id, current_user)
        flash("Evaluation unpublished. Student marks withheld.", 'info')
    except Exception as e:
        flash(f"Error: {str(e)}", 'danger')
    return redirect(request.referrer or url_for('admin.bookings'))
