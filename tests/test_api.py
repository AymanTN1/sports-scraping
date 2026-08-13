"""
MercatoPULSE — Tests Unitaires API (pytest)
============================================
Tests avec client FastAPI en mémoire (TestClient) + SQLite temporaire.
Ces tests s'exécutent sans réseau, sans clé Groq, sans Neon DB.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.base import Base
from backend.db.session import get_db
from backend.main import app

# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_engine():
    """Base de données SQLite en mémoire partagée pour la session de tests."""
    engine = create_engine(
        "sqlite:///./test_mercato.db",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Session DB isolée par test (rollback après chaque test)."""
    SessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient avec override de la dépendance DB."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ──────────────────────────────────────────────────────────────────────
# Tests — Health Check
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_health_check_returns_200(client):
    """L'endpoint /health doit retourner 200 avec le champ status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ("ok", "healthy")


# ──────────────────────────────────────────────────────────────────────
# Tests — Articles Endpoint
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_list_articles_empty_db(client):
    """GET /articles sur une DB vide retourne une liste vide paginée."""
    response = client.get("/api/v1/articles")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert "total" in data
    assert "page" in data


@pytest.mark.unit
def test_list_articles_pagination_params(client):
    """Les paramètres de pagination sont acceptés sans erreur."""
    response = client.get("/api/v1/articles?page=1&page_size=5")
    assert response.status_code == 200


@pytest.mark.unit
def test_list_articles_filter_by_league(client):
    """Le filtre ?league= est accepté (même si 0 résultats)."""
    response = client.get("/api/v1/articles?league=ligue1")
    assert response.status_code in (200, 404)


@pytest.mark.unit
def test_get_article_not_found(client):
    """GET /articles/99999 doit retourner 404."""
    response = client.get("/api/v1/articles/99999")
    assert response.status_code == 404


# ──────────────────────────────────────────────────────────────────────
# Tests — Stats Endpoint
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_get_stats_returns_schema(client):
    """GET /articles/stats retourne les champs attendus."""
    response = client.get("/api/v1/articles/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_articles" in data
    assert "total_sources" in data
    assert isinstance(data["total_articles"], int)


# ──────────────────────────────────────────────────────────────────────
# Tests — OpenAPI / Docs
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_openapi_schema_is_accessible(client):
    """Le schéma OpenAPI doit être accessible."""
    response = client.get("/api/docs")
    assert response.status_code in (200, 307)  # redirect to /docs


@pytest.mark.unit
def test_openapi_json_schema(client):
    """Le JSON OpenAPI doit contenir le title du projet."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "MercatoPULSE" in schema.get("info", {}).get("title", "")
