from datetime import datetime
from app.extensions import db

class ExaminationSlot(db.Model):
    __tablename__ = 'examination_slots'

    id = db.Column(db.Integer, primary_key=True)
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.id', ondelete='CASCADE'), nullable=False, index=True)
    examiner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True)
    examination_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    maximum_capacity = db.Column(db.Integer, nullable=False, default=1)
    available_seats = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(20), nullable=False, default='Available', index=True)
    # Statuses: 'Available', 'Full', 'Cancelled', 'Completed'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    examination = db.relationship('Examination', back_populates='slots')
    examiner = db.relationship('User', foreign_keys=[examiner_id], backref='conducted_slots')
    bookings = db.relationship('Booking', back_populates='slot', cascade='all, delete-orphan', lazy='dynamic')

    def recalculate_status(self):
        """Update available_seats and status based on active bookings."""
        if self.status == 'Cancelled' or self.status == 'Completed':
            return
        active_count = self.bookings.filter_by(status='Booked').count()
        self.available_seats = max(0, self.maximum_capacity - active_count)
        if self.available_seats <= 0:
            self.status = 'Full'
        else:
            self.status = 'Available'

    @property
    def booked_count(self):
        return self.bookings.filter_by(status='Booked').count()

    def __repr__(self):
        return f"<Slot {self.id}: Exam {self.examination_id} on {self.examination_date} {self.start_time}-{self.end_time} ({self.status})>"
