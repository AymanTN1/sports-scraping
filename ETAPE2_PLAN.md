# 📋 ÉTAPE 2 — PLAN DÉTAILLÉ DE MIGRATION

## 🎯 Structure Cible Complète

```
project/
├── __init__.py
├── main.py                          ← Déplacé depuis backend/main.py
│
├── api/                             ← ✨ NEW: Fusionné views + controllers
│   ├── __init__.py
│   ├── dependencies.py              ← Dépendances FastAPI centralisées
│   └── routes/
│       ├── __init__.py
│       ├── articles.py              ← articles.py + article_controller.py fusionnés
│       ├── sources.py               ← sources.py + source_controller.py fusionnés
│       ├── reviews.py               ← reviews.py + review_controller.py fusionnés
│       ├── users.py                 ← user_controller.py réorganisé
│       └── ai.py                    ← ai_controller.py réorganisé
│
├── services/                        ← ✓ Garder identique
│   ├── __init__.py
│   ├── scraper_service.py           ← Inchangé
│   ├── nlp_service.py               ← Inchangé
│   ├── credibility_service.py       ← Inchangé
│   ├── ranking_service.py           ← Inchangé
│   ├── auth_service.py              ← Inchangé
│   ├── review_service.py            ← Inchangé
│   └── user_service.py              ← Inchangé
│
├── repositories/                    ← ✓ Garder identique
│   ├── __init__.py
│   ├── base_repository.py           ← Inchangé
│   ├── article_repository.py        ← Inchangé
│   ├── source_repository.py         ← Inchangé
│   ├── review_repository.py         ← Inchangé
│   └── user_repository.py           ← Inchangé
│
├── models/                          ← ✨ RÉORGANISÉ: Séparation claire
│   ├── __init__.py
│   ├── orm/                         ← SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── base.py                  ← Base = declarative_base()
│   │   ├── articles.py              ← Article model
│   │   ├── sources.py               ← Source model
│   │   ├── reviews.py               ← Review model
│   │   └── users.py                 ← User model
│   │
│   └── schemas/                     ← Pydantic validation schemas
│       ├── __init__.py
│       ├── articles.py              ← ArticleCreate, ArticleResponse, etc.
│       ├── sources.py               ← SourceCreate, SourceResponse, etc.
│       ├── reviews.py               ← ReviewCreate, ReviewResponse, etc.
│       └── users.py                 ← UserCreate, UserResponse, etc.
│
├── ai/                              ← ✨ RÉORGANISÉ: Pipeline + processors
│   ├── __init__.py
│   ├── pipeline.py                  ← AIPipeline (orchestration)
│   └── processors/
│       ├── __init__.py
│       ├── classifier.py            ← Classifier (outil)
│       ├── credibility.py           ← Credibility analyzer (outil)
│       ├── summarizer.py            ← Summarizer (outil)
│       └── collector.py             ← Collector (outil)
│
├── core/                            ← ✨ NEW: Configuration centralisée
│   ├── __init__.py
│   ├── database.py                  ← engine, SessionLocal, get_db(), Database class
│   ├── config.py                    ← (Optional) Paramètres configuration
│   └── security.py                  ← (Optional) JWT, auth utilities
│
├── tests/                           ← Tests (à organiser)
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_services.py
│   │   ├── test_repositories.py
│   │   └── test_schemas.py
│   └── integration/
│       └── test_api.py
│
└── requirements.txt                 ← Inchangé (à la racine sportpulse/)
```

---

## 📋 Mapping Détaillé: Ancien → Nouveau

### ✨ A. FUSION API (Views + Controllers)

| Ressource | Avant | Après | Action |
|-----------|-------|-------|--------|
| Articles | `views/articles.py`<br/>`controllers/article_controller.py` | `api/routes/articles.py` | Fusionner |
| Sources | `views/sources.py`<br/>`controllers/source_controller.py` | `api/routes/sources.py` | Fusionner |
| Reviews | `views/reviews.py`<br/>`controllers/review_controller.py` | `api/routes/reviews.py` | Fusionner |
| Users | `controllers/user_controller.py` | `api/routes/users.py` | Déplacer |
| AI | `controllers/ai_controller.py` | `api/routes/ai.py` | Déplacer |
| Deps | Distribuées dans views/ | `api/dependencies.py` | Centraliser |

#### 🔧 Exemple Consolidation: Articles

**AVANT** (2 fichiers):
```
views/articles.py:
- router = APIRouter(...)
- get_article_controller() dépendance
- @router.get("/", response_model=...)
---
controllers/article_controller.py:
- ArticleController class
- .get_articles() method
```

