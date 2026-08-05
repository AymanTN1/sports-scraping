from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from backend.schemas.source import SourceItem


class ArticleItem(BaseModel):
    id: int
    title: str
    source: str
    source_meta: SourceItem | None = None
    category: str
    sentiment: str | None = "Neutre"
    date: str | None = None
    published_at: datetime | None = None
    language: str | None = None
    summary: str | None = None
    url: str | None = None
    image_url: str | None = None
    image_caption: str | None = None
    credibility: float = 0


class ArticleListResponse(BaseModel):
    items: list[ArticleItem]
    total: int
    page: int
    page_size: int


class ArticleStatsResponse(BaseModel):
    total_articles: int
    total_categories: int
    total_sources: int
    average_credibility: float
    categories: dict[str, int]
    sources: dict[str, int]
    sentiments: dict[str, int] = {}



class CsvImportResponse(BaseModel):
    source_file: str
    inserted_articles: int
    updated_articles: int
    total_articles: int
