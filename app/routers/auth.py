from __future__ import annotations
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Header
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..database import get_db, SessionLocal
from .. import models
from ..schemas import UserCreate, TokenResponse


router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(tz=timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/register", response_model=TokenResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    role_val = user.role.lower()
    if role_val not in {r.value for r in models.UserRole}:
        raise HTTPException(status_code=400, detail="Invalid role")

    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    u = models.User(email=user.email, password_hash=hash_password(user.password), role=models.UserRole(role_val))
    db.add(u)
    db.flush()

    if u.role == models.UserRole.host:
        db.add(models.Host(user_id=u.id, name=user.name, phone=user.phone))
    elif u.role == models.UserRole.cleaner:
        db.add(models.Cleaner(user_id=u.id, name=user.name, phone=user.phone))
    db.commit()
    token = create_access_token({"sub": str(u.id), "role": u.role.value})
    return TokenResponse(token=token)


@router.post("/login", response_model=TokenResponse)
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(token=token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(token: Optional[str] = None, Authorization: Optional[str] = Header(None)):
    """
    Issue a fresh access token. For MVP, we accept a valid (unexpired) JWT passed either
    as Bearer or as body param `token`. In production, use a separate refresh token.
    """
    raw = token
    if not raw and Authorization and Authorization.startswith("Bearer "):
        raw = Authorization.split(" ", 1)[1]
    if not raw:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        payload = jwt.decode(raw, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        # Re-issue short-lived access token
        new_token = create_access_token({"sub": payload.get("sub"), "role": payload.get("role")})
        return TokenResponse(token=new_token)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(Authorization: Optional[str] = Header(None), X_Demo_Role: Optional[str] = Header(None), db: Session = Depends(get_db)) -> models.User:
    # Demo mode: allow bypass with X-Demo-Role
    if os.getenv('DEMO_MODE', 'false').lower() == 'true' and (not Authorization):
        role = (X_Demo_Role or 'host').lower()
        email_map = {
            'host': 'demo_host@local',
            'cleaner': 'demo_cleaner@local',
            'admin': 'demo_admin@local',
        }
        email = email_map.get(role, 'demo_host@local')
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            raise HTTPException(status_code=500, detail="Demo user not initialized")
        return user
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = Authorization.split(" ", 1)[1]
    # Prefer JWT; fallback to legacy api_token if present
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        uid = int(payload.get("sub"))
        user = db.query(models.User).filter(models.User.id == uid).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token user")
        return user
    except jwt.PyJWTError:
        # Legacy token path
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
