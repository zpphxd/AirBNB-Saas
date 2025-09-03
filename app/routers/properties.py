from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from ..schemas import PropertyCreate, PropertyOut, BookingPeriod
from .auth import get_current_user
from ..services.pms_stub import get_upcoming_bookings


router = APIRouter()


@router.post("/", response_model=PropertyOut)
def create_property(payload: PropertyCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if user.role != models.UserRole.host:
        raise HTTPException(status_code=403, detail="Only hosts can create properties")
    host = db.query(models.Host).filter(models.Host.user_id == user.id).first()
    if not host:
        raise HTTPException(status_code=400, detail="Host profile missing")
    p = models.Property(host_id=host.id, name=payload.name, address=payload.address)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/{property_id}", response_model=PropertyOut)
def get_property(property_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    p = db.query(models.Property).filter(models.Property.id == property_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Not found")
    # Authorization: host who owns it or admin
    if user.role != models.UserRole.admin:
        host = db.query(models.Host).filter(models.Host.user_id == user.id).first()
        if not host or p.host_id != host.id:
            raise HTTPException(status_code=403, detail="Forbidden")
    return p


@router.get("/{property_id}/bookings", response_model=list[BookingPeriod])
def upcoming_bookings(property_id: int, user: models.User = Depends(get_current_user)):
    # Any authenticated user can view mocked bookings for demo
    data = get_upcoming_bookings(property_id)
    return data


@router.get("/mine", response_model=list[PropertyOut])
def my_properties(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    if user.role != models.UserRole.host and user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Only hosts/admin can list properties")
    if user.role == models.UserRole.admin:
        props = db.query(models.Property).offset(offset).limit(limit).all()
        return props
    host = db.query(models.Host).filter(models.Host.user_id == user.id).first()
    if not host:
        return []
    props = (
        db.query(models.Property)
        .filter(models.Property.host_id == host.id)
        .order_by(models.Property.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return props
