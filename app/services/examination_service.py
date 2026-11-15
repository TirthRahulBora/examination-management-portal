from datetime import datetime
from app.extensions import db
from app.models import Examination, Course, ExaminationRubric, ExaminationSlot, User

class ExaminationService:
    @staticmethod
    def create_examination(course_id, examination_name, examination_type, duration,
                           maximum_marks, slot_creation_start, slot_creation_end,
                           slot_booking_start, slot_booking_end, status='Draft'):
        """Create and validate a new examination."""
        if slot_creation_end <= slot_creation_start:
            raise ValueError("Slot creation end time must be after slot creation start time.")
        if slot_booking_end <= slot_booking_start:
            raise ValueError("Booking end time must be after booking start time.")
        if duration <= 0:
            raise ValueError("Duration must be a positive integer.")
        if maximum_marks <= 0:
            raise ValueError("Maximum marks must be greater than zero.")

        exam = Examination(
            course_id=course_id,
            examination_name=examination_name.strip(),
            examination_type=examination_type,
            duration=int(duration),
            maximum_marks=float(maximum_marks),
            slot_creation_start=slot_creation_start,
            slot_creation_end=slot_creation_end,
            slot_booking_start=slot_booking_start,
            slot_booking_end=slot_booking_end,
            status=status
        )
        db.session.add(exam)
        db.session.commit()
        return exam

    @staticmethod
    def update_examination(exam_id, **kwargs):
        exam = Examination.query.get_or_404(exam_id)
        for key, value in kwargs.items():
            if hasattr(exam, key) and value is not None:
                setattr(exam, key, value)
        
        # Validation checks on modified dates
        if exam.slot_creation_end <= exam.slot_creation_start:
            raise ValueError("Slot creation end time must be after start time.")
        if exam.slot_booking_end <= exam.slot_booking_start:
            raise ValueError("Booking end time must be after start time.")
        
        db.session.commit()
        return exam

    @staticmethod
    def assign_examiners(exam_id, examiner_ids):
        """Assign approved examiners to the examination."""
        exam = Examination.query.get_or_404(exam_id)
        examiners = User.query.filter(User.id.in_(examiner_ids), User.role == 'examiner', User.status == 'approved').all()
        exam.assigned_examiners = examiners
        db.session.commit()
        return exam

    @staticmethod
    def add_rubric(exam_id, criterion_name, maximum_marks, weightage=1.0, description=None):
        exam = Examination.query.get_or_404(exam_id)
        if maximum_marks <= 0:
            raise ValueError("Rubric criterion maximum marks must be positive.")
        
        # Check that total rubrics do not exceed exam maximum marks using fresh DB query
        from sqlalchemy import func
        current_total = db.session.query(func.coalesce(func.sum(ExaminationRubric.maximum_marks), 0.0)).filter(
            ExaminationRubric.examination_id == exam.id
        ).scalar()

        if (float(current_total) + float(maximum_marks)) > exam.maximum_marks:
            raise ValueError(f"Total rubric marks ({float(current_total) + float(maximum_marks)}) cannot exceed examination maximum marks ({exam.maximum_marks}).")

        rubric = ExaminationRubric(
            examination_id=exam.id,
            criterion_name=criterion_name.strip(),
            maximum_marks=float(maximum_marks),
            weightage=float(weightage),
            description=description.strip() if description else None
        )
        db.session.add(rubric)
        db.session.commit()
        return rubric


    @staticmethod
    def delete_rubric(rubric_id):
        rubric = ExaminationRubric.query.get_or_404(rubric_id)
        if rubric.evaluation_details.count() > 0:
            raise ValueError("Cannot delete criterion with existing student evaluations.")
        db.session.delete(rubric)
        db.session.commit()
        return True

    @staticmethod
    def update_status_automatically():
        """Update exam statuses based on timeline windows if currently in active workflow."""
        now = datetime.utcnow()
        exams = Examination.query.filter(Examination.status.in_(['Draft', 'Slot Creation', 'Booking Open'])).all()
        for exam in exams:
            if exam.status == 'Completed' or exam.status == 'Closed':
                continue
            if exam.slot_booking_start <= now <= exam.slot_booking_end:
                exam.status = 'Booking Open'
            elif exam.slot_creation_start <= now <= exam.slot_creation_end:
                exam.status = 'Slot Creation'
            elif now > exam.slot_booking_end:
                exam.status = 'Closed'
        db.session.commit()
