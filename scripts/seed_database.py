import os
import sys
from datetime import datetime, date, time, timedelta

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models import (
    User, Course, Examination, ExaminationRubric,
    ExaminationSlot, Booking, Evaluation, EvaluationDetail
)

app = create_app()

def seed():
    with app.app_context():
        print("[EMP SEED] Creating tables if not existing...")
        db.create_all()

        print("[EMP SEED] Seeding Users...")
        # 1. Admin
        admin = User.query.filter_by(email='admin@emp.edu').first()
        if not admin:
            admin = User(
                full_name='System Administrator',
                email='admin@emp.edu',
                role='admin',
                department='Examination Office',
                contact_number='+91-44-2257-8000',
                status='active'
            )
            admin.set_password('AdminPassword@123')
            db.session.add(admin)

        # 2. Examiners
        examiner1 = User.query.filter_by(email='examiner1@emp.edu').first()
        if not examiner1:
            examiner1 = User(
                full_name='Dr. Aris Thorne',
                email='examiner1@emp.edu',
                role='examiner',
                department='Computer Science & Engineering',
                contact_number='+91-98401-11223',
                status='approved'
            )
            examiner1.set_password('ExaminerPass@123')
            db.session.add(examiner1)

        examiner2 = User.query.filter_by(email='examiner2@emp.edu').first()
        if not examiner2:
            examiner2 = User(
                full_name='Prof. Maya Sen',
                email='examiner2@emp.edu',
                role='examiner',
                department='Data Science & AI',
                contact_number='+91-98402-22334',
                status='approved'
            )
            examiner2.set_password('ExaminerPass@123')
            db.session.add(examiner2)

        examiner_pending = User.query.filter_by(email='examiner.pending@emp.edu').first()
        if not examiner_pending:
            examiner_pending = User(
                full_name='Dr. Rajesh Kumar',
                email='examiner.pending@emp.edu',
                role='examiner',
                department='Information Technology',
                contact_number='+91-98403-33445',
                status='pending'
            )
            examiner_pending.set_password('ExaminerPass@123')
            db.session.add(examiner_pending)

        # 3. Students
        students_data = [
            ('Aarav Sharma', 'student1@emp.edu', 'Computer Science', '+91-91234-56781'),
            ('Diya Patel', 'student2@emp.edu', 'Data Science', '+91-91234-56782'),
            ('Rohan Verma', 'student3@emp.edu', 'Computer Science', '+91-91234-56783'),
            ('Ananya Iyer', 'student4@emp.edu', 'Artificial Intelligence', '+91-91234-56784'),
            ('Siddharth Nair', 'student5@emp.edu', 'Data Science', '+91-91234-56785'),
        ]
        students = []
        for name, email, dept, phone in students_data:
            s = User.query.filter_by(email=email).first()
            if not s:
                s = User(
                    full_name=name,
                    email=email,
                    role='student',
                    department=dept,
                    contact_number=phone,
                    status='active'
                )
                s.set_password('StudentPass@123')
                db.session.add(s)
            students.append(s)

        db.session.commit()

        # Refresh examiner and student references
        examiner1 = User.query.filter_by(email='examiner1@emp.edu').first()
        examiner2 = User.query.filter_by(email='examiner2@emp.edu').first()
        student1 = User.query.filter_by(email='student1@emp.edu').first()
        student2 = User.query.filter_by(email='student2@emp.edu').first()
        student3 = User.query.filter_by(email='student3@emp.edu').first()
        student4 = User.query.filter_by(email='student4@emp.edu').first()
        student5 = User.query.filter_by(email='student5@emp.edu').first()

        print("[EMP SEED] Seeding Courses...")
        courses_data = [
            ('CS101', 'Data Structures and Algorithms', 'Fundamental algorithmic problem solving, sorting, graph algorithms, and complexity analysis.', 'Active'),
            ('DS201', 'Tools in Data Science & Machine Learning', 'Exploratory data analysis, statistical modeling, machine learning workflows, and data pipelines.', 'Active'),
            ('AI301', 'Deep Learning & Neural Architectures', 'Deep neural networks, CNNs, Transformers, and LLM fine-tuning methodologies.', 'Active'),
            ('DB102', 'Database Systems & SQL Engineering', 'Relational database theory, normalization, ACID properties, indexing, and transactional integrity.', 'Active')
        ]
        courses = {}
        for code, name, desc, st in courses_data:
            c = Course.query.filter_by(course_code=code).first()
            if not c:
                c = Course(course_code=code, course_name=name, description=desc, status=st)
                db.session.add(c)
            courses[code] = c
        db.session.commit()

        # Refresh courses
        for code in courses_data:
            courses[code[0]] = Course.query.filter_by(course_code=code[0]).first()

        print("[EMP SEED] Seeding Examinations...")
        now = datetime.utcnow()
        # Exam 1: Active Booking Viva
        exam1 = Examination.query.filter_by(examination_name='CS101 Comprehensive Viva Voce').first()
        if not exam1:
            exam1 = Examination(
                course_id=courses['CS101'].id,
                examination_name='CS101 Comprehensive Viva Voce',
                examination_type='Viva',
                duration=30,
                maximum_marks=100.0,
                slot_creation_start=now - timedelta(days=10),
                slot_creation_end=now + timedelta(days=20),
                slot_booking_start=now - timedelta(days=5),
                slot_booking_end=now + timedelta(days=15),
                status='Booking Open'
            )
            exam1.assigned_examiners = [examiner1, examiner2]
            db.session.add(exam1)

        # Exam 2: Practical Exam
        exam2 = Examination.query.filter_by(examination_name='DS201 End-Term Practical Laboratory Exam').first()
        if not exam2:
            exam2 = Examination(
                course_id=courses['DS201'].id,
                examination_name='DS201 End-Term Practical Laboratory Exam',
                examination_type='Practical',
                duration=60,
                maximum_marks=100.0,
                slot_creation_start=now - timedelta(days=12),
                slot_creation_end=now + timedelta(days=18),
                slot_booking_start=now - timedelta(days=6),
                slot_booking_end=now + timedelta(days=12),
                status='Booking Open'
            )
            exam2.assigned_examiners = [examiner1, examiner2]
            db.session.add(exam2)

        # Exam 3: Capstone Project Demo
        exam3 = Examination.query.filter_by(examination_name='AI301 Capstone Project Demonstration').first()
        if not exam3:
            exam3 = Examination(
                course_id=courses['AI301'].id,
                examination_name='AI301 Capstone Project Demonstration',
                examination_type='Project Demo',
                duration=45,
                maximum_marks=100.0,
                slot_creation_start=now - timedelta(days=15),
                slot_creation_end=now + timedelta(days=10),
                slot_booking_start=now - timedelta(days=7),
                slot_booking_end=now + timedelta(days=7),
                status='Booking Open'
            )
            exam3.assigned_examiners = [examiner2]
            db.session.add(exam3)

        # Exam 4: Assessment
        exam4 = Examination.query.filter_by(examination_name='DB102 Schema Design Assessment').first()
        if not exam4:
            exam4 = Examination(
                course_id=courses['DB102'].id,
                examination_name='DB102 Schema Design Assessment',
                examination_type='Assessment',
                duration=40,
                maximum_marks=50.0,
                slot_creation_start=now + timedelta(days=2),
                slot_creation_end=now + timedelta(days=10),
                slot_booking_start=now + timedelta(days=11),
                slot_booking_end=now + timedelta(days=20),
                status='Draft'
            )
            exam4.assigned_examiners = [examiner1]
            db.session.add(exam4)

        db.session.commit()

        # Refresh examinations
        exam1 = Examination.query.filter_by(examination_name='CS101 Comprehensive Viva Voce').first()
        exam2 = Examination.query.filter_by(examination_name='DS201 End-Term Practical Laboratory Exam').first()
        exam3 = Examination.query.filter_by(examination_name='AI301 Capstone Project Demonstration').first()
        exam4 = Examination.query.filter_by(examination_name='DB102 Schema Design Assessment').first()

        print("[EMP SEED] Seeding Rubrics...")
        # Rubrics for Exam 1 (CS101)
        if not exam1.rubrics:
            r1 = ExaminationRubric(examination_id=exam1.id, criterion_name='Algorithm Theory & Analysis', maximum_marks=30.0, weightage=1.0, description='Demonstration of Big-O complexity and data structure fundamentals')
            r2 = ExaminationRubric(examination_id=exam1.id, criterion_name='Live Problem Solving', maximum_marks=40.0, weightage=1.0, description='Approach, pseudo-code clarity, and edge-case handling')
            r3 = ExaminationRubric(examination_id=exam1.id, criterion_name='Viva Defense & Oral Response', maximum_marks=30.0, weightage=1.0, description='Clarity of verbal articulation and technical defense')
            db.session.add_all([r1, r2, r3])

        # Rubrics for Exam 2 (DS201)
        if not exam2.rubrics:
            r4 = ExaminationRubric(examination_id=exam2.id, criterion_name='Data Ingestion & Cleaning', maximum_marks=25.0, weightage=1.0, description='Handling missing data, normalization, and outlier detection')
            r5 = ExaminationRubric(examination_id=exam2.id, criterion_name='Model Construction & Evaluation', maximum_marks=50.0, weightage=1.0, description='Appropriate choice of algorithm, cross-validation, and metrics')
            r6 = ExaminationRubric(examination_id=exam2.id, criterion_name='Visual Presentation of Insights', maximum_marks=25.0, weightage=1.0, description='Quality and accuracy of generated graphs and statistical conclusions')
            db.session.add_all([r4, r5, r6])

        # Rubrics for Exam 3 (AI301)
        if not exam3.rubrics:
            r7 = ExaminationRubric(examination_id=exam3.id, criterion_name='Architecture Design & Innovation', maximum_marks=40.0, weightage=1.0, description='Novelty and technical depth of neural architecture')
            r8 = ExaminationRubric(examination_id=exam3.id, criterion_name='Live Code Demonstration', maximum_marks=35.0, weightage=1.0, description='Functional execution, inference latency, and robustness')
            r9 = ExaminationRubric(examination_id=exam3.id, criterion_name='Technical Q&A', maximum_marks=25.0, weightage=1.0, description='Answering examiner questions on gradients, optimization, and scaling')
            db.session.add_all([r7, r8, r9])

        # Rubrics for Exam 4 (DB102)
        if not exam4.rubrics:
            r10 = ExaminationRubric(examination_id=exam4.id, criterion_name='Relational Normalization (BCNF/3NF)', maximum_marks=25.0, weightage=1.0, description='Elimination of insertion, update, and deletion anomalies')
            r11 = ExaminationRubric(examination_id=exam4.id, criterion_name='Complex SQL & Transactions', maximum_marks=25.0, weightage=1.0, description='Window functions, joins, and ACID compliance')
            db.session.add_all([r10, r11])

        db.session.commit()

        print("[EMP SEED] Seeding Examination Slots...")
        today = date.today()
        # Slots for Exam 1
        slot1 = ExaminationSlot.query.filter_by(examination_id=exam1.id, examination_date=today + timedelta(days=1), start_time=time(10, 0)).first()
        if not slot1:
            slot1 = ExaminationSlot(
                examination_id=exam1.id,
                examiner_id=examiner1.id,
                examination_date=today + timedelta(days=1),
                start_time=time(10, 0),
                end_time=time(10, 30),
                maximum_capacity=2,
                available_seats=2,
                status='Available'
            )
            db.session.add(slot1)

        slot2 = ExaminationSlot.query.filter_by(examination_id=exam1.id, examination_date=today + timedelta(days=1), start_time=time(11, 0)).first()
        if not slot2:
            slot2 = ExaminationSlot(
                examination_id=exam1.id,
                examiner_id=examiner1.id,
                examination_date=today + timedelta(days=1),
                start_time=time(11, 0),
                end_time=time(11, 30),
                maximum_capacity=1,
                available_seats=1,
                status='Available'
            )
            db.session.add(slot2)

        slot3 = ExaminationSlot.query.filter_by(examination_id=exam1.id, examination_date=today + timedelta(days=2), start_time=time(14, 0)).first()
        if not slot3:
            slot3 = ExaminationSlot(
                examination_id=exam1.id,
                examiner_id=examiner2.id,
                examination_date=today + timedelta(days=2),
                start_time=time(14, 0),
                end_time=time(14, 30),
                maximum_capacity=2,
                available_seats=2,
                status='Available'
            )
            db.session.add(slot3)

        # Slot for Exam 2
        slot4 = ExaminationSlot.query.filter_by(examination_id=exam2.id, examination_date=today + timedelta(days=3), start_time=time(9, 30)).first()
        if not slot4:
            slot4 = ExaminationSlot(
                examination_id=exam2.id,
                examiner_id=examiner2.id,
                examination_date=today + timedelta(days=3),
                start_time=time(9, 30),
                end_time=time(10, 30),
                maximum_capacity=3,
                available_seats=3,
                status='Available'
            )
            db.session.add(slot4)

        # Slot in the past for completed evaluation demo
        past_slot = ExaminationSlot.query.filter_by(examination_id=exam1.id, examination_date=today - timedelta(days=2), start_time=time(15, 0)).first()
        if not past_slot:
            past_slot = ExaminationSlot(
                examination_id=exam1.id,
                examiner_id=examiner1.id,
                examination_date=today - timedelta(days=2),
                start_time=time(15, 0),
                end_time=time(15, 30),
                maximum_capacity=2,
                available_seats=1,
                status='Available'
            )
            db.session.add(past_slot)

        db.session.commit()

        # Refresh slots
        slot1 = ExaminationSlot.query.filter_by(examination_id=exam1.id, examination_date=today + timedelta(days=1), start_time=time(10, 0)).first()
        slot2 = ExaminationSlot.query.filter_by(examination_id=exam1.id, examination_date=today + timedelta(days=1), start_time=time(11, 0)).first()
        past_slot = ExaminationSlot.query.filter_by(examination_id=exam1.id, examination_date=today - timedelta(days=2), start_time=time(15, 0)).first()

        print("[EMP SEED] Seeding Bookings and Evaluations...")
        # Booking 1: Student 1 booked into Slot 1
        b1 = Booking.query.filter_by(student_id=student1.id, examination_id=exam1.id).first()
        if not b1:
            b1 = Booking(student_id=student1.id, slot_id=slot1.id, examination_id=exam1.id, status='Booked')
            slot1.available_seats -= 1
            if slot1.available_seats <= 0:
                slot1.status = 'Full'
            db.session.add(b1)

        # Booking 2: Student 2 booked into Past Slot and evaluated with published result!
        b2 = Booking.query.filter_by(student_id=student2.id, examination_id=exam1.id).first()
        if not b2:
            b2 = Booking(student_id=student2.id, slot_id=past_slot.id, examination_id=exam1.id, status='Completed')
            past_slot.available_seats -= 1
            db.session.add(b2)
            db.session.flush()

            # Create Evaluation with rubric details
            eval2 = Evaluation(
                booking_id=b2.id,
                examiner_id=examiner1.id,
                total_marks=88.0,
                remarks='Exceptional mastery of algorithm complexity and balanced tree rotations. Confident verbal defense.',
                evaluation_date=datetime.utcnow() - timedelta(days=1),
                publication_status='Published'
            )
            db.session.add(eval2)
            db.session.flush()

            r_list = exam1.rubrics
            d1 = EvaluationDetail(evaluation_id=eval2.id, rubric_id=r_list[0].id, marks_awarded=27.0, remarks='Strong theory')
            d2 = EvaluationDetail(evaluation_id=eval2.id, rubric_id=r_list[1].id, marks_awarded=35.0, remarks='Optimal code')
            d3 = EvaluationDetail(evaluation_id=eval2.id, rubric_id=r_list[2].id, marks_awarded=26.0, remarks='Articulate responses')
            db.session.add_all([d1, d2, d3])

        # Booking 3: Student 3 booked into Slot 2 (which becomes Full)
        b3 = Booking.query.filter_by(student_id=student3.id, examination_id=exam1.id).first()
        if not b3:
            b3 = Booking(student_id=student3.id, slot_id=slot2.id, examination_id=exam1.id, status='Booked')
            slot2.available_seats -= 1
            if slot2.available_seats <= 0:
                slot2.status = 'Full'
            db.session.add(b3)

        # Booking 4: Cancelled booking record for Student 4 (to demo historical preservation)
        b4 = Booking.query.filter_by(student_id=student4.id, examination_id=exam1.id).first()
        if not b4:
            b4 = Booking(student_id=student4.id, slot_id=slot1.id, examination_id=exam1.id, status='Cancelled')
            db.session.add(b4)

        db.session.commit()
        print("[EMP SEED] Database seeding completed successfully!")

if __name__ == '__main__':
    seed()
