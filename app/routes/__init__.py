from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.examiner import examiner_bp
from app.routes.student import student_bp

__all__ = ['auth_bp', 'admin_bp', 'examiner_bp', 'student_bp']
