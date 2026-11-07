from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('Access denied: Administrator privileges required.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def examiner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_examiner:
            flash('Access denied: Examiner account required.', 'danger')
            abort(403)
        if current_user.status != 'approved':
            flash('Your examiner account is pending approval or inactive.', 'warning')
            return redirect(url_for('auth.pending_approval'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_student:
            flash('Access denied: Student account required.', 'danger')
            abort(403)
        if current_user.status != 'active':
            flash('Your student account is deactivated. Contact administrator.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# RBAC: admin_required decorator verified

# RBAC: examiner_required decorator verified

# RBAC: student_required decorator verified
