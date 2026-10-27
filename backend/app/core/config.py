import os
from pydantic_settings import BaseSettings
from typing import List

_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_DEFAULT_DB = f"sqlite:///{os.path.join(_BACKEND_DIR, 'civicresolve.db')}"


class Settings(BaseSettings):
    APP_NAME: str = "Samanvay (समन्वय) – Secure Complaint Coordination System for AICTE"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api"
    SECRET_KEY: str = "change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Comma separated list, e.g. "http://localhost:3000,http://localhost:5173"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:8000"
    CORS_ORIGIN_REGEX: str = r"https://.*\.vercel\.app"

    AUTO_SEED: bool = True

    DATABASE_URL: str = os.environ.get("DATABASE_URL", _DEFAULT_DB)

    REDIS_URL: str = "redis://localhost:6379/0"

    USE_SEMANTIC_MATCHING: bool = True
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    SIMILARITY_THRESHOLD: float = 0.45
    MAX_CANDIDATES: int = 60
    MAX_SUGGESTIONS_PER_COMPLAINT: int = 6
    MAX_SCAN_COMPLAINTS: int = 500
    MAX_SCAN_SUGGESTIONS: int = 120
    # Scoring weights (the score is capped at 0.99)
    TEXT_WEIGHT: float = 0.45
    CATEGORY_WEIGHT: float = 0.30
    SUBCATEGORY_WEIGHT: float = 0.05
    INSTITUTION_WEIGHT: float = 0.20
    CROSS_BUREAU_WEIGHT: float = 0.05
    DOMAIN_TOPIC_SCORE: float = 0.50
    ENABLE_LLM_SUMMARIZATION: bool = False
    OPENAI_API_KEY: str = ""

    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10485760
    ALLOWED_EXTENSIONS: str = "pdf,doc,docx,jpg,jpeg,png,txt"

    DEADLINE_WARNING_DAYS: int = 3
    OVERDUE_ESCALATION_DAYS: int = 7

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@samanvay.demo"

    DEMO_MODE: bool = True
    SHOW_DEMO_BADGE: bool = True

    # Docker Compose database settings (not used directly by the app).
    POSTGRES_USER: str = "civicresolve"
    POSTGRES_PASSWORD: str = "civicresolve_pass"
    POSTGRES_DB: str = "civicresolve_db"

    @property
    def cors_origins(self) -> List[str]:
        if isinstance(self.ALLOWED_ORIGINS, list):
            return self.ALLOWED_ORIGINS
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
