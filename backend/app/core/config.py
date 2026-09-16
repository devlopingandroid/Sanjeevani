"""Centralized configuration for SANJEEVNI Backend.

Reads settings from environment variables or .env file with strong validation.
"""
from typing import List, Union, Optional
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    """Application settings with environment variable bindings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Project metadata
    PROJECT_NAME: str = "SANJEEVNI API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # development | staging | production
    API_V1_STR: str = "/api/v1"

    # Database
    # Default to local SQLite for local dev/testing if PostgreSQL URL is not provided.
    # Production Supabase format: postgresql+psycopg2://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
    DATABASE_URL: str = "sqlite:///./sanjeevani_dev.db"

    # Supabase Specific Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # USB Serial (Development Transport)
    ESP32_SERIAL_PORT: Optional[str] = None  # e.g., "COM3" on Windows or "/dev/ttyUSB0" on Linux
    ESP32_SERIAL_BAUDRATE: int = 115200
    ESP32_SERIAL_DEVICE_ID: str = "ESP32_WEARABLE_DEV"
    ESP32_SERIAL_AUTO_RECONNECT: bool = True
    ESP32_SERIAL_RECONNECT_DELAY_SECONDS: float = 2.0

    # ML Model
    MODEL_PATH: str = os.path.join("models", "Sanjeevni_Best_Stress_Model.pkl")

    # Security & JWT
    JWT_SECRET: str = "sanjeevni-dev-insecure-secret-key-change-in-production-32b"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Mistral AI Integration
    MISTRAL_API_KEY: Optional[str] = None
    MISTRAL_MODEL: str = "open-mistral-7b"
    MISTRAL_BASE_URL: str = "https://api.mistral.ai"
    MISTRAL_TIMEOUT_SECONDS: float = 30.0

    # Risk Engine Lookback Window Configuration
    RISK_ENGINE_LOOKBACK_COUNT: int = 5
    RISK_ENGINE_LOOKBACK_MINUTES: int = 60

    # Trusted Contact Notification Provider Configuration
    NOTIFICATION_PROVIDER: str = "console"  # console | twilio | twilio_sms | twilio_whatsapp | webhook
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_PHONE: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None
    NOTIFICATION_WEBHOOK_URL: Optional[str] = None
    NOTIFICATION_WEBHOOK_SECRET: Optional[str] = None
    NOTIFICATION_TIMEOUT_SECONDS: float = 10.0
    NOTIFICATION_MAX_RETRIES: int = 3

    @property
    def effective_twilio_from_phone(self) -> Optional[str]:
        return self.TWILIO_FROM_PHONE or self.TWILIO_FROM_NUMBER


    # YouTube Data API v3 Integration
    YOUTUBE_API_KEY: Optional[str] = None
    YOUTUBE_API_BASE_URL: str = "https://www.googleapis.com/youtube/v3"
    YOUTUBE_MAX_RESULTS: int = 5


    # Uploads & Media
    @property
    def uploads_dir(self) -> str:
        d = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
        os.makedirs(os.path.join(d, "avatars"), exist_ok=True)
        return d

    @property
    def avatars_dir(self) -> str:
        d = os.path.join(self.uploads_dir, "avatars")
        os.makedirs(d, exist_ok=True)
        return d

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Logging
    LOG_LEVEL: str = "INFO"

    # Wearable Device Parameters
    DEVICE_HEARTBEAT_TIMEOUT_SECONDS: int = 30  # Considered STALE after 30s
    DEVICE_DISCONNECT_TIMEOUT_SECONDS: int = 90  # Considered DISCONNECTED after 90s
    BUFFER_WINDOW_SECONDS: int = 30
    EXPECTED_SAMPLING_RATE_HZ: int = 25  # 25 Hz as configured in ESP32 (interval = 40ms)


settings = Settings()
