from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import Source


class SourceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_name(self, name: str) -> Source | None:
        return self.db.execute(select(Source).where(Source.name == name)).scalar_one_or_none()

    def list_all(self) -> list[Source]:
        return list(self.db.execute(select(Source).order_by(Source.name.asc())).scalars().all())

    def create(
        self,
        *,
        name: str,
        language: str | None = None,
        credibility_score: float = 0,
        base_url: str | None = None,
    ) -> Source:
        source = Source(
            name=name,
            language=language,
            credibility_score=credibility_score,
            base_url=base_url,
        )
        self.db.add(source)
        self.db.flush()
        return source
