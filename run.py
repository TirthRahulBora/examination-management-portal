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
        admin = User(
            full_name='System Administrator',
            email='admin@emp.edu',
            role='admin',
            department='Examination Office',
            contact_number='+91-44-2257-8000',
            status='active'
        )
        admin.set_password('AdminPassword@123')
        db.session.add(admin)
        db.session.commit()
        print("[EMP] Initialized default administrator: admin@emp.edu / AdminPassword@123")

if __name__ == '__main__':
    with app.app_context():
        # Ensure database tables exist
        db.create_all()
        ensure_admin()

    print("==================================================")
    print("  Examination Management Portal (EMP) Starting  ")
    print("  Local URL: http://127.0.0.1:5000               ")
    print("==================================================")
    app.run(host='127.0.0.1', port=5000, debug=True)

# Seed CLI command integration complete
