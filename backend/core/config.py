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
    base_dir: Path = BASE_DIR
    project_name: str = "MercatoPULSE API"
    project_version: str = "3.1.0"
    api_prefix: str = "/api/v1"
    docs_url: str = "/api/docs"
    openapi_url: str = "/api/openapi.json"
    is_serverless: bool = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
    default_database_path: Path = (
        Path("/tmp/mercatopulse.db")
        if is_serverless
        else BASE_DIR / "data" / "mercatopulse.db"
    )
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
        for origin in os.getenv(
            "CORS_ORIGINS",
            "*,http://127.0.0.1:8000,http://localhost:8000,https://mercato-pulse-web-sigma.vercel.app"
        ).split(",")
        if origin.strip()
    ]
    bootstrap_from_csv: bool = os.getenv("BOOTSTRAP_FROM_CSV", "true").lower() == "true"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


settings = Settings()
