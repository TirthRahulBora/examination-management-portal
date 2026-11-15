from datetime import datetime
from app.extensions import db
from app.models import Evaluation, EvaluationDetail, Booking, ExaminationRubric

class EvaluationService:
    @staticmethod
    def submit_evaluation(examiner, booking_id, rubric_scores, remarks=None, publication_status='Draft'):
        """
        Record or update an evaluation with rubric breakdown and strict authorization checks.
        rubric_scores: dict mapping rubric_id (int) -> marks_awarded (float)
        """
        booking = Booking.query.get_or_404(booking_id)

        # 1. Examiner authorization: only assigned slot examiner (or admin) can evaluate
        if not examiner.is_admin and booking.slot.examiner_id != examiner.id:
            raise PermissionError("Examiner is not authorized to evaluate students booked in another examiner's slot.")

        # 2. Booking status check: cannot evaluate cancelled bookings
        if booking.status not in ['Booked', 'Completed']:
            raise ValueError(f"Cannot submit evaluation for a booking with status '{booking.status}'.")

        exam = booking.examination
        evaluation = booking.evaluation

        # 3. Guard against arbitrary modification of already published results by non-admins
        if evaluation and evaluation.is_published and not examiner.is_admin:
            raise PermissionError("Published evaluation results cannot be modified without administrative clearance.")

        # 4. Validate rubrics and scores
        valid_rubrics = {r.id: r for r in exam.rubrics}
        if not valid_rubrics:
            raise ValueError("No rubrics configured for this examination. Evaluation cannot proceed.")

        total_marks = 0.0
        validated_details = []

        for rubric_id, mark_val in rubric_scores.items():
            rubric_id = int(rubric_id)
            if rubric_id not in valid_rubrics:
                raise ValueError(f"Rubric ID {rubric_id} does not belong to examination {exam.examination_name}.")
            
            rubric = valid_rubrics[rubric_id]
            try:
                score = float(mark_val)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid mark provided for criterion '{rubric.criterion_name}'.")

            if score < 0:
                raise ValueError(f"Score for '{rubric.criterion_name}' cannot be negative.")
            if score > rubric.maximum_marks:
                raise ValueError(f"Score for '{rubric.criterion_name}' ({score}) exceeds criterion maximum ({rubric.maximum_marks}).")

            total_marks += score
            validated_details.append((rubric, score))

        if total_marks > exam.maximum_marks:
            raise ValueError(f"Calculated total marks ({total_marks}) exceeds examination ceiling ({exam.maximum_marks}).")

        # Create or update evaluation record
        if not evaluation:
            evaluation = Evaluation(
                booking_id=booking.id,
                examiner_id=examiner.id,
                total_marks=total_marks,
                remarks=remarks.strip() if remarks else None,
                publication_status=publication_status,
                evaluation_date=datetime.utcnow()
            )
            db.session.add(evaluation)
            db.session.flush()
        else:
            evaluation.total_marks = total_marks
            evaluation.remarks = remarks.strip() if remarks else None
            evaluation.publication_status = publication_status
            evaluation.evaluation_date = datetime.utcnow()
            # Clear existing details
            for d in list(evaluation.details):
                db.session.delete(d)
            db.session.flush()

        # Add detail rows
        for rubric, score in validated_details:
            detail = EvaluationDetail(
                evaluation_id=evaluation.id,
                rubric_id=rubric.id,
                marks_awarded=score,
                remarks=""
            )
            db.session.add(detail)

        # Mark booking as completed
        booking.status = 'Completed'

        db.session.commit()
        return evaluation

    @staticmethod
    def publish_evaluation(evaluation_id, user):
        """Publish an evaluation so the student can view their marks and remarks."""
        evaluation = Evaluation.query.get_or_404(evaluation_id)
        if not user.is_admin and evaluation.examiner_id != user.id:
            raise PermissionError("Unauthorized to publish this evaluation.")
        evaluation.publication_status = 'Published'
        db.session.commit()
        return evaluation

    @staticmethod
    def unpublish_evaluation(evaluation_id, user):
        """Unpublish an evaluation."""
        if not user.is_admin:
            raise PermissionError("Only administrators can unpublish released marks.")
        evaluation = Evaluation.query.get_or_404(evaluation_id)
        evaluation.publication_status = 'Draft'
        db.session.commit()
        return evaluation
