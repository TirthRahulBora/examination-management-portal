from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        elif current_user.is_examiner and current_user.status == 'approved':
            return redirect(url_for('examiner.dashboard'))
        elif current_user.is_student:
            return redirect(url_for('student.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please provide both email and password.', 'warning')
            return render_template('auth/login.html')

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Invalid email or password. Please verify credentials.', 'danger')
            return render_template('auth/login.html')

        # Check examiner approval status
        if user.is_examiner:
            if user.status == 'pending':
                flash('Your examiner registration is pending administrator approval.', 'info')
                return redirect(url_for('auth.pending_approval'))
            elif user.status == 'rejected':
                flash('Your examiner application was rejected by the administrator.', 'danger')
                return render_template('auth/login.html')
            elif user.status == 'deactivated':
                flash('Your examiner account is deactivated. Contact system administrator.', 'danger')
                return render_template('auth/login.html')

        # Check student deactivation
        if user.is_student and user.status == 'deactivated':
            flash('Your student account is currently deactivated. Contact administrator.', 'danger')
            return render_template('auth/login.html')

        # Check admin deactivation
        if user.is_admin and user.status != 'active':
            flash('Administrator account is inactive.', 'danger')
            return render_template('auth/login.html')

        login_user(user)
        flash(f'Welcome back, {user.full_name}!', 'success')

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)

        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        elif user.is_examiner:
            return redirect(url_for('examiner.dashboard'))
        elif user.is_student:
            return redirect(url_for('student.dashboard'))

    return render_template('auth/login.html')

@auth_bp.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        department = request.form.get('department', '').strip()
        contact_number = request.form.get('contact_number', '').strip()

        if not full_name or not email or not password:
            flash('Full Name, Email, and Password are required fields.', 'warning')
            return render_template('auth/register_student.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters in length.', 'warning')
            return render_template('auth/register_student.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register_student.html')

        if User.query.filter_by(email=email).first():
            flash('An account with this email address already exists.', 'warning')
            return render_template('auth/register_student.html')

        student = User(
            full_name=full_name,
            email=email,
            role='student',
            department=department or 'General',
            contact_number=contact_number or None,
            status='active'
        )
        student.set_password(password)
        db.session.add(student)
        db.session.commit()

        flash('Registration successful! You may now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_student.html')

@auth_bp.route('/register/examiner', methods=['GET', 'POST'])
def register_examiner():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        department = request.form.get('department', '').strip()
        contact_number = request.form.get('contact_number', '').strip()

        if not full_name or not email or not password:
            flash('Full Name, Email, and Password are required.', 'warning')
            return render_template('auth/register_examiner.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters in length.', 'warning')
            return render_template('auth/register_examiner.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register_examiner.html')

        if User.query.filter_by(email=email).first():
            flash('An account with this email address already exists.', 'warning')
            return render_template('auth/register_examiner.html')

        examiner = User(
            full_name=full_name,
            email=email,
            role='examiner',
            department=department or 'Academic Division',
            contact_number=contact_number or None,
            status='pending'  # pending admin approval
        )
        examiner.set_password(password)
        db.session.add(examiner)
        db.session.commit()

        flash('Registration request submitted! Your account is pending administrator approval before you can access the portal.', 'info')
        return redirect(url_for('auth.pending_approval'))

    return render_template('auth/register_examiner.html')

@auth_bp.route('/pending-approval')
def pending_approval():
    return render_template('auth/pending_approval.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

# Secure user logout and session teardown

# Student self-registration and department binding

# Examiner signup workflow with pending admin gate
