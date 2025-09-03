#!/usr/bin/env python3
from datetime import datetime, timedelta
from app.database import SessionLocal, init_db
from app import models

def main():
    init_db()
    db = SessionLocal()
    try:
        # Ensure demo users
        def ensure_user(email, role):
            u = db.query(models.User).filter(models.User.email==email).first()
            if not u:
                u = models.User(email=email, password_hash='x', role=role)
                db.add(u); db.flush()
                if role==models.UserRole.host:
                    db.add(models.Host(user_id=u.id, name='Seed Host'))
                elif role==models.UserRole.cleaner:
                    db.add(models.Cleaner(user_id=u.id, name='Seed Cleaner'))
            return u
        host = ensure_user('demo_host@local', models.UserRole.host)
        cleaner = ensure_user('demo_cleaner@local', models.UserRole.cleaner)

        # Property
        prop = db.query(models.Property).filter(models.Property.host_id==host.id).first()
        if not prop:
            prop = models.Property(host_id=host.id, name='Downtown Flat', address='123 Main St')
            db.add(prop); db.flush()

        # Job + checklist
        s = datetime.utcnow() + timedelta(days=1)
        e = s + timedelta(hours=3)
        job = models.CleaningJob(property_id=prop.id, booking_start=s, booking_end=e, status=models.JobStatus.open)
        db.add(job); db.flush()
        for text in ['Change linens','Dust surfaces','Mop floors']:
            db.add(models.ChecklistItem(job_id=job.id, text=text))

        db.commit()
        print('Seeded demo data')
    finally:
        db.close()

if __name__=='__main__':
    main()
