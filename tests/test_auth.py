import pytest
from app import create_app
from app.models import User
from app.extensions import db

def test_admin_login(client, admin_user):
    res = client.post('/auth/login', data={
        'email': 'admin@test.edu',
        'password': 'AdminPass123'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Administrator Dashboard' in res.data

def test_student_registration_and_login(client, app):
    res = client.post('/auth/register/student', data={
        'full_name': 'New Student',
        'email': 'newstudent@test.edu',
        'password': 'Password123',
        'confirm_password': 'Password123',
        'department': 'Data Science',
        'contact_number': '+91-99999-88888'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Registration successful' in res.data

    with app.app_context():
        u = User.query.filter_by(email='newstudent@test.edu').first()
        assert u is not None
        assert u.role == 'student'
        assert u.status == 'active'

    # Now login with the created account
    login_res = client.post('/auth/login', data={
        'email': 'newstudent@test.edu',
        'password': 'Password123'
    }, follow_redirects=True)
    assert login_res.status_code == 200
    assert b'Student Dashboard' in login_res.data

def test_examiner_registration_and_pending_approval(client, app):
    res = client.post('/auth/register/examiner', data={
        'full_name': 'Prof. Hopeful',
        'email': 'hopeful@test.edu',
        'password': 'Password123',
        'confirm_password': 'Password123',
        'department': 'Mechanical Engineering',
        'contact_number': '+91-99999-77777'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'pending' in res.data.lower()

    with app.app_context():
        u = User.query.filter_by(email='hopeful@test.edu').first()
        assert u is not None
        assert u.role == 'examiner'
        assert u.status == 'pending'

    # Attempting to login while pending must be redirected to pending-approval
    login_res = client.post('/auth/login', data={
        'email': 'hopeful@test.edu',
        'password': 'Password123'
    }, follow_redirects=True)
    assert login_res.status_code == 200
    assert b'Pending Approval' in login_res.data

def test_examiner_approval_workflow(client, app, admin_user, examiner_pending):
    # Admin logs in
    client.post('/auth/login', data={'email': 'admin@test.edu', 'password': 'AdminPass123'})
    
    # Admin approves pending examiner
    approve_res = client.post(f'/admin/examiners/{examiner_pending.id}/approve', follow_redirects=True)
    assert approve_res.status_code == 200

    with app.app_context():
        u = User.query.get(examiner_pending.id)
        assert u.status == 'approved'

    # Logout admin
    client.get('/auth/logout')

    # Examiner can now login and reach examiner dashboard
    login_res = client.post('/auth/login', data={
        'email': 'pending@test.edu',
        'password': 'PendingPass123'
    }, follow_redirects=True)
    assert login_res.status_code == 200
    assert b'Faculty Examiner Dashboard' in login_res.data

def test_role_based_access_restrictions(client, student_user, examiner_approved):
    # Student logs in
    client.post('/auth/login', data={'email': 'student@test.edu', 'password': 'StudentPass123'})

    # Student cannot access admin dashboard
    admin_res = client.get('/admin/dashboard')
    assert admin_res.status_code in [403, 302]

    # Student cannot access examiner dashboard
    examiner_res = client.get('/examiner/dashboard')
    assert examiner_res.status_code in [403, 302]

    client.get('/auth/logout')

    # Examiner logs in
    client.post('/auth/login', data={'email': 'examiner@test.edu', 'password': 'ExaminerPass123'})

    # Examiner cannot access admin dashboard
    admin_res2 = client.get('/admin/dashboard')
    assert admin_res2.status_code in [403, 302]

def test_csrf_token_validation(app):
    # Temporarily enable CSRF protection to verify rejection of untokenized POST requests
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['TESTING'] = False
    try:
        with app.test_client() as c:
            # POST without CSRF token must return 400 Bad Request
            res = c.post('/auth/login', data={'email': 'any@test.edu', 'password': 'Pass'})
            assert res.status_code == 400
            assert b'CSRF validation failed' in res.data
    finally:
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['TESTING'] = True

def test_production_secret_key_requirement(monkeypatch):
    monkeypatch.delenv('SECRET_KEY', raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY must be set when FLASK_ENV=production"):
        create_app('production')
