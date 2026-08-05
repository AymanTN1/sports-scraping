from __future__ import annotations

from backend.repositories import ArticleRepository, SourceRepository
from backend.schemas.article import ArticleItem, ArticleListResponse, ArticleStatsResponse
from backend.schemas.source import SourceItem


class ArticleService:
    def __init__(self, article_repository: ArticleRepository, source_repository: SourceRepository):
        self.article_repository = article_repository
        self.source_repository = source_repository

    def list_articles(
        self,
        *,
        page: int = 1,
        page_size: int = 100,
        category: str | None = None,
        source_name: str | None = None,
        search: str | None = None,
    ) -> ArticleListResponse:
        items, total = self.article_repository.list(
            page=page,
            page_size=page_size,
            category=category,
            source_name=source_name,
            search=search,
        )
        return ArticleListResponse(
            items=[self._serialize_article(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_article(self, article_id: int) -> ArticleItem | None:
        article = self.article_repository.get(article_id)
        return self._serialize_article(article) if article else None

    def list_categories(self) -> list[str]:
        return list(self.article_repository.category_counts().keys())

    def list_sources(self) -> list[SourceItem]:
        return [SourceItem.model_validate(source) for source in self.source_repository.list_all()]

    def get_stats(self) -> ArticleStatsResponse:
        categories = self.article_repository.category_counts()
        sources = self.article_repository.source_counts()
        return ArticleStatsResponse(
            total_articles=self.article_repository.count(),
            total_categories=len(categories),
            total_sources=len(sources),
            average_credibility=self.article_repository.average_credibility(),
            categories=categories,
            sources=sources,
        )

    @staticmethod
    def _serialize_article(article) -> ArticleItem:
        return ArticleItem(
            id=article.id,
            title=article.title,
            source=article.source.name if article.source else "Source inconnue",
            source_meta=SourceItem.model_validate(article.source) if article.source else None,
            category=article.category or "Macroéconomie",
            sentiment=getattr(article, "sentiment", "Neutre") or "Neutre",
            date=article.raw_date,
            published_at=article.published_at,
            language=article.language,
            summary=article.summary,
            url=article.url,
            image_url=article.image_url,
            image_caption=article.image_caption,
            credibility=float(article.credibility_score or 0),
        )
