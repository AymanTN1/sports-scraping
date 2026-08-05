from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.base import Base
from backend.models import Article, Source
from backend.repositories import ArticleRepository, SourceRepository
from backend.services import ArticleService, CsvIngestionService


def build_session():
    engine = create_engine("sqlite:///:memory:", future=True, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return session_factory()


def test_csv_ingestion_creates_articles_and_sources(tmp_path):
    csv_path = tmp_path / "articles.csv"
    pd.DataFrame(
        [
            {
                "title": "Premier sujet football",
                "source": "BBC Sport",
                "lang": "fr",
                "url": "https://example.com/1",
                "date": "2026-04-26",
                "summary": "Resume 1",
                "category": "Football",
                "credibility": 5,
            },
            {
                "title": "Deuxieme sujet tennis",
                "source": "Eurosport FR",
                "lang": "fr",
                "url": "https://example.com/2",
                "date": "2026-04-25",
                "summary": "Resume 2",
                "category": "Tennis",
                "credibility": 4,
            },
        ]
    ).to_csv(csv_path, index=False)

    with build_session() as db:
        result = CsvIngestionService(db).import_csv(csv_path)

        assert result.inserted_articles == 2
        assert result.updated_articles == 0
        assert result.total_articles == 2
        assert db.query(Source).count() == 2
        assert db.query(Article).count() == 2


def test_article_service_stats_are_consistent(tmp_path):
    csv_path = tmp_path / "articles.csv"
    pd.DataFrame(
        [
            {
                "title": "Grand match",
                "source": "BBC Sport",
                "lang": "fr",
                "url": "https://example.com/match",
                "date": "2026-04-26",
                "summary": "Un match important",
                "category": "Football",
                "credibility": 5,
            },
            {
                "title": "Autre match",
                "source": "BBC Sport",
                "lang": "fr",
                "url": "https://example.com/match-2",
                "date": "2026-04-26",
                "summary": "Encore un match",
                "category": "Football",
                "credibility": 5,
            },
        ]
    ).to_csv(csv_path, index=False)

    with build_session() as db:
        CsvIngestionService(db).import_csv(csv_path)
        service = ArticleService(ArticleRepository(db), SourceRepository(db))

        response = service.list_articles(page=1, page_size=20)
        stats = service.get_stats()

        assert response.total == 2
        assert len(response.items) == 2
        assert stats.total_articles == 2
        assert stats.total_categories == 1
        assert stats.total_sources == 1
        assert stats.categories["Football"] == 2
