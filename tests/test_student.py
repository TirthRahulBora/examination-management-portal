from datetime import datetime, date, time, timedelta
from app.models import ExaminationSlot, Booking, Evaluation, User
from app.extensions import db

def test_student_browse_and_book_slot(client, app, student_user, examiner_approved, sample_exam):
    slot = ExaminationSlot(
        examination_id=sample_exam.id,
        examiner_id=examiner_approved.id,
        examination_date=date.today() + timedelta(days=2),
        start_time=time(11, 0),
        end_time=time(11, 30),
        maximum_capacity=2,
        available_seats=2,
        status='Available'
    )
    db.session.add(slot)
    db.session.commit()
    slot_id = slot.id

    client.post('/auth/login', data={'email': 'student@test.edu', 'password': 'StudentPass123'})

    # Browse examinations
    browse_res = client.get('/student/examinations')
    assert browse_res.status_code == 200
    assert b'CS101 Final Viva' in browse_res.data

    # Book slot
    book_res = client.post(f'/student/slots/{slot_id}/book', follow_redirects=True)
    assert book_res.status_code == 200
    assert b'Slot successfully booked' in book_res.data

    s = db.session.get(ExaminationSlot, slot_id)
    assert s.available_seats == 1
    b = Booking.query.filter_by(student_id=student_user.id, slot_id=slot_id).first()
    assert b is not None
    assert b.status == 'Booked'

def test_student_booking_cancellation(client, app, student_user, examiner_approved, sample_exam):
    slot = ExaminationSlot(
        examination_id=sample_exam.id,
        examiner_id=examiner_approved.id,
        examination_date=date.today() + timedelta(days=2),
        start_time=time(15, 0),
        end_time=time(15, 30),
        maximum_capacity=1,
        available_seats=0,
        status='Full'
    )
    db.session.add(slot)
    db.session.flush()

    booking = Booking(
        student_id=student_user.id,
        slot_id=slot.id,
        examination_id=sample_exam.id,
        status='Booked'
    )
    db.session.add(booking)
    db.session.commit()
    booking_id = booking.id
    slot_id = slot.id

    client.post('/auth/login', data={'email': 'student@test.edu', 'password': 'StudentPass123'})

    # Cancel booking
    cancel_res = client.post(f'/student/bookings/{booking_id}/cancel', follow_redirects=True)
    assert cancel_res.status_code == 200
    assert b'cancelled successfully' in cancel_res.data

    b = db.session.get(Booking, booking_id)
    assert b.status == 'Cancelled'
    s = db.session.get(ExaminationSlot, slot_id)
    # Seat must be restored and slot status restored to Available
    assert s.available_seats == 1
    assert s.status == 'Available'

def test_result_publication_visibility(client, app, student_user, examiner_approved, sample_exam):
    slot = ExaminationSlot(
        examination_id=sample_exam.id,
        examiner_id=examiner_approved.id,
        examination_date=date.today() - timedelta(days=1),
        start_time=time(10, 0),
        end_time=time(10, 30),
        maximum_capacity=1,
        available_seats=0,
        status='Completed'
    )
    db.session.add(slot)
    db.session.flush()

    booking = Booking(
        student_id=student_user.id,
        slot_id=slot.id,
        examination_id=sample_exam.id,
        status='Completed'
    )
    db.session.add(booking)
    db.session.flush()

    # Draft evaluation (not yet published)
    evaluation = Evaluation(
        booking_id=booking.id,
        examiner_id=examiner_approved.id,
        total_marks=92.0,
        remarks='Draft feedback',
        publication_status='Draft'
    )
    db.session.add(evaluation)
    db.session.commit()
    eval_id = evaluation.id

    client.post('/auth/login', data={'email': 'student@test.edu', 'password': 'StudentPass123'})

    # Student cannot view draft evaluation scorecard
    res = client.get(f'/student/results/{eval_id}', follow_redirects=True)
    assert b'not yet published' in res.data

    # Now publish the evaluation
    ev = db.session.get(Evaluation, eval_id)
    ev.publication_status = 'Published'
    db.session.commit()

    # Student can now view published scorecard
    pub_res = client.get(f'/student/results/{eval_id}')
    assert pub_res.status_code == 200
    assert b'Official Examination Scorecard' in pub_res.data
    assert b'92' in pub_res.data

def test_student_idor_scorecard_forbidden(client, app, student_user, examiner_approved, sample_exam):
    student2 = User(
        full_name='Other Student',
        email='other_student@test.edu',
        role='student',
        status='active'
    )
    student2.set_password('Pass1234')
    db.session.add(student2)
    db.session.flush()

    slot = ExaminationSlot(
        examination_id=sample_exam.id,
        examiner_id=examiner_approved.id,
        examination_date=date.today() - timedelta(days=1),
        start_time=time(10, 0),
        end_time=time(10, 30),
        maximum_capacity=1,
        available_seats=0,
        status='Completed'
    )
    db.session.add(slot)
    db.session.flush()

    booking2 = Booking(
        student_id=student2.id,
        slot_id=slot.id,
        examination_id=sample_exam.id,
        status='Completed'
    )
    db.session.add(booking2)
    db.session.flush()

    eval2 = Evaluation(
        booking_id=booking2.id,
        examiner_id=examiner_approved.id,
        total_marks=88.0,
        remarks='Published for student 2',
        publication_status='Published'
    )
    db.session.add(eval2)
    db.session.commit()

    # Log in as student1 and attempt to access student2's evaluation card
    client.post('/auth/login', data={'email': 'student@test.edu', 'password': 'StudentPass123'})
    idor_res = client.get(f'/student/results/{eval2.id}')
    assert idor_res.status_code == 403

def test_student_idor_cancel_booking_forbidden(client, app, student_user, examiner_approved, sample_exam):
    student2 = User(
        full_name='Another Student',
        email='another@test.edu',
        role='student',
        status='active'
    )
    student2.set_password('Pass1234')
    db.session.add(student2)
    db.session.flush()

    slot = ExaminationSlot(
        examination_id=sample_exam.id,
        examiner_id=examiner_approved.id,
        examination_date=date.today() + timedelta(days=2),
        start_time=time(14, 0),
        end_time=time(14, 30),
        maximum_capacity=1,
        available_seats=0,
        status='Full'
    )
    db.session.add(slot)
    db.session.flush()

    booking2 = Booking(
        student_id=student2.id,
        slot_id=slot.id,
        examination_id=sample_exam.id,
        status='Booked'
    )
    db.session.add(booking2)
    db.session.commit()

    # Log in as student1 and attempt to cancel student2's booking
    client.post('/auth/login', data={'email': 'student@test.edu', 'password': 'StudentPass123'})
    cancel_res = client.post(f'/student/bookings/{booking2.id}/cancel', follow_redirects=True)
    assert b'Unauthorized cancellation attempt' in cancel_res.data
    # Verify booking2 is still Booked
    b2 = db.session.get(Booking, booking2.id)
    assert b2.status == 'Booked'
