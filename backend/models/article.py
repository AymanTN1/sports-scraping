from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_date: Mapped[str | None] = mapped_column(String(128), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    category: Mapped[str] = mapped_column(String(128), index=True, default="Premier League")
    sentiment: Mapped[str | None] = mapped_column(String(32), nullable=True, default="Neutre")
    player_name: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    from_club: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    to_club: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    league: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    transfer_fee: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str | None] = mapped_column(String(64), nullable=True, default="RUMEUR 📰")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    credibility_score: Mapped[float] = mapped_column(Float, default=0)
    fee_numeric: Mapped[float | None] = mapped_column(Float, nullable=True, default=0)
    semantic_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    source = relationship("Source", back_populates="articles")
