from datetime import datetime
from app.extensions import db

# Association table for Examiner assignments to Examinations
examination_examiners = db.Table(
    'examination_examiners',
    db.Column('examination_id', db.Integer, db.ForeignKey('examinations.id', ondelete='CASCADE'), primary_key=True),
    db.Column('examiner_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    db.Column('assigned_at', db.DateTime, default=datetime.utcnow)
)

class Examination(db.Model):
    __tablename__ = 'examinations'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    examination_name = db.Column(db.String(150), nullable=False)
    examination_type = db.Column(db.String(50), nullable=False)  # 'Viva', 'Practical', 'Project Demo', 'Assessment'
    duration = db.Column(db.Integer, nullable=False)  # in minutes
    maximum_marks = db.Column(db.Float, nullable=False, default=100.0)
    slot_creation_start = db.Column(db.DateTime, nullable=False)
    slot_creation_end = db.Column(db.DateTime, nullable=False)
    slot_booking_start = db.Column(db.DateTime, nullable=False)
    slot_booking_end = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(30), nullable=False, default='Draft', index=True)
    # Statuses: 'Draft', 'Slot Creation', 'Booking Open', 'Closed', 'Completed'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    course = db.relationship('Course', back_populates='examinations')
    rubrics = db.relationship('ExaminationRubric', back_populates='examination', cascade='all, delete-orphan', lazy='joined')
    slots = db.relationship('ExaminationSlot', back_populates='examination', cascade='all, delete-orphan', lazy='dynamic')
    assigned_examiners = db.relationship(
        'User',
        secondary=examination_examiners,
        back_populates='assigned_examinations'
    )
    bookings = db.relationship('Booking', back_populates='examination', cascade='all, delete-orphan', lazy='dynamic')

    def is_in_slot_creation_period(self, target_dt=None):
        if target_dt is None:
            target_dt = datetime.utcnow()
        return self.slot_creation_start <= target_dt <= self.slot_creation_end

    def is_in_booking_period(self, target_dt=None):
        if target_dt is None:
            target_dt = datetime.utcnow()
        return self.slot_booking_start <= target_dt <= self.slot_booking_end

    @property
    def total_rubric_marks(self):
        return sum(r.maximum_marks for r in self.rubrics)

    def __repr__(self):
        return f"<Examination {self.id}: {self.examination_name} ({self.status})>"
