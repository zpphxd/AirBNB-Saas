from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    role: str
    name: Optional[str] = None
    phone: Optional[str] = None


class TokenResponse(BaseModel):
    token: str


class PropertyCreate(BaseModel):
    name: str
    address: str


class PropertyOut(BaseModel):
    id: int
    name: str
    address: str
    class Config:
        from_attributes = True


class ChecklistItemIn(BaseModel):
    text: str


class ChecklistItemOut(BaseModel):
    id: int
    text: str
    checked: bool
    photo_path: Optional[str] = None
    class Config:
        from_attributes = True


class JobCreate(BaseModel):
    property_id: int
    booking_start: datetime
    booking_end: datetime
    checklist: List[ChecklistItemIn] = []


class JobOut(BaseModel):
    id: int
    property_id: int
    booking_start: datetime
    booking_end: datetime
    status: str
    cleaner_id: Optional[int]
    checklist_items: List[ChecklistItemOut] = []
    class Config:
        from_attributes = True


class ClaimJobRequest(BaseModel):
    pass


class TickChecklistRequest(BaseModel):
    item_ids: List[int]


class RatingCreate(BaseModel):
    stars: int = Field(ge=1, le=5)
    feedback: Optional[str] = None


class BookingPeriod(BaseModel):
    start: datetime
    end: datetime

