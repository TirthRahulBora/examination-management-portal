from datetime import datetime, date, time, timedelta
from app.models import ExaminationSlot, Booking, Evaluation, User
from app.extensions import db

def test_slot_creation_and_conflict_detection(client, app, examiner_approved, sample_exam):
    client.post('/auth/login', data={'email': 'examiner@test.edu', 'password': 'ExaminerPass123'})

    target_date = (date.today() + timedelta(days=2)).strftime('%Y-%m-%d')
    # Create valid slot
    res = client.post(f'/examiner/examinations/{sample_exam.id}/slots/new', data={
        'examination_date': target_date,
        'start_time': '10:00',
        'end_time': '10:30',
        'maximum_capacity': 2
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Examination slot created successfully' in res.data

    # Attempting to create an overlapping slot for the same examiner on that date must fail
    conflict_res = client.post(f'/examiner/examinations/{sample_exam.id}/slots/new', data={
        'examination_date': target_date,
        'start_time': '10:15',
        'end_time': '10:45',
        'maximum_capacity': 1
    }, follow_redirects=True)
    assert b'Schedule conflict' in conflict_res.data

def test_rubric_evaluation_submission(client, app, examiner_approved, student_user, sample_exam):
    slot = ExaminationSlot(
        examination_id=sample_exam.id,
        examiner_id=examiner_approved.id,
        examination_date=date.today() + timedelta(days=2),
        start_time=time(14, 0),
        end_time=time(14, 30),
        maximum_capacity=2,
        available_seats=1,
        status='Available'
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
    rubric_ids = [r.id for r in sample_exam.rubrics]

    # Examiner logs in
    client.post('/auth/login', data={'email': 'examiner@test.edu', 'password': 'ExaminerPass123'})

    # Submitting negative score should fail
    fail_res = client.post(f'/examiner/bookings/{booking_id}/evaluate', data={
        f'rubric_{rubric_ids[0]}': -5,
        f'rubric_{rubric_ids[1]}': 40,
        'remarks': 'Negative test',
        'action': 'draft'
    }, follow_redirects=True)
    assert b'cannot be negative' in fail_res.data

    # Submitting score exceeding criterion max should fail
    exceed_res = client.post(f'/examiner/bookings/{booking_id}/evaluate', data={
        f'rubric_{rubric_ids[0]}': 60,  # Max is 50
        f'rubric_{rubric_ids[1]}': 40,
        'remarks': 'Exceed test',
        'action': 'draft'
    }, follow_redirects=True)
    assert b'exceeds criterion maximum' in exceed_res.data

    # Submitting valid scores and finalizing as Published
    valid_res = client.post(f'/examiner/bookings/{booking_id}/evaluate', data={
        f'rubric_{rubric_ids[0]}': 45.0,
        f'rubric_{rubric_ids[1]}': 42.5,
        'remarks': 'Great problem solving and complexity explanation.',
        'action': 'publish'
    }, follow_redirects=True)
    assert valid_res.status_code == 200

    b = db.session.get(Booking, booking_id)
    assert b.status == 'Completed'
    assert b.evaluation is not None
    assert b.evaluation.total_marks == 87.5
    assert b.evaluation.publication_status == 'Published'
    assert len(b.evaluation.details) == 2

def test_unauthorized_examiner_evaluation_guard(client, app, student_user, examiner_approved, sample_exam):
    # Create another examiner who does NOT own the slot
    other_ex = User(
        full_name='Dr. Unauthorized Examiner',
        email='unauthorized@test.edu',
        role='examiner',
        status='approved'
    )
    other_ex.set_password('Pass123')
    db.session.add(other_ex)
    db.session.commit()

    slot = ExaminationSlot(
        examination_id=sample_exam.id,
        examiner_id=examiner_approved.id,
        examination_date=date.today() + timedelta(days=2),
        start_time=time(16, 0),
        end_time=time(16, 30),
        maximum_capacity=2,
        available_seats=1,
        status='Available'
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

    # other_ex logs in and tries to grade booking in examiner_approved's slot
    client.post('/auth/login', data={'email': 'unauthorized@test.edu', 'password': 'Pass123'})
    res = client.get(f'/examiner/bookings/{booking_id}/evaluate')
    assert res.status_code in [403, 302]
