from __future__ import annotations
from io import BytesIO
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.main import app




def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def run():
    with TestClient(app) as client:
        # Register users
        r = client.post("/auth/register", json={"email": "host@example.com", "password": "secret123", "role": "host", "name": "Host A"})
        assert r.status_code == 200, r.text
        host_token = r.json()["token"]

        r = client.post("/auth/register", json={"email": "cleaner@example.com", "password": "secret123", "role": "cleaner", "name": "Cleaner A"})
        assert r.status_code == 200, r.text
        cleaner_token = r.json()["token"]

        # Create property
        r = client.post("/properties/", json={"name": "Downtown Flat", "address": "123 Main St"}, headers=auth_headers(host_token))
        assert r.status_code == 200, r.text
        prop = r.json()

        # Create job
        start = (datetime.utcnow() + timedelta(days=1)).isoformat()
        end = (datetime.utcnow() + timedelta(days=1, hours=3)).isoformat()
        r = client.post("/jobs/", json={
            "property_id": prop["id"],
            "booking_start": start,
            "booking_end": end,
            "checklist": [{"text": "Change linens"}, {"text": "Dust surfaces"}]
        }, headers=auth_headers(host_token))
        assert r.status_code == 200, r.text
        job = r.json()

        # Cleaner lists and claims
        r = client.get("/jobs/open", headers=auth_headers(cleaner_token))
        assert r.status_code == 200 and len(r.json()) >= 1
        r = client.post(f"/jobs/{job['id']}/claim", headers=auth_headers(cleaner_token))
        assert r.status_code == 200, r.text

        # Tick checklist
        item_ids = [it["id"] for it in job["checklist_items"]]
        r = client.post(f"/jobs/{job['id']}/checklist/tick", json={"item_ids": item_ids}, headers=auth_headers(cleaner_token))
        assert r.status_code == 200, r.text

        # Upload photo for first item
        img_bytes = BytesIO(b"\x89PNG\r\n\x1a\n\x00fake")
        files = {"file": ("evidence.png", img_bytes, "image/png")}
        r = client.post(f"/jobs/{job['id']}/checklist/{item_ids[0]}/photo", files=files, headers=auth_headers(cleaner_token))
        assert r.status_code == 200, r.text

        # Mark complete
        r = client.post(f"/jobs/{job['id']}/complete", headers=auth_headers(cleaner_token))
        assert r.status_code == 200, r.text

        # Host rates
        r = client.post(f"/jobs/{job['id']}/rating", json={"stars": 5, "feedback": "Great work!"}, headers=auth_headers(host_token))
        assert r.status_code == 200, r.text

        return "OK"


if __name__ == "__main__":
    print(run())
