import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import datetime, date, time, timedelta
from app import create_app
from app.extensions import db
from app.models import User, Course, Examination, ExaminationRubric, ExaminationSlot, Booking

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture(autouse=True)
def app_context(app):
    with app.app_context():
        yield

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def admin_user(app):
    admin = User(
        full_name='Test Admin',
        email='admin@test.edu',
        role='admin',
        status='active'
    )
    admin.set_password('AdminPass123')
    db.session.add(admin)
    db.session.commit()
    return admin

@pytest.fixture
def examiner_approved(app):
    examiner = User(
        full_name='Dr. Test Examiner',
        email='examiner@test.edu',
        role='examiner',
        department='Computer Science',
        status='approved'
    )
    examiner.set_password('ExaminerPass123')
    db.session.add(examiner)
    db.session.commit()
    return examiner

@pytest.fixture
def examiner_pending(app):
    examiner = User(
        full_name='Pending Examiner',
        email='pending@test.edu',
        role='examiner',
        department='Data Science',
        status='pending'
    )
    examiner.set_password('PendingPass123')
    db.session.add(examiner)
    db.session.commit()
    return examiner

@pytest.fixture
def student_user(app):
    student = User(
        full_name='Test Student',
        email='student@test.edu',
        role='student',
        department='Computer Science',
        status='active'
    )
    student.set_password('StudentPass123')
    db.session.add(student)
    db.session.commit()
    return student

@pytest.fixture
def sample_course(app):
    course = Course(
        course_code='CS101',
        course_name='Data Structures & Algorithms',
        description='Core foundational course',
        status='Active'
    )
    db.session.add(course)
    db.session.commit()
    return course

@pytest.fixture
def sample_exam(app, sample_course, examiner_approved):
    now = datetime.utcnow()
    exam = Examination(
        course_id=sample_course.id,
        examination_name='CS101 Final Viva',
        examination_type='Viva',
        duration=30,
        maximum_marks=100.0,
        slot_creation_start=now - timedelta(days=2),
        slot_creation_end=now + timedelta(days=5),
        slot_booking_start=now - timedelta(days=1),
        slot_booking_end=now + timedelta(days=10),
        status='Booking Open'
    )
    exam.assigned_examiners = [examiner_approved]
    db.session.add(exam)
    db.session.flush()

    r1 = ExaminationRubric(
        examination_id=exam.id,
        criterion_name='Algorithmic Complexity',
        maximum_marks=50.0,
        weightage=1.0
    )
    r2 = ExaminationRubric(
        examination_id=exam.id,
        criterion_name='Implementation Details',
        maximum_marks=50.0,
        weightage=1.0
    )
    db.session.add_all([r1, r2])
    db.session.commit()
    return exam
