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
    allow_origin_regex=settings.CORS_ORIGIN_REGEX if getattr(settings, "CORS_ORIGIN_REGEX", None) else None,
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

    # Automatically seed empty databases (e.g. on fresh Render/cloud deployments)
    if getattr(settings, "AUTO_SEED", False):
        try:
            from app.models import Bureau
            from app.core.database import SessionLocal
            with SessionLocal() as db:
                if db.query(Bureau).count() == 0:
                    import logging
                    logger = logging.getLogger("uvicorn")
                    logger.info("Empty database detected with AUTO_SEED=True. Seeding demo data...")
                    seed_fn = None
                    try:
                        from scripts.seed_demo_data import seed_data
                        seed_fn = seed_data
                    except ImportError:
                        for cand in [
                            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")),
                            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")),
                        ]:
                            script_file = os.path.join(cand, "seed_demo_data.py")
                            if os.path.isfile(script_file):
                                import importlib.util
                                spec = importlib.util.spec_from_file_location("seed_demo_data_mod", script_file)
                                if spec and spec.loader:
                                    mod = importlib.util.module_from_spec(spec)
                                    spec.loader.exec_module(mod)
                                    seed_fn = getattr(mod, "seed_data", None)
                                    if seed_fn:
                                        break

                    if seed_fn:
                        seed_fn()
                        logger.info("Database auto-seeded successfully.")
                    else:
                        logger.warning("Could not find seed_demo_data script to auto-seed.")
        except Exception as err:
            import logging
            logging.getLogger("uvicorn").warning(f"AUTO_SEED check failed: {err}")


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
