from __future__ import annotations
import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .services.scheduler import SCHEDULER
from .routers import auth as auth_router
from .routers import jobs as jobs_router
from .routers import properties as properties_router


def ensure_media_dir() -> str:
    root = os.path.dirname(os.path.dirname(__file__))
    media_dir = os.path.join(root, "media")
    os.makedirs(media_dir, exist_ok=True)
    return media_dir


app = FastAPI(title="Airbnb Cleaning & Maintenance Micro-SaaS (MVP)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    init_db()
    SCHEDULER.start()
    ensure_media_dir()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    SCHEDULER.stop()


app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
app.include_router(properties_router.router, prefix="/properties", tags=["properties"])
app.include_router(jobs_router.router, prefix="/jobs", tags=["jobs"])

# Serve uploaded media
media_path = ensure_media_dir()
app.mount("/media", StaticFiles(directory=media_path), name="media")

# Serve minimal UI for demo at /ui and redirect root to it
ui_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui")
os.makedirs(ui_dir, exist_ok=True)
app.mount("/ui", StaticFiles(directory=ui_dir, html=True), name="ui")


@app.get("/")
async def root():
    return RedirectResponse(url="/ui/")
