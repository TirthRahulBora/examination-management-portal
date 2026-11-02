from datetime import datetime
from app.extensions import db

class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    course_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Active')  # 'Active', 'Inactive'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    examinations = db.relationship(
        'Examination',
        back_populates='course',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    def __repr__(self):
        return f"<Course {self.course_code}: {self.course_name}>"
