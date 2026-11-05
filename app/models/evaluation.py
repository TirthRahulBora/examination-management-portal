from datetime import datetime
from app.extensions import db

class Evaluation(db.Model):
    __tablename__ = 'evaluations'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    examiner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True)
    total_marks = db.Column(db.Float, nullable=False, default=0.0)
    remarks = db.Column(db.Text, nullable=True)
    evaluation_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    publication_status = db.Column(db.String(20), nullable=False, default='Draft', index=True)
    # Publication statuses: 'Draft', 'Published'

    # Relationships
    booking = db.relationship('Booking', back_populates='evaluation')
    examiner = db.relationship('User', foreign_keys=[examiner_id], backref='conducted_evaluations')
    details = db.relationship(
        'EvaluationDetail',
        back_populates='evaluation',
        cascade='all, delete-orphan',
        lazy='joined'
    )

    @property
    def is_published(self):
        return self.publication_status == 'Published'

    def __repr__(self):
        return f"<Evaluation {self.id}: Booking {self.booking_id} Marks={self.total_marks} ({self.publication_status})>"


class EvaluationDetail(db.Model):
    __tablename__ = 'evaluation_details'

    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluations.id', ondelete='CASCADE'), nullable=False, index=True)
    rubric_id = db.Column(db.Integer, db.ForeignKey('examination_rubrics.id', ondelete='CASCADE'), nullable=False, index=True)
    marks_awarded = db.Column(db.Float, nullable=False, default=0.0)
    remarks = db.Column(db.Text, nullable=True)

    # Relationships
    evaluation = db.relationship('Evaluation', back_populates='details')
    rubric = db.relationship('ExaminationRubric', back_populates='evaluation_details')

    def __repr__(self):
        return f"<EvaluationDetail {self.id}: Rubric {self.rubric_id} Marks={self.marks_awarded}>"

# EvaluationDetail itemized breakdown schema registered
