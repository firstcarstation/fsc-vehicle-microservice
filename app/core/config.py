from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # NOTE: ignore unknown env vars so shared .env files
    # (e.g. AWS_* for other services) don't crash startup.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    APP_ENV: Literal["local", "dev", "prod"] = "local"
    APP_NAME: str = "fsc-vehicle-microservice"
    APP_VERSION: str = "0.1.0"
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Optional outbound integrations (empty = skip call / use local fallback where applicable).
    USER_MS_BASE_URL: str = ""
    USER_MS_VALIDATE_PATH: str = "/api/u1/users/internal/validate"
    USER_MS_INTERNAL_API_KEY: str = ""

    INTERNAL_API_KEY: str = ""

    MEDIA_MS_BASE_URL: str = ""
    MEDIA_MS_UPLOAD_PATH: str = "/api/v1/media/upload"

    # Optional: if set and there is no local row in vehicle_positions, GET tracking falls back here.
    TRACKING_MS_BASE_URL: str = ""
    TRACKING_MS_VEHICLE_PATH: str = "/api/v1/vehicles/{vehicle_id}/tracking"

    TICKET_MS_BASE_URL: str = ""
    TICKET_MS_CREATE_PATH: str = "/api/v1/tickets/create"
    TICKET_MS_APPROVE_PATH: str = "/api/v1/tickets/approve"

    ANALYTICS_MS_BASE_URL: str = ""
    ANALYTICS_MS_VEHICLE_SUMMARY_PATH: str = "/api/v1/analytics/vehicle-summary"

    HTTP_CLIENT_TIMEOUT_SEC: float = 15.0
    UPLOAD_MAX_MB: int = Field(default=10, description="Max multipart upload size (MB)")

    # When MEDIA_MS is not set, files are stored under this directory and served via StaticFiles.
    LOCAL_UPLOAD_DIR: str = "uploads"
    PUBLIC_APP_URL: str = "http://localhost:8000"

    # AWS S3 uploads (optional; when configured, media uploads go to S3 instead of local disk)
    AWS_S3_BUCKET: str = ""
    AWS_REGION: str = ""
    AWS_PUBLIC_BASE_URL: str = ""
    AWS_UPLOAD_PREFIX: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]


settings = get_settings()
