from datetime import datetime
from app.extensions import db

class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    slot_id = db.Column(db.Integer, db.ForeignKey('examination_slots.id', ondelete='CASCADE'), nullable=False, index=True)
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.id', ondelete='CASCADE'), nullable=False, index=True)
    booking_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='Booked', index=True)
    # Statuses: 'Booked', 'Cancelled', 'Completed'

    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], backref='bookings')
    slot = db.relationship('ExaminationSlot', back_populates='bookings')
    examination = db.relationship('Examination', back_populates='bookings')
    evaluation = db.relationship('Evaluation', uselist=False, back_populates='booking', cascade='all, delete-orphan')

    # Partial unique index to enforce single active booking per examination per student in SQLite
    __table_args__ = (
        db.Index(
            'uq_active_student_exam_booking',
            'student_id',
            'examination_id',
            unique=True,
            sqlite_where=(status == 'Booked')
        ),
    )

    def __repr__(self):
        return f"<Booking {self.id}: Student {self.student_id} -> Slot {self.slot_id} ({self.status})>"

# Enforced uniqueness per student per examination lifecycle
