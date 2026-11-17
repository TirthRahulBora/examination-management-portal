import pytest
from datetime import datetime, date, time, timedelta
from app.models import User, Course, Examination, ExaminationSlot, Booking
from app.services import BookingService
from app.extensions import db

def test_overbooking_prevention(app, examiner_approved, sample_exam):
    # Create a slot with capacity of exactly 1
    slot = BookingService.create_slot(
        examiner=examiner_approved,
        exam_id=sample_exam.id,
        exam_date=date.today() + timedelta(days=2),
        start_time=time(9, 0),
        end_time=time(9, 30),
        maximum_capacity=1
    )
    assert slot.available_seats == 1
    assert slot.status == 'Available'

    # Create two students
    s1 = User(full_name='Student 1', email='s1@test.edu', role='student', status='active')
    s1.set_password('Pass123')
    s2 = User(full_name='Student 2', email='s2@test.edu', role='student', status='active')
    s2.set_password('Pass123')
    db.session.add_all([s1, s2])
    db.session.commit()

    # First booking succeeds
    b1 = BookingService.book_slot(student_id=s1.id, slot_id=slot.id)
    assert b1.status == 'Booked'

    s = db.session.get(ExaminationSlot, slot.id)
    assert s.available_seats == 0
    assert s.status == 'Full'

    # Second booking MUST raise ValueError and prevent overbooking
    with pytest.raises(ValueError, match="full or unavailable"):
        BookingService.book_slot(student_id=s2.id, slot_id=slot.id)

def test_duplicate_booking_prevention(app, examiner_approved, sample_exam):
    # Create two different slots for the SAME examination
    slot1 = BookingService.create_slot(
        examiner=examiner_approved,
        exam_id=sample_exam.id,
        exam_date=date.today() + timedelta(days=2),
        start_time=time(10, 0),
        end_time=time(10, 30),
        maximum_capacity=2
    )
    slot2 = BookingService.create_slot(
        examiner=examiner_approved,
        exam_id=sample_exam.id,
        exam_date=date.today() + timedelta(days=3),
        start_time=time(14, 0),
        end_time=time(14, 30),
        maximum_capacity=2
    )

    student = User(full_name='Greedy Student', email='greedy@test.edu', role='student', status='active')
    student.set_password('Pass123')
    db.session.add(student)
    db.session.commit()

    # Student books slot 1
    b1 = BookingService.book_slot(student_id=student.id, slot_id=slot1.id)
    assert b1.status == 'Booked'

    # Student tries to book slot 2 in the same exam -> must raise ValueError
    with pytest.raises(ValueError, match="Duplicate booking prohibited"):
        BookingService.book_slot(student_id=student.id, slot_id=slot2.id)

def test_booking_deadline_enforcement(app, examiner_approved, sample_course):
    now = datetime.utcnow()
    # Exam where booking window closed yesterday
    closed_exam = Examination(
        course_id=sample_course.id,
        examination_name='Expired Booking Exam',
        examination_type='Viva',
        duration=30,
        maximum_marks=50.0,
        slot_creation_start=now - timedelta(days=10),
        slot_creation_end=now - timedelta(days=5),
        slot_booking_start=now - timedelta(days=5),
        slot_booking_end=now - timedelta(days=1),  # Closed!
        status='Closed'
    )
    closed_exam.assigned_examiners = [examiner_approved]
    db.session.add(closed_exam)
    db.session.flush()

    slot = ExaminationSlot(
        examination_id=closed_exam.id,
        examiner_id=examiner_approved.id,
        examination_date=date.today() + timedelta(days=1),
        start_time=time(10, 0),
        end_time=time(10, 30),
        maximum_capacity=2,
        available_seats=2,
        status='Available'
    )
    student = User(full_name='Late Student', email='late@test.edu', role='student', status='active')
    student.set_password('Pass123')
    db.session.add_all([slot, student])
    db.session.commit()

    with pytest.raises(ValueError, match="window is currently closed"):
        BookingService.book_slot(student_id=student.id, slot_id=slot.id)

def test_slot_creation_deadline_enforcement(app, examiner_approved, sample_course):
    now = datetime.utcnow()
    # Exam where slot creation period has not started yet
    future_exam = Examination(
        course_id=sample_course.id,
        examination_name='Future Slot Exam',
        examination_type='Practical',
        duration=60,
        maximum_marks=100.0,
        slot_creation_start=now + timedelta(days=5),  # Not open yet!
        slot_creation_end=now + timedelta(days=10),
        slot_booking_start=now + timedelta(days=11),
        slot_booking_end=now + timedelta(days=20),
        status='Draft'
    )
    future_exam.assigned_examiners = [examiner_approved]
    db.session.add(future_exam)
    db.session.commit()

    with pytest.raises(ValueError, match="window closed or not open yet"):
        BookingService.create_slot(
            examiner=examiner_approved,
            exam_id=future_exam.id,
            exam_date=date.today() + timedelta(days=12),
            start_time=time(10, 0),
            end_time=time(11, 0),
            maximum_capacity=5
        )

