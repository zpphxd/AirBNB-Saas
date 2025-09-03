from __future__ import annotations
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from ..schemas import JobCreate, JobOut, ClaimJobRequest, TickChecklistRequest, RatingCreate, ChecklistItemOut
from .auth import get_current_user
from ..services.scheduler import SCHEDULER, remind_job_upcoming


router = APIRouter()


def _ensure_media_dir() -> str:
    root = os.path.dirname(os.path.dirname(__file__))
    media_dir = os.path.join(root, "media")
    os.makedirs(media_dir, exist_ok=True)
    return media_dir


@router.post("/", response_model=JobOut)
def create_job(payload: JobCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if user.role != models.UserRole.host:
        raise HTTPException(status_code=403, detail="Only hosts can create jobs")
    host = db.query(models.Host).filter(models.Host.user_id == user.id).first()
    prop = db.query(models.Property).filter(models.Property.id == payload.property_id).first()
    if not host or not prop or prop.host_id != host.id:
        raise HTTPException(status_code=400, detail="Invalid property")
    job = models.CleaningJob(
        property_id=prop.id,
        booking_start=payload.booking_start,
        booking_end=payload.booking_end,
        status=models.JobStatus.open,
    )
    db.add(job)
    db.flush()

    for item in payload.checklist:
        db.add(models.ChecklistItem(job_id=job.id, text=item.text))

    db.commit()
    db.refresh(job)

    # Schedule reminder 1 hour before booking_end (stub)
    try:
        delta = job.booking_end - datetime.utcnow() - timedelta(hours=1)
        if delta.total_seconds() > 0:
            SCHEDULER.schedule(delta, lambda j_id=job.id: remind_job_upcoming(j_id))
    except Exception:
        pass

    job.checklist_items  # load
    return job


@router.get("/open", response_model=list[JobOut])
def list_open_jobs(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    q = db.query(models.CleaningJob).filter(models.CleaningJob.status == models.JobStatus.open)
    jobs = q.order_by(models.CleaningJob.booking_start.asc()).all()
    return jobs


@router.post("/{job_id}/claim", response_model=JobOut)
def claim_job(job_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if user.role != models.UserRole.cleaner:
        raise HTTPException(status_code=403, detail="Only cleaners can claim jobs")
    cleaner = db.query(models.Cleaner).filter(models.Cleaner.user_id == user.id).first()
    job = db.query(models.CleaningJob).filter(models.CleaningJob.id == job_id).first()
    if not job or job.status != models.JobStatus.open:
        raise HTTPException(status_code=400, detail="Job not open or not found")
    job.status = models.JobStatus.claimed
    job.cleaner_id = cleaner.id
    db.commit()
    db.refresh(job)
    return job


@router.post("/{job_id}/checklist/tick", response_model=list[ChecklistItemOut])
def tick_checklist(job_id: int, payload: TickChecklistRequest, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    job = db.query(models.CleaningJob).filter(models.CleaningJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # Only assigned cleaner or admin can tick
    if user.role not in (models.UserRole.admin,) and not (user.role == models.UserRole.cleaner and job.cleaner and job.cleaner.user_id == user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    items = db.query(models.ChecklistItem).filter(models.ChecklistItem.job_id == job_id, models.ChecklistItem.id.in_(payload.item_ids)).all()
    now = datetime.utcnow()
    for it in items:
        it.checked = True
        it.checked_at = now
    db.commit()
    out = db.query(models.ChecklistItem).filter(models.ChecklistItem.job_id == job_id).all()
    return out


@router.post("/{job_id}/checklist/{item_id}/photo", response_model=ChecklistItemOut)
async def upload_photo(job_id: int, item_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    job = db.query(models.CleaningJob).filter(models.CleaningJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # Cleaner assigned or admin
    if user.role not in (models.UserRole.admin,) and not (user.role == models.UserRole.cleaner and job.cleaner and job.cleaner.user_id == user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    item = db.query(models.ChecklistItem).filter(models.ChecklistItem.id == item_id, models.ChecklistItem.job_id == job_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    media_dir = _ensure_media_dir()
    ext = os.path.splitext(file.filename or "upload.bin")[1]
    fname = f"job{job_id}_item{item_id}_{int(datetime.utcnow().timestamp())}{ext}"
    dest = os.path.join(media_dir, fname)
    with open(dest, "wb") as f:
        f.write(await file.read())
    item.photo_path = f"/media/{fname}"
    db.commit()
    db.refresh(item)
    return item


@router.post("/{job_id}/complete", response_model=JobOut)
def mark_complete(job_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    job = db.query(models.CleaningJob).filter(models.CleaningJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if user.role not in (models.UserRole.admin,) and not (user.role == models.UserRole.cleaner and job.cleaner and job.cleaner.user_id == user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    all_checked = db.query(models.ChecklistItem).filter(models.ChecklistItem.job_id == job_id, models.ChecklistItem.checked == False).count() == 0  # noqa: E712
    if not all_checked:
        raise HTTPException(status_code=400, detail="All checklist items must be checked before completion")
    job.status = models.JobStatus.completed
    job.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job


@router.post("/{job_id}/rating")
def rate_job(job_id: int, payload: RatingCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if user.role != models.UserRole.host and user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Only hosts/admin can rate")
    job = db.query(models.CleaningJob).filter(models.CleaningJob.id == job_id).first()
    if not job or job.status != models.JobStatus.completed:
        raise HTTPException(status_code=400, detail="Job not completed or not found")
    host = db.query(models.Host).filter(models.Host.user_id == user.id).first()
    if user.role == models.UserRole.host:
        prop = db.query(models.Property).filter(models.Property.id == job.property_id).first()
        if not host or not prop or prop.host_id != host.id:
            raise HTTPException(status_code=403, detail="Host does not own this property")
    if not job.cleaner_id:
        raise HTTPException(status_code=400, detail="Job has no cleaner")

    # One rating per job
    existing = db.query(models.Rating).filter(models.Rating.job_id == job_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Rating already exists")

    rating = models.Rating(job_id=job.id, host_id=host.id if host else 0, cleaner_id=job.cleaner_id, stars=payload.stars, feedback=payload.feedback)
    db.add(rating)
    # Update cleaner aggregates
    cleaner = db.query(models.Cleaner).filter(models.Cleaner.id == job.cleaner_id).first()
    if cleaner:
        total = (cleaner.avg_rating or 0) * cleaner.ratings_count + payload.stars
        cleaner.ratings_count += 1
        cleaner.avg_rating = total / cleaner.ratings_count
    db.commit()
    return {"status": "ok"}


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    job = db.query(models.CleaningJob).filter(models.CleaningJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Not found")
    return job

