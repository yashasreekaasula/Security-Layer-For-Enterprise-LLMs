"""Create the first local development administrator. Set ADMIN_EMAIL and ADMIN_PASSWORD."""
import os, getpass
from .db import Base, engine, SessionLocal
from .models import Employee, PrivacyBudget
from .security import hash_password
Base.metadata.create_all(engine)
email=os.getenv('ADMIN_EMAIL') or input('Administrator email: ').strip().lower()
name=os.getenv('ADMIN_NAME') or input('Administrator full name: ').strip()
password=os.getenv('ADMIN_PASSWORD') or getpass.getpass('Administrator password (12+ characters): ')
if len(password)<12: raise SystemExit('Password must contain at least 12 characters.')
with SessionLocal() as db:
    existing=db.query(Employee).filter_by(email=email).first()
    if existing:
        if existing.registered: raise SystemExit('Account already activated; use account recovery instead.')
        existing.role='Administrator'; existing.password_hash=hash_password(password); existing.registered=True; existing.approved=True
        emp=existing
    else:
        emp=Employee(employee_id='ADMIN-LOCAL-001',full_name=name,email=email,department='Information Technology',title='System Administrator',role='Administrator',registered=True,approved=True,password_hash=hash_password(password)); db.add(emp); db.flush()
    if not db.query(PrivacyBudget).filter_by(employee_id=emp.id).first(): db.add(PrivacyBudget(employee_id=emp.id,remaining=10.0,initial=10.0))
    db.commit()
    from .main import sync_exports
    sync_exports(db)
print('Administrator account ready:',email)
