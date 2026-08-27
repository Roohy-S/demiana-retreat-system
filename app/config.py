import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True
    )

    PROJECT_NAME: str = "بيت الخلوة – دير القديسة دميانة – ببراري بلقاس"
    PROJECT_SHORT_NAME: str = "بيت الخلوة بدير القديسة دميانة"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "demiana_monastery_retreat_super_secret_jwt_key_2026_prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database (Supabase PostgreSQL or local SQLite)
    DATABASE_URL: str = ""
    
    # Supabase direct settings (Optional)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    
    # Gmail / SMTP Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_NAME: str = "بيت الخلوة – دير القديسة دميانة ببراري بلقاس"
    SMTP_USE_TLS: bool = True
    EMAIL_VERIFICATION_EXPIRY_MINUTES: int = 15
    REQUIRE_EMAIL_VERIFICATION: bool = True
    
    # Storage
    PRIVATE_STORAGE_DIR: Path = BASE_DIR / "app" / "storage"
    MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS: set = {"jpg", "jpeg", "png", "pdf"}
    
    # Business Rules Defaults
    DEFAULT_RETREAT_NIGHTS: int = 3
    MIN_BOOKING_INTERVAL_MONTHS: int = 3
    MIN_APPLICANT_AGE_YEARS: int = 15
    DEFAULT_PERIOD_CAPACITY: int = 20

    @property
    def async_database_url(self) -> str:
        url = self.DATABASE_URL.strip() if self.DATABASE_URL else ""
        if not url:
            return f"sqlite+aiosqlite:///{BASE_DIR / 'demiana_retreat.db'}"
        
        # Convert postgres:// or postgresql:// to postgresql+asyncpg://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        # Strip sslmode query param if present for asyncpg compatibility
        if "sslmode=" in url:
            import re
            url = re.sub(r'[\?\&]sslmode=[^&]+', '', url)
            if '?' not in url and '&' in url:
                url = url.replace('&', '?', 1)
        return url

settings = Settings()
settings.PRIVATE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
