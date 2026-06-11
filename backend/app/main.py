from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import auth, external, public, silent_auth, surveys
from app.core.config import settings
from app.middleware.security_headers import SecurityMiddleware

app = FastAPI(
    title="Survey Platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityMiddleware)


@app.get("/health")
async def health_check():
    return {"status": "ok", "env": settings.APP_ENV}


app.include_router(auth.router)
app.include_router(silent_auth.router)
app.include_router(surveys.router)
app.include_router(public.router)
app.include_router(external.router)
app.include_router(external.integrations_router)

_upload_dir = Path(settings.UPLOAD_DIR)
_upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_upload_dir)), name="uploads")
