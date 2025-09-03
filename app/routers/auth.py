from __future__ import annotations
import hashlib
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from ..schemas import UserCreate, TokenResponse


router = APIRouter()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@router.post("/register", response_model=TokenResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    role_val = user.role.lower()
    if role_val not in {r.value for r in models.UserRole}:
        raise HTTPException(status_code=400, detail="Invalid role")

    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    token = secrets.token_hex(16)
    u = models.User(email=user.email, password_hash=hash_password(user.password), role=models.UserRole(role_val), api_token=token)
    db.add(u)
    db.flush()

    if u.role == models.UserRole.host:
        db.add(models.Host(user_id=u.id, name=user.name, phone=user.phone))
    elif u.role == models.UserRole.cleaner:
        db.add(models.Cleaner(user_id=u.id, name=user.name, phone=user.phone))
    db.commit()
    return TokenResponse(token=token)


@router.post("/login", response_model=TokenResponse)
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or user.password_hash != hash_password(password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.api_token:
        user.api_token = secrets.token_hex(16)
        db.commit()
    return TokenResponse(token=user.api_token)


def get_current_user(Authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> models.User:
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = Authorization.split(" ", 1)[1]
    user = db.query(models.User).filter(models.User.api_token == token).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


def require_role(required: models.UserRole):
    def _dep(user: models.User = Depends(get_current_user)) -> models.User:
        if user.role != required:
            raise HTTPException(status_code=403, detail="Forbidden for role")
        return user
    return _dep