**APRÈS** (1 fichier `api/routes/articles.py`):
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..schemas.articles import ArticleResponse, ArticleCreate
from ..repositories.article_repository import ArticleRepository
from ..services.ranking_service import RankingService
from ..core.database import get_db

router = APIRouter(prefix="/api/v1/articles", tags=["articles"])

# Logique du controller directement comme fonctions/classe
class ArticleHandler:  # Renommé de ArticleController
    def __init__(self, repo, ranking_service):
        self.repo = repo
        self.ranking_service = ranking_service
    
    def get_articles(self, skip: int = 0, limit: int = 50):
        return self.repo.get_all(skip, limit)

def get_article_handler(db: Session = Depends(get_db)) -> ArticleHandler:
    return ArticleHandler(
        ArticleRepository(db),
        RankingService()
    )

@router.get("/", response_model=List[ArticleResponse])
async def list_articles(
    skip: int = 0, 
    limit: int = 50,
    handler: ArticleHandler = Depends(get_article_handler)
):
    return handler.get_articles(skip, limit)
```

---

### ✨ B. SÉPARATION MODÈLES (ORM + Schemas)

#### Part 1: SQLAlchemy ORM

| Avant | Nouveau | Contenu |
|-------|---------|---------|
| `database/models.py` (complète) | `models/orm/base.py` | `Base = declarative_base()` |
| | `models/orm/articles.py` | Classe `Article(Base)` |
| | `models/orm/sources.py` | Classe `Source(Base)` |
| | `models/orm/reviews.py` | Classe `Review(Base)` |
| | `models/orm/users.py` | Classe `User(Base)` |

**Exemple `models/orm/articles.py`**:
```python
"""
models/orm/articles.py - SQLAlchemy ORM for Articles
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Article(Base):
    """Article ORM Model"""
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), unique=True, index=True)
    content = Column(Text)
    # ... rest of columns
    
    source = relationship("Source", back_populates="articles")
    reviews = relationship("Review", back_populates="article")
```

#### Part 2: Pydantic Schemas

| Avant | Nouveau | Contenu |
|-------|---------|---------|
| `schemas/schemas.py` (mélangé) | `models/schemas/articles.py` | ArticleBase, ArticleCreate, ArticleResponse |
| | `models/schemas/sources.py` | SourceBase, SourceCreate, SourceResponse |
| | `models/schemas/reviews.py` | ReviewBase, ReviewCreate, ReviewResponse |
| | `models/schemas/users.py` | UserBase, UserCreate, UserResponse |

**Exemple `models/schemas/articles.py`**:
```python
"""
models/schemas/articles.py - Pydantic schemas for Article validation
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ArticleBase(BaseModel):
    title: str
    content: str
    source_id: int
    url: str
    language: str

class ArticleCreate(ArticleBase):
    summary: Optional[str] = None
    image_url: Optional[str] = None
    publish_date: Optional[datetime] = None

class ArticleResponse(ArticleBase):
    id: int
    scrape_date: datetime
    credibility_score: float
    
    class Config:
        from_attributes = True
```

---

### ✨ C. DÉPLACEMENT Configuration DB

| Avant | Après | Action |
|-------|-------|--------|
| `database/db.py` | `core/database.py` | Déplacer + renommer |
| `database/__init__.py` | Supprimer | Pas besoin |

**Ancien `database/db.py`** → **Nouveau `core/database.py`**:
```python
"""
core/database.py - Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os
from typing import Generator

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sportpulse.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Database:
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    # ... méthodes inchangées

db = Database()

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for sessions"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
```

---

### ✨ D. RÉORGANISATION IA (ai_agent → ai)

| Avant | Après | Type |
|-------|-------|------|
| `ai_agent/__init__.py` | `ai/__init__.py` | Déplacer |
| `ai_agent/pipeline.py` | `ai/pipeline.py` | Déplacer (orchestration) |
| `ai_agent/classifier.py` | `ai/processors/classifier.py` | Déplacer (outil) |
| `ai_agent/credibility.py` | `ai/processors/credibility.py` | Déplacer (outil) |
| `ai_agent/summarizer.py` | `ai/processors/summarizer.py` | Déplacer (outil) |
| `ai_agent/collector.py` | `ai/processors/collector.py` | Déplacer (outil) |

**Nouvelle structure `ai/`**:
```python
# ai/__init__.py
from .pipeline import AIPipeline
__all__ = ["AIPipeline"]

# ai/pipeline.py (orchestration)
from .processors import Classifier, CredibilityAnalyzer, Summarizer, Collector

class AIPipeline:
    def __init__(self, ...):
        self.classifier = Classifier()
        self.credibility = CredibilityAnalyzer()
        self.summarizer = Summarizer()
        self.collector = Collector()
    
    def process_pipeline(self, ...):
        # Orchestration logic

# ai/processors/classifier.py (outil)
class Classifier:
    def classify(self, article):
        # Logic
```

---

### ✨ E. MAIN APPLICATION

| Avant | Après | Action |
|-------|-------|--------|
| `backend/main.py` | `project/main.py` | Déplacer (à la racine) |

**Nouveau `project/main.py`** (imports mises à jour):
```python
#!/usr/bin/env python3
"""
SportPulse Backend - Application principale
Architecture: Layered (API + Services + Repositories)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SportPulse API",
    description="API pour le système de veille sportive multilingue",
    version="2.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Endpoints racine
