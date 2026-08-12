from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from backend.models import Article, Source


class ArticleRepository:
    def __init__(self, db: Session):
        self.db = db

    def count(self) -> int:
        return int(self.db.execute(select(func.count(Article.id))).scalar_one())

    def get_by_external_key(self, external_key: str) -> Article | None:
        return self.db.execute(select(Article).where(Article.external_key == external_key)).scalar_one_or_none()

    def get(self, article_id: int) -> Article | None:
        stmt = select(Article).options(joinedload(Article.source)).where(Article.id == article_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list(
        self,
        *,
        page: int,
        page_size: int,
        category: str | None = None,
        league: str | None = None,
        club: str | None = None,
        status: str | None = None,
        source_name: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Article], int]:
        filters = []
        if category:
            filters.append(or_(Article.category == category, Article.league == category))
        if league:
            filters.append(or_(Article.league == league, Article.category == league))
        if club:
            filters.append(or_(Article.from_club.ilike(f"%{club}%"), Article.to_club.ilike(f"%{club}%"), Article.title.ilike(f"%{club}%")))
        if status:
            filters.append(Article.status == status)
        if source_name:
            filters.append(Source.name == source_name)
        if search:
            term = f"%{search.strip()}%"
            filters.append(or_(
                Article.title.ilike(term),
                Article.summary.ilike(term),
                Article.player_name.ilike(term),
                Article.from_club.ilike(term),
                Article.to_club.ilike(term)
            ))

        total_stmt = select(func.count(Article.id)).join(Source)
        items_stmt = (
            select(Article)
            .join(Source)
            .options(joinedload(Article.source))
            .order_by(Article.published_at.desc().nullslast(), Article.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        if filters:
            total_stmt = total_stmt.where(*filters)
            items_stmt = items_stmt.where(*filters)

        total = int(self.db.execute(total_stmt).scalar_one())
        items = list(self.db.execute(items_stmt).unique().scalars().all())
        return items, total

    def category_counts(self) -> dict[str, int]:
        stmt = (
            select(Article.category, func.count(Article.id))
            .group_by(Article.category)
            .order_by(func.count(Article.id).desc(), Article.category.asc())
        )
        return {category or "Autre": int(count) for category, count in self.db.execute(stmt).all()}

    def league_list(self) -> list[str]:
        stmt = select(Article.league).where(Article.league.isnot(None)).distinct()
        return [str(x[0]) for x in self.db.execute(stmt).all() if x[0]]

    def club_list(self) -> list[str]:
        stmt_from = select(Article.from_club).where(Article.from_club.isnot(None)).distinct()
        stmt_to = select(Article.to_club).where(Article.to_club.isnot(None)).distinct()
        from_clubs = [str(x[0]) for x in self.db.execute(stmt_from).all() if x[0]]
        to_clubs = [str(x[0]) for x in self.db.execute(stmt_to).all() if x[0]]
        return sorted(list(set(from_clubs + to_clubs)))

    def status_list(self) -> list[str]:
        stmt = select(Article.status).where(Article.status.isnot(None)).distinct()
        return [str(x[0]) for x in self.db.execute(stmt).all() if x[0]]

    def source_counts(self) -> dict[str, int]:
        stmt = (
            select(Source.name, func.count(Article.id))
            .join(Article, Article.source_id == Source.id)
            .group_by(Source.name)
            .order_by(func.count(Article.id).desc(), Source.name.asc())
        )
        return {name: int(count) for name, count in self.db.execute(stmt).all()}

    def average_credibility(self) -> float:
        value = self.db.execute(select(func.avg(Article.credibility_score))).scalar_one()
        return round(float(value or 0), 2)
