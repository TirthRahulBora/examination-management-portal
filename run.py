import os
from pathlib import Path
from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

def ensure_admin():
    """Ensure an administrator exists on startup."""
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin_email = os.environ.get('EMP_ADMIN_EMAIL', 'admin@emp.edu')
        admin_password = os.environ.get('EMP_ADMIN_PASSWORD')
        
        is_production = os.environ.get('FLASK_ENV') == 'production'
        if is_production and not admin_password:
            raise RuntimeError("EMP_ADMIN_PASSWORD must be configured in environment when running in production.")
        
        if not admin_password:
            admin_password = 'AdminPassword@123'
            print("[EMP NOTICE] Initialized administrator using default development credentials.")
            print("[EMP NOTICE] Set EMP_ADMIN_PASSWORD in environment or .env for customized security.")
        
        admin = User(
            full_name='System Administrator',
            email=admin_email,
            role='admin',
            department='Examination Office',
            contact_number='+91-44-2257-8000',
            status='active'
        )
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print(f"[EMP] Administrator account ready: {admin_email}")

if __name__ == '__main__':
    with app.app_context():
        # Ensure database tables exist
        db.create_all()
        ensure_admin()

    debug_mode = os.environ.get('FLASK_DEBUG', '0').lower() in {'1', 'true', 'yes'}
    print("==================================================")
    print("  Examination Management Portal (EMP) Starting  ")
    print("  Local URL: http://127.0.0.1:5000               ")
    print(f"  Debug Mode: {'Enabled' if debug_mode else 'Disabled (Production Safe)'}")
    print("==================================================")
    app.run(host='127.0.0.1', port=5000, debug=debug_mode)