@app.get("/")
async def root():
    return {"message": "SportPulse API v2.0", "status": "running", "docs": "/api/docs"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "SportPulse API"}

# Import routers
try:
    from api.routes import articles, sources, reviews, users, ai
    
    app.include_router(articles.router)
    app.include_router(sources.router)
    app.include_router(reviews.router)
    app.include_router(users.router)
    app.include_router(ai.router)
    
    logger.info("✓ Routers loaded successfully")
except ImportError as e:
    logger.warning(f"Warning: Routers not found ({e})")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```

---

## 🔄 Update d'Imports - Stratégie

### Avant Migration:
```python
from backend.database.db import get_db
from backend.database.models import Article
from backend.schemas.schemas import ArticleResponse
from backend.controllers.article_controller import ArticleController
from backend.views import articles
from backend.ai_agent.pipeline import AIPipeline
```

### Après Migration:
```python
from core.database import get_db
from models.orm.articles import Article
from models.schemas.articles import ArticleResponse, ArticleCreate
from api.routes.articles import ArticleHandler
from api.routes import articles
from ai.pipeline import AIPipeline
```

### Pattern à appliquer:
1. ✅ `backend.database.*` → `core.database`
2. ✅ `backend.database.models` → `models.orm.*`
3. ✅ `backend.schemas.schemas` → `models.schemas.*`
4. ✅ `backend.controllers.*` → `api.routes.*`
5. ✅ `backend.views.*` → `api.routes.*`
6. ✅ `backend.ai_agent.*` → `ai.*` ou `ai.processors.*`
7. ✅ `backend.repositories.*` → `repositories.*`
8. ✅ `backend.services.*` → `services.*`

---

## 📂 Fichiers à Créer/Modifier/Supprimer

### ✅ À CRÉER (Nouveaux répertoires + files)
```
project/
├── api/
│   ├── __init__.py                  [NEW]
│   ├── dependencies.py              [NEW]
│   └── routes/
│       ├── __init__.py              [NEW]
│       ├── articles.py              [FUSION views/articles.py + controllers/article_controller.py]
│       ├── sources.py               [FUSION views/sources.py + controllers/source_controller.py]
│       ├── reviews.py               [FUSION views/reviews.py + controllers/review_controller.py]
│       ├── users.py                 [NEW from controllers/user_controller.py]
│       └── ai.py                    [NEW from controllers/ai_controller.py]
├── models/
│   ├── orm/
│   │   ├── __init__.py              [NEW]
│   │   ├── base.py                  [NEW - from database/models Base]
│   │   ├── articles.py              [NEW - from database/models Article]
│   │   ├── sources.py               [NEW - from database/models Source]
│   │   ├── reviews.py               [NEW - from database/models Review]
│   │   └── users.py                 [NEW - from database/models User]
│   └── schemas/
│       ├── __init__.py              [NEW]
│       ├── articles.py              [NEW - from schemas/schemas ArticleCreate/Response]
│       ├── sources.py               [NEW - from schemas/schemas SourceCreate/Response]
│       ├── reviews.py               [NEW - from schemas/schemas ReviewCreate/Response]
│       └── users.py                 [NEW - from schemas/schemas UserCreate/Response]
├── ai/
│   ├── __init__.py                  [MOVE from ai_agent/__init__.py]
│   ├── pipeline.py                  [MOVE from ai_agent/pipeline.py]
│   └── processors/
│       ├── __init__.py              [NEW]
│       ├── classifier.py            [MOVE from ai_agent/classifier.py]
│       ├── credibility.py           [MOVE from ai_agent/credibility.py]
│       ├── summarizer.py            [MOVE from ai_agent/summarizer.py]
│       └── collector.py             [MOVE from ai_agent/collector.py]
├── core/
│   ├── __init__.py                  [NEW]
│   ├── database.py                  [MOVE from database/db.py]
│   ├── config.py                    [OPTIONAL - new if needed]
│   └── security.py                  [OPTIONAL - new if needed]
└── __init__.py                      [NEW - project marker]
```

### 🗑️ À SUPPRIMER (Anciens répertoires complets)
```
backend/
├── views/                           [DELETE - consolidé dans api/]
├── controllers/                     [DELETE - consolidé dans api/]
├── database/                        [DELETE - config déplacé à core/]
├── schemas/                         [DELETE - split into models/schemas/]
├── ai_agent/                        [DELETE - reorganisé en ai/]
└── (garder: services/, repositories/, models/)
```

---

## 📊 Tableau Complet Fichier par Fichier

| Source (Backend) | Destination (Project) | Action | Notes |
|------------------|----------------------|--------|-------|
| `main.py` | `main.py` | MOVE | Mettre à jour imports |
| `views/articles.py` | `api/routes/articles.py` | **MERGE** + controller | Fusionner + updates imports |
| `views/sources.py` | `api/routes/sources.py` | **MERGE** + controller | Fusionner + updates imports |
| `views/reviews.py` | `api/routes/reviews.py` | **MERGE** + controller | Fusionner + updates imports |
| `controllers/user_controller.py` | `api/routes/users.py` | MOVE | Update imports |
| `controllers/ai_controller.py` | `api/routes/ai.py` | MOVE | Update imports |
| `database/db.py` | `core/database.py` | MOVE | Inchangé logique |
| `database/models.py` | `models/orm/*.py` | SPLIT | 4 fichiers (articles, sources, reviews, users) |
| `schemas/schemas.py` | `models/schemas/*.py` | SPLIT | 4 fichiers (articles, sources, reviews, users) |
| `ai_agent/pipeline.py` | `ai/pipeline.py` | MOVE | Update imports |
| `ai_agent/classifier.py` | `ai/processors/classifier.py` | MOVE | Update imports |
| `ai_agent/credibility.py` | `ai/processors/credibility.py` | MOVE | Update imports |
| `ai_agent/summarizer.py` | `ai/processors/summarizer.py` | MOVE | Update imports |
| `ai_agent/collector.py` | `ai/processors/collector.py` | MOVE | Update imports |
| `services/*.py` | `services/*.py` | COPY | 7 fichiers - Inchangés |
| `repositories/*.py` | `repositories/*.py` | COPY | 5 fichiers + base - Inchangés |
| `tests/*` | `tests/*` | REVIEW | À analyser/réorganiser |

---

## 🔐 Import Dependencies (Avant → Après)

### Services (Inchangés, mais imports mis à jour)
```python
# AVANT: from backend.database.db import get_db
# APRÈS:
from core.database import get_db
from models.orm.articles import Article
from models.schemas.articles import ArticleCreate
```

### Repositories (Inchangés, mais imports mis à jour)
```python
# AVANT: from backend.database.models import Article
# APRÈS:
from models.orm.articles import Article
from core.database import SessionLocal
```

### API Routes (Nouvelles structures)
```python
# AVANT (views/articles.py):
from ..schemas.schemas import ArticleResponse
from ..controllers.article_controller import ArticleController

# APRÈS (api/routes/articles.py):
from ..models.schemas.articles import ArticleResponse, ArticleCreate
from ..repositories.article_repository import ArticleRepository
from ..core.database import get_db
```

---

## ✅ Checklist de Vérification

**Avant ÉTAPE 3 — MIGRATION:**
- [ ] Tous les fichiers source identifiés
- [ ] Mapping old → new compris
- [ ] Consolidation views+controllers understood
- [ ] Séparation ORM vs schemas approved
- [ ] Import patterns known
- [ ] No circular dependencies expected
- [ ] Tests strategy clear

---

## 🚀 Prêt pour ÉTAPE 3 — MIGRATION?

Cette ÉTAPE 2 fournit:
1. ✅ Structure cible complète
2. ✅ Exact new file paths
3. ✅ Consolidation examples (views + controllers)
4. ✅ Séparation strategy (ORM + schemas)
5. ✅ Import migration patterns
6. ✅ File-by-file mapping table

**ÉTAPE 3 va**:
- Créer la structure project/
- Fusionner les fichiers (views + controllers)
- Diviser les modèles (ORM + schemas)
- Déplacer les fichiers
- Mettre à jour tous les imports
- Vérifier pas de circular imports

**Y a-t-il des ajustements au plan avant ÉTAPE 3?**
