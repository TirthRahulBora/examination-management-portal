import os
from datetime import datetime
from flask import Flask, redirect, url_for, render_template
from flask_login import current_user
from app.extensions import db, login_manager
from config import config_by_name

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    config_obj = config_by_name.get(config_name, config_by_name['default'])
    app.config.from_object(config_obj)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.examiner import examiner_bp
    from app.routes.student import student_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(examiner_bp, url_prefix='/examiner')
    app.register_blueprint(student_bp, url_prefix='/student')

    # Root route
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.is_admin:
                return redirect(url_for('admin.dashboard'))
            elif current_user.is_examiner:
                if current_user.status == 'approved':
                    return redirect(url_for('examiner.dashboard'))
                else:
                    return redirect(url_for('auth.pending_approval'))
            elif current_user.is_student:
                return redirect(url_for('student.dashboard'))
        return redirect(url_for('auth.login'))

    # Custom Jinja filters
    @app.template_filter('format_dt')
    def format_dt(value, fmt='%d %b %Y, %I:%M %p'):
        if value is None:
            return '—'
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except Exception:
                return value
        return value.strftime(fmt)

    @app.template_filter('format_date')
    def format_date(value, fmt='%d %b %Y'):
        if value is None:
            return '—'
        return value.strftime(fmt)

    @app.template_filter('format_time')
    def format_time(value, fmt='%I:%M %p'):
        if value is None:
            return '—'
        return value.strftime(fmt)

    # Context processors
    @app.context_processor
    def inject_globals():
        return {
            'current_year': datetime.utcnow().year,
            'app_title': 'Examination Management Portal'
        }

    # Error handlers
    @app.errorhandler(400)
    def bad_request_error(error):
        return render_template('errors/400.html', error=error), 400

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html', error=error), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html', error=error), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html', error=error), 500

    return app
