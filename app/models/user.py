from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)  # 'admin', 'examiner', 'student'
    department = db.Column(db.String(100), nullable=True)
    contact_number = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='active', index=True)
    # examiner statuses: 'pending', 'approved', 'rejected', 'deactivated'
    # student/admin statuses: 'active', 'deactivated'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    # Assigned examinations (many-to-many) via association table defined in examination.py
    assigned_examinations = db.relationship(
        'Examination',
        secondary='examination_examiners',
        back_populates='assigned_examiners'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        """Flask-Login integration: user can only authenticate if active/approved."""
        if self.role == 'admin':
            return self.status == 'active'
        elif self.role == 'examiner':
            return self.status == 'approved'
        elif self.role == 'student':
            return self.status == 'active'
        return False

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_examiner(self):
        return self.role == 'examiner'

    @property
    def is_student(self):
        return self.role == 'student'

    @property
    def is_approved_examiner(self):
        return self.role == 'examiner' and self.status == 'approved'

    def __repr__(self):
        return f"<User {self.id}: {self.email} ({self.role})>"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Verified Flask-Login integration and role helpers
