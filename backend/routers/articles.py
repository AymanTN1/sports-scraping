from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.repositories import ArticleRepository, SourceRepository
from backend.schemas import ArticleItem, ArticleListResponse, ArticleStatsResponse, CsvImportResponse, SourceItem
from backend.services import ArticleService, CsvIngestionService


router = APIRouter(prefix="/api/v1/articles", tags=["articles"])


def get_article_service(db: Session = Depends(get_db)) -> ArticleService:
    return ArticleService(ArticleRepository(db), SourceRepository(db))


@router.get("", response_model=ArticleListResponse)
def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=5000),
    category: str | None = None,
    source: str | None = None,
    search: str | None = None,
    service: ArticleService = Depends(get_article_service),
):
    return service.list_articles(
        page=page,
        page_size=page_size,
        category=category,
        source_name=source,
        search=search,
    )


@router.get("/categories", response_model=list[str])
def list_categories(service: ArticleService = Depends(get_article_service)):
    return service.list_categories()


@router.get("/sources", response_model=list[SourceItem])
def list_sources(service: ArticleService = Depends(get_article_service)):
    return service.list_sources()


@router.get("/stats", response_model=ArticleStatsResponse)
def get_stats(service: ArticleService = Depends(get_article_service)):
    return service.get_stats()


@router.post("/import-csv", response_model=CsvImportResponse)
def import_csv(db: Session = Depends(get_db)):
    ingestion = CsvIngestionService(db)
    csv_path = ingestion.get_default_csv_path()
    if not csv_path:
        raise HTTPException(status_code=404, detail="Aucun CSV d'articles disponible")
    return ingestion.import_csv(csv_path)


@router.get("/{article_id}", response_model=ArticleItem)
def get_article(article_id: int, service: ArticleService = Depends(get_article_service)):
    article = service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable")
    return article
