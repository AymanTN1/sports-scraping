from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency safety
    load_dotenv = None


BASE_DIR = Path(__file__).resolve().parents[2]
if load_dotenv is not None:
    load_dotenv(BASE_DIR / ".env")


class Settings:
    project_name: str = "MarketPulse API"
    project_version: str = "3.0.0"
    api_prefix: str = "/api/v1"
    docs_url: str = "/api/docs"
    openapi_url: str = "/api/openapi.json"
    default_database_path: Path = BASE_DIR / "data" / "sportpulse.db"
    _raw_db_url: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{default_database_path.as_posix()}",
    )
    database_url: str = (
        _raw_db_url.replace("postgres://", "postgresql://", 1)
        if _raw_db_url.startswith("postgres://")
        else _raw_db_url
    )
    scheduler_timezone: str = os.getenv("SCHEDULER_TIMEZONE", "Africa/Casablanca")
    scheduler_hour: int = int(os.getenv("SCHEDULER_HOUR", "6"))
    scheduler_minute: int = int(os.getenv("SCHEDULER_MINUTE", "0"))
    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(",")
        if origin.strip()
    ]
    bootstrap_from_csv: bool = os.getenv("BOOTSTRAP_FROM_CSV", "true").lower() == "true"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


settings = Settings()
