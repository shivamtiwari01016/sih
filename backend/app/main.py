import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.api.v1 import api_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Institution Complaint Monitoring & Coordination Platform - DEMO ENVIRONMENT",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
def on_startup():
    # Import every model before creating tables (also helps fresh local installs).
    from app import models  # noqa: F401
    from app.core.migrations import run_light_migrations

    Base.metadata.create_all(bind=engine)
    run_light_migrations()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@app.get("/")
async def root():
    return {
        "project": "Samanvay (समन्वय)",
        "full_name": "Samanvay (समन्वय) – Secure Complaint Coordination System for AICTE",
        "ps_code": "SIH26264",
        "theme": "Smart Automation",
        "status": "running",
        "environment": "SECURE_INTERNAL",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "environment": settings.APP_ENV}
