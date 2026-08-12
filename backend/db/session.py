from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core import settings
from backend.db.base import Base


connect_args = {"check_same_thread": False} if settings.is_sqlite else {}
engine = create_engine(settings.database_url, future=True, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    from backend.models import article, source  # noqa: F401
    from sqlalchemy import text

    Base.metadata.create_all(bind=engine)

    # Migrations automatiques pour les colonnes V2
    with engine.connect() as conn:
        try:
            if settings.is_sqlite:
                conn.execute(text("ALTER TABLE articles ADD COLUMN fee_numeric FLOAT DEFAULT 0;"))
            else:
                conn.execute(text("ALTER TABLE articles ADD COLUMN IF NOT EXISTS fee_numeric DOUBLE PRECISION DEFAULT 0;"))
            conn.commit()
        except Exception:
            pass

        try:
            if settings.is_sqlite:
                conn.execute(text("ALTER TABLE articles ADD COLUMN semantic_hash VARCHAR(128);"))
            else:
                conn.execute(text("ALTER TABLE articles ADD COLUMN IF NOT EXISTS semantic_hash VARCHAR(128);"))
            conn.commit()
        except Exception:
            pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
