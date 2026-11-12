from datetime import datetime, date, time, timedelta
from app.models import Course, Examination, ExaminationRubric, ExaminationSlot, Booking, User
from app.extensions import db

def test_course_crud(client, app, admin_user):
    client.post('/auth/login', data={'email': 'admin@test.edu', 'password': 'AdminPass123'})

    # Create course
    res = client.post('/admin/courses/new', data={
        'course_code': 'AI401',
        'course_name': 'Reinforcement Learning',
        'description': 'MDPs, Q-Learning, and Policy Gradients',
        'status': 'Active'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'AI401' in res.data

    with app.app_context():
        c = Course.query.filter_by(course_code='AI401').first()
        assert c is not None
        assert c.course_name == 'Reinforcement Learning'

    # Edit course
    edit_res = client.post(f'/admin/courses/{c.id}/edit', data={
        'course_code': 'AI401',
        'course_name': 'Advanced Reinforcement Learning',
        'description': 'Updated description',
        'status': 'Active'
    }, follow_redirects=True)
    assert edit_res.status_code == 200
    assert b'Advanced Reinforcement Learning' in edit_res.data

def test_examination_management(client, app, admin_user, sample_course):
    client.post('/auth/login', data={'email': 'admin@test.edu', 'password': 'AdminPass123'})

    now = datetime.utcnow()
    res = client.post('/admin/examinations/new', data={
        'examination_name': 'Mid-Term Lab Practical',
        'course_id': sample_course.id,
        'examination_type': 'Practical',
        'duration': 45,
        'maximum_marks': 50,
        'slot_creation_start': (now - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
        'slot_creation_end': (now + timedelta(days=5)).strftime('%Y-%m-%dT%H:%M'),
        'slot_booking_start': (now - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
        'slot_booking_end': (now + timedelta(days=4)).strftime('%Y-%m-%dT%H:%M'),
        'status': 'Booking Open'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Mid-Term Lab Practical' in res.data

    with app.app_context():
        e = Examination.query.filter_by(examination_name='Mid-Term Lab Practical').first()
        assert e is not None
        assert e.examination_type == 'Practical'
        assert e.duration == 45

def test_rubric_management(client, app, admin_user, sample_exam):
    client.post('/auth/login', data={'email': 'admin@test.edu', 'password': 'AdminPass123'})

    # Current sample_exam has 100 max marks and two 50 mark rubrics (total 100).
    # Trying to add another 10 mark rubric should fail validation
    fail_res = client.post(f'/admin/examinations/{sample_exam.id}/rubrics/new', data={
        'criterion_name': 'Bonus Criterion',
        'maximum_marks': 10,
        'weightage': 1.0,
        'description': 'Should exceed max marks'
    }, follow_redirects=True)
    assert b'exceed examination maximum marks' in fail_res.data

    # Now edit existing rubric down to 40 so there's headroom
    r1 = ExaminationRubric.query.filter_by(examination_id=sample_exam.id).first()
    r1.maximum_marks = 40.0
    db.session.commit()


    # Now add valid criterion with 10 marks
    res = client.post(f'/admin/examinations/{sample_exam.id}/rubrics/new', data={
        'criterion_name': 'Documentation & Style',
        'maximum_marks': 10,
        'weightage': 1.0,
        'description': 'Clean code and documentation'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Documentation' in res.data





def test_examiner_deactivation_and_reassignment(client, app, admin_user, examiner_approved, sample_exam):
    client.post('/auth/login', data={'email': 'admin@test.edu', 'password': 'AdminPass123'})

    # Create slot for examiner_approved
    slot = ExaminationSlot(
        examination_id=sample_exam.id,
        examiner_id=examiner_approved.id,
        examination_date=date.today() + timedelta(days=2),
        start_time=time(10, 0),
        end_time=time(10, 30),
        maximum_capacity=2,
        available_seats=2,
        status='Available'
    )
    ex2 = User(
        full_name='Dr. Second Examiner',
        email='second@test.edu',
        role='examiner',
        status='approved'
    )
    ex2.set_password('Pass123')
    db.session.add_all([slot, ex2])
    db.session.commit()
    slot_id = slot.id
    ex2_id = ex2.id

    # Reassign slot examiner
    res = client.post(f'/admin/slots/{slot_id}/reassign', data={
        'new_examiner_id': ex2_id
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Examiner reassigned successfully' in res.data

    s = ExaminationSlot.query.get(slot_id)
    assert s.examiner_id == ex2_id

