from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    Boolean,
    Text,
    Float,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .database import Base


class UserRole(str, Enum):
    host = "host"
    cleaner = "cleaner"
    admin = "admin"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), nullable=False)
    api_token: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    host_profile: Mapped[Optional[Host]] = relationship("Host", back_populates="user", uselist=False)
    cleaner_profile: Mapped[Optional[Cleaner]] = relationship("Cleaner", back_populates="user", uselist=False)


class Host(Base):
    __tablename__ = "hosts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))

    user: Mapped[User] = relationship("User", back_populates="host_profile")
    properties: Mapped[list[Property]] = relationship("Property", back_populates="host")


class Cleaner(Base):
    __tablename__ = "cleaners"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    avg_rating: Mapped[Optional[float]] = mapped_column(Float, default=0)
    ratings_count: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped[User] = relationship("User", back_populates="cleaner_profile")
    jobs: Mapped[list[CleaningJob]] = relationship("CleaningJob", back_populates="cleaner")


class Property(Base):
    __tablename__ = "properties"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    host_id: Mapped[int] = mapped_column(ForeignKey("hosts.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str] = mapped_column(Text)

    host: Mapped[Host] = relationship("Host", back_populates="properties")
    jobs: Mapped[list[CleaningJob]] = relationship("CleaningJob", back_populates="property")


class JobStatus(str, Enum):
    open = "open"
    claimed = "claimed"
    in_progress = "in_progress"
    completed = "completed"


class CleaningJob(Base):
    __tablename__ = "cleaning_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), index=True)
    booking_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    booking_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[JobStatus] = mapped_column(SAEnum(JobStatus), default=JobStatus.open)
    cleaner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cleaners.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    property: Mapped[Property] = relationship("Property", back_populates="jobs")
    cleaner: Mapped[Optional[Cleaner]] = relationship("Cleaner", back_populates="jobs")
    checklist_items: Mapped[list[ChecklistItem]] = relationship("ChecklistItem", back_populates="job", cascade="all, delete-orphan")
    rating: Mapped[Optional[Rating]] = relationship("Rating", back_populates="job", uselist=False)


class ChecklistItem(Base):
    __tablename__ = "checklist_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("cleaning_jobs.id"), index=True)
    text: Mapped[str] = mapped_column(String(255), nullable=False)
    checked: Mapped[bool] = mapped_column(Boolean, default=False)
    checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    photo_path: Mapped[Optional[str]] = mapped_column(String(512))

    job: Mapped[CleaningJob] = relationship("CleaningJob", back_populates="checklist_items")


class Rating(Base):
    __tablename__ = "ratings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("cleaning_jobs.id"), unique=True)
    host_id: Mapped[int] = mapped_column(ForeignKey("hosts.id"))
    cleaner_id: Mapped[int] = mapped_column(ForeignKey("cleaners.id"))
    stars: Mapped[int] = mapped_column(Integer)
    feedback: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped[CleaningJob] = relationship("CleaningJob", back_populates="rating")

