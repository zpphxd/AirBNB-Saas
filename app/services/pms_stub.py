from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Dict


def get_upcoming_bookings(property_id: int) -> List[Dict]:
    """
    Mock booking periods for a property. In production, fetch from Airbnb/PMS.
    """
    base = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    return [
        {"start": base + timedelta(days=3, hours=11), "end": base + timedelta(days=6, hours=15)},
        {"start": base + timedelta(days=10, hours=11), "end": base + timedelta(days=13, hours=15)},
    ]


def create_smartlock_code_stub(property_id: int, job_id: int) -> str:
    """Placeholder for smart-lock code provisioning."""
    return f"CODE-{property_id}-{job_id}"


def initiate_payment_stub(job_id: int, amount_cents: int) -> str:
    """Placeholder for payments integration."""
    return f"PAYMENT_INTENT_{job_id}_{amount_cents}"

