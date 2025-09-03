from __future__ import annotations
import os
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .services.scheduler import SCHEDULER
from .routers import auth as auth_router
from .routers import jobs as jobs_router
from .routers import properties as properties_router
from .database import SessionLocal
from . import models


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
    # Demo users to bypass login when DEMO_MODE=true
    import os as _os
    if _os.getenv('DEMO_MODE', 'false').lower() == 'true':
        db = SessionLocal()
        try:
            def ensure_user(email: str, role: models.UserRole):
                u = db.query(models.User).filter(models.User.email == email).first()
                if not u:
                    u = models.User(email=email, password_hash='x', role=role)
                    db.add(u); db.flush()
                    if role == models.UserRole.host:
                        db.add(models.Host(user_id=u.id, name='Demo Host'))
                    if role == models.UserRole.cleaner:
                        db.add(models.Cleaner(user_id=u.id, name='Demo Cleaner'))
                return u
            ensure_user('demo_host@local', models.UserRole.host)
            ensure_user('demo_cleaner@local', models.UserRole.cleaner)
            ensure_user('demo_admin@local', models.UserRole.admin)
            db.commit()
        finally:
            db.close()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    SCHEDULER.stop()


# Consistent error envelope for HTTPExceptions
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    from fastapi import HTTPException
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail if isinstance(exc.detail, str) else "HTTP error",
            }
        })
    # Unhandled
    return JSONResponse(status_code=500, content={
        "error": {"code": 500, "message": "Internal Server Error"}
    })


app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
app.include_router(properties_router.router, prefix="/properties", tags=["properties"])
app.include_router(jobs_router.router, prefix="/jobs", tags=["jobs"])

# Serve uploaded media
media_path = ensure_media_dir()
app.mount("/media", StaticFiles(directory=media_path), name="media")

# Serve minimal UI for demo at /ui and redirect root to it
root_dir = os.path.dirname(os.path.dirname(__file__))
ui_dir = os.path.join(root_dir, "ui")
frontend_dist = os.path.join(root_dir, "frontend", "dist")
os.makedirs(ui_dir, exist_ok=True)
app.mount("/ui", StaticFiles(directory=ui_dir, html=True), name="ui")
if os.path.isdir(frontend_dist):
    app.mount("/app", StaticFiles(directory=frontend_dist, html=True), name="app")


@app.get("/")
async def root():
    # Prefer React app if built
    if os.path.isdir(frontend_dist):
        return RedirectResponse(url="/app/")
    return RedirectResponse(url="/ui/")


@app.get("/ui")
async def ui_redirect():
    return RedirectResponse(url="/ui/")


@app.get("/health")
async def health():
    return {"status": "ok"}