def test_admin_rescheduling(app, admin_user, examiner_approved, sample_exam):
    slot_src = ExaminationSlot(
        examination_id=sample_exam.id,
        examiner_id=examiner_approved.id,
        examination_date=date.today() + timedelta(days=2),
        start_time=time(9, 0),
        end_time=time(9, 30),
        maximum_capacity=1,
        available_seats=0,
        status='Full'
    )
    slot_dst = ExaminationSlot(
        examination_id=sample_exam.id,
        examiner_id=examiner_approved.id,
        examination_date=date.today() + timedelta(days=3),
        start_time=time(15, 0),
        end_time=time(15, 30),
        maximum_capacity=2,
        available_seats=2,
        status='Available'
    )
    student = User(full_name='Reschedule Student', email='resched@test.edu', role='student', status='active')
    student.set_password('Pass123')
    db.session.add_all([slot_src, slot_dst, student])
    db.session.flush()

    booking = Booking(
        student_id=student.id,
        slot_id=slot_src.id,
        examination_id=sample_exam.id,
        status='Booked'
    )
    db.session.add(booking)
    db.session.commit()

    BookingService.reschedule_booking(
        booking_id=booking.id,
        target_slot_id=slot_dst.id,
        admin_user=admin_user
    )

    b = db.session.get(Booking, booking.id)
    assert b.slot_id == slot_dst.id

    src = db.session.get(ExaminationSlot, slot_src.id)
    assert src.available_seats == 1
    assert src.status == 'Available'

    dst = db.session.get(ExaminationSlot, slot_dst.id)
    assert dst.available_seats == 1
    assert dst.status == 'Available'

def test_cancellation_deadline_boundary_enforcement(app, examiner_approved, sample_course):
    now = datetime.utcnow()
    # Exam where booking window has closed
    exam = Examination(
        course_id=sample_course.id,
        examination_name='Deadline Past Exam',
        examination_type='Viva',
        duration=30,
        maximum_marks=50.0,
        slot_creation_start=now - timedelta(days=10),
        slot_creation_end=now - timedelta(days=5),
        slot_booking_start=now - timedelta(days=5),
        slot_booking_end=now - timedelta(minutes=5),  # Booking deadline has just passed!
        status='Closed'
    )
    exam.assigned_examiners = [examiner_approved]
    db.session.add(exam)
    db.session.flush()

    slot = ExaminationSlot(
        examination_id=exam.id,
        examiner_id=examiner_approved.id,
        examination_date=date.today() + timedelta(days=1),
        start_time=time(10, 0),
        end_time=time(10, 30),
        maximum_capacity=2,
        available_seats=1,
        status='Available'
    )
    student = User(full_name='Cancel Student', email='cancel_bound@test.edu', role='student', status='active')
    student.set_password('Pass123')
    db.session.add_all([slot, student])
    db.session.flush()

    booking = Booking(
        student_id=student.id,
        slot_id=slot.id,
        examination_id=exam.id,
        status='Booked'
    )
    db.session.add(booking)
    db.session.commit()

    # Attempting to cancel after/at booking deadline must be rejected
    with pytest.raises(ValueError, match="Cancellation deadline has passed"):
        BookingService.cancel_booking(booking_id=booking.id, user=student)

def test_atomic_capacity_exhaustion(app, student_user, examiner_approved, sample_exam):
    slot = ExaminationSlot(
        examination_id=sample_exam.id,
        examiner_id=examiner_approved.id,
        examination_date=date.today() + timedelta(days=2),
        start_time=time(9, 0),
        end_time=time(9, 30),
        maximum_capacity=1,
        available_seats=1,
        status='Available'
    )
    db.session.add(slot)
    db.session.commit()

    # First booking claims the only available seat
    b1 = BookingService.book_slot(student_id=student_user.id, slot_id=slot.id)
    assert b1 is not None

    # Slot must reflect Full and 0 available seats
    s = db.session.get(ExaminationSlot, slot.id)
    assert s.available_seats == 0
    assert s.status == 'Full'

    # Second student attempting to book must be rejected
    student2 = User(full_name='Second Student', email='second_student@test.edu', role='student', status='active')
    student2.set_password('Pass123')
    db.session.add(student2)
    db.session.commit()

    with pytest.raises(ValueError, match="full or unavailable"):
        BookingService.book_slot(student_id=student2.id, slot_id=slot.id)
