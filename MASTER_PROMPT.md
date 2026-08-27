# 🧠 MASTER PROMPT — SportPulse (Sport Intelligence Collection)

**Generated**: April 9, 2026  
**Status**: Production-ready MVP with expanding features  
**Version**: 2.0.0 — Backend restructuring phase

---

## 1. IDENTITÉ DU PROJET

### Nom & Objectif
- **Nom complet**: SportPulse (Sport Intelligence Collection)
- **Type d'application**: Plateforme de veille sportive multilingue
- **Objectif principal**: Scraper, filtrer, organiser et classer automatiquement des articles sportifs depuis 14 sources multilingues avec évaluation de crédibilité et synthèse
- **Utilisateurs cibles**: Journalistes sportifs, analystes, fans, organisations sportives
- **Horizon**: MVP → Plateforme SaaS avec personnalisation utilisateur

### Stack Technique Complet
```
Langage:           Python 3.8+
Backend Framework: FastAPI 0.104+ (async/await)
Serveur:           Uvicorn 0.24.0
ORM:               SQLAlchemy 2.0.0+
Base Données:      SQLite (dev) / PostgreSQL (prod)
Validation:        Pydantic (implicite via FastAPI)
Authentication:    Bcrypt + JWT (partial implementation)
Parsing:           BeautifulSoup4 4.12+, lxml 4.9+
Data Processing:   Pandas 2.0+, requests 2.31+
Frontend:          HTML5 + CSS3 + Vanilla JS (http.server)
```

### Déploiement
- **Local**: `python start.py` (développement)
- **Production**: Uvicorn depuis backend/ sur port 8000
- **Frontend**: Servi via http.server sur port 3000
- **Base de données**: Fichier SQLite `sportpulse.db` (persistant)

---

## 2. ARCHITECTURE GLOBALE

### Pattern Architectural: MVC + Repository Pattern

```
┌─────────────────────────────────────────────────────────┐
│                  FRONTEND (HTTP Client)                 │
│         (index.html statique sur port 3000)             │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/REST
                         ▼
┌──────────────────────────────────────────────────────────┐
│            LAYER 1: VIEWS (Routes FastAPI)              │
│  • articles.py, sources.py, reviews.py                  │
│  • Routes HTTP avec validation Pydantic                 │
│  • Dépendances FastAPI (Depends)                        │
│  • Transforme requêtes → appels Controllers             │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│         LAYER 2: CONTROLLERS (Business Logic)           │
│  • ArticleController, SourceController, etc.            │
│  • Logique métier: filtrage, tri, validation            │
│  • Appelle Services ET Repositories                     │
│  • N'accède PAS directement à la DB (via Repo)          │
└────────────────────────┬─────────────────────────────────┘
                         │
                ┌────────┴────────┐
                ▼                 ▼
        ┌──────────────┐  ┌──────────────────┐
        │   SERVICES   │  │ REPOSITORIES     │
        └──────────────┘  │ (Data Abstraction)
                          └──────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   DATABASE Layer        │
                    │  (SQLAlchemy ORM)       │
                    │  Models: Article,       │
                    │  Source, Review, User   │
                    │  Engine: SQLite/PG      │
                    └─────────────────────────┘
```

### Couches & Responsabilités

| Couche | Fichiers | Responsabilité | Peut appeler |
|--------|----------|-----------------|-------------|
| **Views** | `views/{articles,sources,reviews}.py` | Routes HTTP, parsing query, responses | Controllers + Repositories |
| **Controllers** | `controllers/{*}_controller.py` | Logique métier, orchestration | Services + Repositories |
| **Services** | `services/{*}_service.py` | Opérations réutilisables, pas de HTTP | Services seulement (pas circulaire) |
| **Repositories** | `repositories/{*}` | Accès données abstraits (CRUD) | Database models uniquement |
| **Database** | `database/db.py, models.py` | Configuration ORM, sessions | Rien (bottom layer) |
| **Schemas** | `schemas/schemas.py` | Validation Pydantic (entrée/sortie) | Rien (pure data) |

### Flux de Requête: Détail Complet

**Exemple**: GET /api/v1/articles/credible/?min_score=0.8

```
1. CLIENT: Envoie requête HTTP
   GET /api/v1/articles/credible/?min_score=0.8

2. VIEWS LAYER (articles.py)
   @router.get("/credible/")
   async def credible_articles(min_score: float = 3.0, ...):
       controller: ArticleController = Depends(get_article_controller)
       ↓
       Valide min_score via Pydantic (automatique)
       ↓
       Appelle: controller.get_credible_articles(min_score)

3. CONTROLLER LAYER (article_controller.py)
   def get_credible_articles(self, min_score: float) -> List[Dict]:
       articles = self.article_repo.get_by_credibility(min_score)
       ↓
       Applique logique supplémentaire si nécessaire
       ↓
       Retourne articles

4. REPOSITORY LAYER (article_repository.py)
   def get_by_credibility(self, min_score: float) -> List:
       return self.db.query(Article)
             .filter(Article.credibility_score >= min_score)
             .all()
       ↓
       Récupère depuis DB

5. DATABASE LAYER (models.py)
   class Article(Base):
       __tablename__ = "articles"
       credibility_score = Column(Float, default=0.0)
       
6. SQLAlchemy ORM + Moteur:
   Traduit query en SQL:
   SELECT * FROM articles WHERE credibility_score >= 0.8
   
7. DB Moteur (SQLite):
   ┌─────────────────┐
   │  sportpulse.db        │
   │  ┌───────────┐  │
   │  │ articles  │  │
   │  └───────────┘  │
   └─────────────────┘

8. RESPONSE (de bas en haut):
   Row objects → ArticleResponse validation → JSON → HTTP 200
```

### Graphe de Dépendances

```
main.py
 └─→ views/ (articles.py, sources.py, reviews.py)
     ├─→ controllers/ (ArticleController, SourceController, ReviewController)
     │   ├─→ repositories/ (ArticleRepository, SourceRepository, ReviewRepository)
     │   │   └─→ database/models.py (ORM)
     │   │       └─→ database/db.py (SessionLocal, engine)
     │   │
     │   └─→ services/ (RankingService, CredibilityService, NLPService, etc.)
     │       └─→ (pas d'accès direct à DB - utilise servic

e logic)
     │
     ├─→ schemas/ (validation Pydantic)
     │
     └─→ database/db.py (get_db dependency)

Note: Pas de dépendance circulaire
Services ne dépendent pas de Repository/Controllers
Controllers dépendent de Services ET Repositories (OK)
```

---

## 3. MODULES ET RESPONSABILITÉS

### 3.1 LAYER 1 — VIEWS (HTTP Routes)
**Fichiers**: `backend/views/{articles.py, sources.py, reviews.py}`

| Fichier | Routes | Responsabilité |
|---------|--------|-----------------|
| `articles.py` | GET/POST /api/v1/articles<br/>GET /api/v1/articles/{id}<br/>GET /articles/recent<br/>GET /articles/credible<br/>GET /articles/source/{id}<br/>GET /articles/language/{code} | Routes HTTP pour articles. Valide query params. Injecte ArticleController et dépendances |
| `sources.py` | GET/POST /api/v1/sources<br/>GET /sources/active<br/>GET /sources/credible<br/>GET /sources/language/{code} | Routes HTTP pour sources. Validation. Injection SourceController |
| `reviews.py` | POST /api/v1/reviews<br/>GET /reviews/article/{id}<br/>GET /reviews/user/{id}<br/>GET /article/{id}/rating | Routes pour avis. Validation ReviewCreate. Injection ReviewController |

**Pattern**:
```python
# TOUJOURS utiliser Depends() pour les dépendances
def get_article_controller(db: Session = Depends(get_db)) -> ArticleController:
    from ..repositories.article_repository import ArticleRepository
    from ..services.ranking_service import RankingService
    
    article_repo = ArticleRepository(db)
    ranking_service = RankingService()
    return ArticleController(article_repo, ranking_service)

@router.get("/credible/")
async def credible_articles(..., controller: ArticleController = Depends(get_article_controller)):
    # Le controller est injecté par FastAPI
    return controller.get_credible_articles(...)
```

**Ce qu'ils font**:
- ✅ Reçoivent requêtes HTTP
- ✅ Valident paramètres (automatique via Pydantic)
- ✅ Injectent dépendances (Controller, DB session)
- ✅ Appellent Controller → récupèrent résultat
- ✅ Transforment result en response_model
- ✅ Retournent JSON

**Ce qu'ils NE FONT PAS**:
- ❌ N'accèdent PAS directement à la DB
- ❌ Ne contiennent pas de logique métier complexe
- ❌ Ne créent pas les repositories (Depends le fait)

---

### 3.2 LAYER 2 — CONTROLLERS (Business Logic)
**Fichiers**: `backend/controllers/{*}_controller.py`

| Contrôleur | Responsabilité | Appelle |
|-----------|-----------------|---------|
| `ArticleController` | Logique métier pour articles (filtrage, tri, recherche) | ArticleRepository + RankingService |
| `SourceController` | Gestion des sources (créer, mise à jour, filtrer) | SourceRepository + CredibilityService |
| `ReviewController` | Gestion des avis (création, moyenne, filtrage) | ReviewRepository + ReviewService |
| `UserController` | Gestion utilisateurs (création, mise à jour, activation) | UserService + UserRepository |
| `AIController` | **NOT YET IMPLEMENTED** | (placeholder) |

**Exemple ArticleController**:
```python
class ArticleController:
    def __init__(self, article_repo, ranking_service):
        self.article_repo = article_repo
        self.ranking_service = ranking_service
    
    def get_credible_articles(self, min_score: float = 3.0, limit: int = 50):
        """Logique: récupère articles > min_score et les classe"""
        articles = self.article_repo.get_by_credibility(min_score, limit)
        # Appliquer classement
        ranked = self.ranking_service.rank_articles(articles, criteria="date")
        return ranked
    
    def search_articles(self, query: str):
        """Logique: recherche + filtrage + tri"""
        all_articles = self.article_repo.get_all(limit=1000)
        query_lower = query.lower()
        results = [a for a in all_articles 
                  if query_lower in a.get("title", "").lower()]
        return results
```

**Responsabilités**:
- ✅ Orchestration de la logique métier
- ✅ Appel aux Services pour calculs
- ✅ Appel aux Repositories pour données
- ✅ Validation métier (min/max, plages, etc.)
- ✅ Préparation réponse (tri, filtrage)

**Interdits**:
- ❌ N'accède pas directement à self.db
- ❌ Pas de requêtes SQL
- ❌ Pas de HTTP (que des dicts/lists)

---

### 3.3 LAYER 3 — SERVICES (Reusable Business Operations)
**Fichiers**: `backend/services/{*}_service.py` (7 services)

| Service | Responsabilité | Dépendances |
|---------|-----------------|-------------|
| **ScraperService** | Web scraping de 15 sources sportives multilingues | requests, BeautifulSoup4, HEADERS const |
| **NLPService** | Nettoyage texte, extraction résumés, sentiment, keywords | Patterns regex, stopwords multilingues |
| **CredibilityService** | Scoring crédibilité sources/articles, détection spam | TRUSTED_SOURCES dict, SPAM_PATTERNS |
| **RankingService** | Classement articles (par date, crédibilité, pertinence) | Articles list, criteria |
| **AuthService** | Hash/verify passwords, JWT token generation | Bcrypt, jwt library |
| **ReviewService** | Création/Update avis, moyenne ratings | ReviewRepository |
| **UserService** | Gestion utilisateurs (CRUD), activation | UserRepository |

#### 🔍 Service Détails

**ScraperService**:
```python
SOURCES = [
    {"name": "Hesport", "url": "https://...", "lang": "ar", "selectors": {...}},
    {"name": "L'Équipe", "url": "https://...", "lang": "fr", "selectors": {...}},
    {"name": "BBC Sport", "url": "https://...", "lang": "en", "selectors": {...}},
    # ... 12 autres sources
]

class ScraperService:
    def scrape_articles(self, sources=None) -> List[Dict]:
        # Scrape multi-source
        # Utilise selectors CSS pour extraction
        # Retourne [{title, content, source, url, publish_date, language}, ...]
    
    def _extract_article(self, elem, source, selectors) -> Optional[Dict]:
        # Extrait un article HTML → dict
```
**Responsabilité**: Web scraping uniquement. Retourne dicts bruts.

**CredibilityService**:
```python
TRUSTED_SOURCES = {
    "BBC Sport": 1.0,      # 5 stars
    "L'Équipe": 1.0,
    "Hesport": 0.70,       # 3.5 stars
    "Unknown": 0.30        # 1.5 stars
}

class CredibilityService:
    def get_source_credibility(self, name: str) -> float:
        # Lookup dans TRUSTED_SOURCES
        # Retourne score 0.0-1.0
    
    def calculate_article_credibility(self, article: Dict) -> float:
        # Score pondéré: source (40%) + spam (20%) + text quality (20%) + keywords (20%)
        # Retourne 0.15-1.0
```
**Responsabilité**: Évaluer fiabilité sans accès DB.

**RankingService**:
```python
class RankingService:
    @staticmethod
    def rank_articles(articles, criteria="credibility", order="desc"):
        # Trier par credibility_score, date, ou relevance_score
        # Retourne articles triés
    
    @staticmethod
    def calculate_relevance(article, query):
        # Score pertinence: mots en titre (poids 2), contenu (0.5)
        # Retourne score float
```
**Responsabilité**: Logique de tri/ranking, indépendant de la DB.

---

### 3.4 LAYER 4 — REPOSITORIES (Data Access)
**Fichiers**: `backend/repositories/{*}.py`

| Repository | Modèle | Responsabilité |
|-----------|--------|-----------------|
| `BaseRepository[T]` | Generic | Générique pour CRUD (Create, Read, Update, Delete) |
| `ArticleRepository` | Article | Accès articles: get_by_credibility, get_recent, get_by_source, get_by_language |
| `SourceRepository` | Source | Accès sources: get_by_name, get_by_language, get_active, get_by_credibility |
| `ReviewRepository` | Review | Accès avis: get_by_article, get_by_user, get_average_rating |
| `UserRepository` | User | Accès utilisateurs: get_by_username, get_by_email, get_active |

**BaseRepository Pattern** (Generic):
```python
class BaseRepository(Generic[T]):
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model
    
    def create(self, obj: T) -> T:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
    
    def get(self, id: int) -> Optional[T]:
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    def update(self, id: int, obj: T) -> Optional[T]: ...
    
    def delete(self, id: int) -> bool: ...

# Chaque repository hérite
class ArticleRepository(BaseRepository[Article]):
    def __init__(self, db: Session):
        super().__init__(db, Article)
    
    def get_by_credibility(self, min_score: float) -> List[Article]:
        return self.db.query(Article).filter(Article.credibility_score >= min_score).all()
```

**Responsabilités**:
- ✅ Opérations CRUD
- ✅ Requêtes spécifiques (get_by_*, filter combinations)
- ✅ Transaction management (commit/rollback)

**Interdits**:
- ❌ Pas de logique métier
- ❌ Pas de filtering complexe (ça c'est Controller)
- ❌ Pas de JSON/schema conversion (ça c'est Service)

---

### 3.5 LAYER 5 — DATABASE & MODELS
**Fichiers**: `backend/database/db.py`, `database/models.py`

**db.py** (Configuration):
```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sportpulse.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Database:
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def get_session(self) -> Session:
        return SessionLocal()
    
    def create_tables(self):
        from .models import Base
        Base.metadata.create_all(bind=self.engine)

db = Database()

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency pour injection session"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
```

**models.py** (ORM Definitions):
```python
Base = declarative_base()

class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), unique=True, index=True)
    content = Column(Text)
    summary = Column(Text)
    source_id = Column(Integer, ForeignKey("sources.id"))
    url = Column(String(500), unique=True, index=True)
    image_url = Column(String(500))
    publish_date = Column(DateTime)
    scrape_date = Column(DateTime, default=datetime.utcnow)
    language = Column(String(10))
    credibility_score = Column(Float, default=0.0)
    
    source = relationship("Source", back_populates="articles")
    reviews = relationship("Review", back_populates="article")

class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(250), unique=True, index=True)
    url = Column(String(500))
    language = Column(String(10))
    credibility_score = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    articles = relationship("Article", back_populates="source")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    rating = Column(Integer)  # 1-5
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    article = relationship("Article", back_populates="reviews")
    user = relationship("User", back_populates="reviews")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviews = relationship("Review", back_populates="user")
```

**Diagramme Entité-Relation**:
```
┌─────────────┐
│   User      │
├─────────────┤
│ id (PK)     │
│ username    │
│ email       │
│ password    │
│ is_active   │
│ created_at  │
└──────┬──────┘
       │
       │ 1→Many
       │
       ▼
┌─────────────┐
│   Review    │
├─────────────┤
│ id (PK)     │
│ article_id  │◄─────┐
│ user_id (FK)│      │
│ rating      │      │ Many→1
│ comment     │      │
│ created_at  │      │
└─────────────┘      │
                     │
┌────────────────────┘
│
│ Many→1
▼
┌─────────────┐         ┌─────────────┐
│  Article    │         │   Source    │
├─────────────┤         ├─────────────┤
│ id (PK)     │         │ id (PK)     │
│ title       │         │ name        │
│ content     │         │ url         │
│ summary     │         │ language    │
│ source_id (FK)───────►│ credibility │
│ url         │  Many→1 │ is_active   │
│ language    │         └─────────────┘
│ credibility │
│ scrape_date │
└─────────────┘
```

---

### 3.6 LAYER 6 — SCHEMAS (Pydantic Validation)
**Fichier**: `backend/schemas/schemas.py`

```python
# Patterns de schema Pydantic (FastAPI utilise automatiquement)

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
    summary: Optional[str] = None
    scrape_date: datetime
    credibility_score: float
    class Config:
        from_attributes = True  # Convertir ORM models → schemas

# Similaire pour Source, Review, User
```

**Responsabilité**:
- ✅ Validation données entrante (API requests)
- ✅ Sérialisation réponse (JSON output)
- ✅ Conversion ORM → DTO pour JSON

---

## 4. MODULE IA (ai_agent/) — STATUS: PLANNED

**État Actuel**: Répertoire vide (implémentation prévue)

**Pipeline IA Planifié**:
```
Article Brut (scraped)
    ↓
1. COLLECTOR (collecteur)
    • Normalise format
    • Enrichit avec metadata
    ↓
2. CLASSIFIER (classificateur)
    • Catégorise sport
    • Dictionnaires multilingues
    ↓
3. CREDIBILITY EVALUATOR (évaluateur)
    • Score source
    • Détecte spam/fake
    ↓
4. SUMMARIZER (résumé)
    • Génère résumé IA
    ↓
Article Final (enrichi + scoré + résumé)
```

**Modules à Implémenter**:
- `pipeline.py` - Orchestration (controller)
- `collector.py` - Normalisation, enrichissement
- `classifier.py` - Classification sport + multilingue
- `credibility.py` - Score crédibilité avancé
- `summarizer.py` - Résumé IA (Claude AI?)

**Import Pattern** (futur):
```python
from backend.ai_agent.pipeline import AIPipeline

pipeline = AIPipeline(
    scraper=scraper_service,
    nlp=nlp_service,
    credibility=credibility_service,
    classifier=classifier,
    summarizer=summarizer
)

result = pipeline.process_pipeline(sources=[...])
```

---

## 5. BASE DE DONNÉES

### Schéma Complet

```sql
-- Modèle: Source (14 sources multilingues)
CREATE TABLE sources (
    id INTEGER PRIMARY KEY,
    name VARCHAR(250) UNIQUE,           -- "BBC Sport", "L'Équipe", "Hesport"
    url VARCHAR(500),                   -- "https://..."
    language VARCHAR(10),               -- "en", "fr", "ar", "es"
    credibility_score FLOAT DEFAULT 0.0,-- 0.0-1.0 (1.0 = 100% fiable)
    is_active BOOLEAN DEFAULT TRUE      -- Active/inactive
);

-- Modèle: Article (articles collectés)
CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
    title VARCHAR(500) UNIQUE,
    content TEXT,
    summary TEXT,
    source_id INTEGER FOREIGN KEY,     -- Lien vers Source
    url VARCHAR(500) UNIQUE,
    image_url VARCHAR(500),
    publish_date DATETIME,
    scrape_date DATETIME,
    language VARCHAR(10),
    credibility_score FLOAT DEFAULT 0.0 -- 0.0-1.0
);

-- Modèle: User (utilisateurs)
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(100) UNIQUE,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255),        -- Bcrypt
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME
);

-- Modèle: Review (avis utilisateurs)
CREATE TABLE reviews (
    id INTEGER PRIMARY KEY,
    article_id INTEGER FOREIGN KEY,    -- Lien vers Article
    user_id INTEGER FOREIGN KEY,       -- Lien vers User
    rating INTEGER,                     -- 1-5 stars
    comment TEXT,
    created_at DATETIME
);
```

### Relations
```
Source → Article (1 → Many)
User → Review (1 → Many)
Article → Review (1 → Many)
```

### Requêtes Fréquentes
```python
# Tous les articles crédibles (score > 0.75)
db.query(Article).filter(Article.credibility_score >= 0.75).all()

# Articles d'une source spécifique
db.query(Article).filter(Article.source_id == source_id).all()

# Articles par langue
db.query(Article).filter(Article.language == "fr").all()

# Avis d'un article
db.query(Review).filter(Review.article_id == article_id).all()

# Utilisateurs actifs
db.query(User).filter(User.is_active == True).all()
```

### Stratégie Indexation
- Indices sur: `id` (PK), `title`, `url`, `source_id`, `article_id`, `user_id`, `credibility_score`, `language`
- Permet recherche/filtrage rapides

---

## 6. API ENDPOINTS (REST)

### Endpoints Implémentés

```
GET /                          → Status check
GET /health                    → Health probe
GET /api/v1                    → API info

╔═════════════════════════════════════════════════════════════╗
║ ARTICLES — /api/v1/articles                                ║
╚═════════════════════════════════════════════════════════════╝

GET    /api/v1/articles                     ← List all
  Params: skip=0, limit=50
  Response: List[ArticleResponse]

GET    /api/v1/articles/{id}                ← Get one
  Response: ArticleResponse (404 if not found)

GET    /api/v1/articles/recent/             ← Latest articles
  Params: limit=50
  Response: List[ArticleResponse] (sorted by date DESC)

GET    /api/v1/articles/credible/           ← High credibility
  Params: min_score=3.0 (sur 5 étoiles approximativement), limit=50
  Response: List[ArticleResponse]

GET    /api/v1/articles/source/{source_id}  ← By source
  Response: List[ArticleResponse]

GET    /api/v1/articles/language/{lang}     ← By language
  Params: lang="fr", "en", "ar"
  Response: List[ArticleResponse]

╔═════════════════════════════════════════════════════════════╗
║ SOURCES — /api/v1/sources                                  ║
╚═════════════════════════════════════════════════════════════╝

GET    /api/v1/sources                      ← List all (14 sources)
  Params: skip=0, limit=100
  Response: List[SourceResponse]

GET    /api/v1/sources/active/              ← Active sources only
  Response: List[SourceResponse]

GET    /api/v1/sources/credible/            ← Trusted sources
  Params: min_score=3.0
  Response: List[SourceResponse]

GET    /api/v1/sources/{id}                 ← Get one source
  Response: SourceResponse

GET    /api/v1/sources/language/{lang}      ← Sources by language
  Response: List[SourceResponse]

POST   /api/v1/sources                      ← Create source
  Body: SourceCreate {name, url, language}
  Response: SourceResponse (201 Created)

╔═════════════════════════════════════════════════════════════╗
║ REVIEWS — /api/v1/reviews                                  ║
╚═════════════════════════════════════════════════════════════╝

POST   /api/v1/reviews                      ← Create review
  Body: ReviewCreate {article_id, user_id, rating, comment}
  Response: ReviewResponse (201 Created)

GET    /api/v1/reviews/article/{id}         ← Reviews for article
  Params: skip=0, limit=50
  Response: List[ReviewResponse]

GET    /api/v1/reviews/user/{id}            ← Reviews by user
  Params: skip=0, limit=50
  Response: List[ReviewResponse]

GET    /api/v1/reviews/article/{id}/rating  ← Average rating
  Response: {article_id, average_rating}
```

### Status Codes Standards
```
200 OK              ← Success
201 Created         ← POST success
400 Bad Request     ← Validation error (invalid params/body)
404 Not Found       ← Resource not found
500 Internal Error  ← Server error
```

### Authentification
**Status**: Implémentée partiellement
- ✅ Hash: Bcrypt (AuthService)
- ✅ JWT: Generation (AuthService.create_access_token)
- ⏳ Guard: Pas d'@ authentifiée sur endpoints (à implémenter)

---

## 6.5. ÉCARTS: Documentation vs Implémentation Réelle

### ⚠️ ENDPOINTS DOCUMENTÉS MAIS NON IMPLÉMENTÉS

| Endpoint | Status | Raison |
|----------|--------|--------|
| `/api/articles/` (root) | ❌ N'existe pas | Utilisez `/api/v1/articles/` |
| `/api/articles/categories` | ❌ Not found | À implémenter |
| `/api/articles/stats` | ❌ Not found | À implémenter |
| `/api/pipeline/run` | ❌ Not found | AI pipeline pas encore fait |
| `/api/pipeline/status/{id}` | ❌ Not found | À implémenter |
| `/api/ai/analyze` | ❌ Not found | AI controller missing |
| `/api/ai/{id}/general` | ❌ Not found | À implémenter |
| `/api/ai/{id}/summary` | ❌ Not found | À implémenter |
| `/api/reports/latest` | ❌ Not found | À implémenter |

**Ce qui EST réellement implémenté**:
- ✅ `/api/v1/articles/` (GET, list all)
- ✅ `/api/v1/articles/{id}` (GET one)
- ✅ `/api/v1/articles/recent/` (GET recent)
- ✅ `/api/v1/articles/credible/` (GET credible)
- ✅ `/api/v1/articles/source/{id}` (GET by source)
- ✅ `/api/v1/articles/language/{lang}` (GET by language)
- ✅ `/api/v1/sources/` (GET list)
- ✅ `/api/v1/sources/active/` (GET active)
- ✅ `/api/v1/sources/credible/` (GET credible)
- ✅ `/api/v1/sources/{id}` (GET one)
- ✅ `/api/v1/sources/language/{lang}` (GET by language)
- ✅ `/api/v1/reviews/` (POST create)
- ✅ `/api/v1/reviews/article/{id}` (GET reviews for article)

---

## 7. FRONTEND & INTÉGRATION

### 7.1 Architecture Frontend

**Fichier Principal**: `web/index.html` (standalone, ~500+ lignes)

**Caractéristiques**:
```
├─ HTML5 + CSS3 (modern, responsive)
├─ Vanilla JavaScript (no framework)
├─ Dark/Light theme toggle (CSS variables)
├─ Interactive dashboard avec:
│  ├─ Sidebar navigation (64px fixed left)
│  ├─ Topbar avec ticker (news feed)
│  ├─ Main content area (multi-section)
│  ├─ Charts (Chart.js library)
│  ├─ Article list/detail views
│  ├─ Filters/search
│  └─ Live statistics
└─ Portable (aucune dépendance backend obligatoire)
```

**Style Moderne** (Dark theme default):
- Colors: Fire (#FF4C00), Gold (#FFB800), Lime (#7EE080), Ice (#4EC9F7)
- Typography: "Syne" (headings), "Barlow" (body)
- Animations: Smooth transitions, ticker animation
- Responsive: Mobile-friendly (flex layout)
- Accessibility: Theme variables, semantic HTML

**Fichier Statique Servi Par**:
- Option 1: FastAPI `StaticFiles` (futur)
- Option 2: `python -m http.server` (current)
- Option 3: Nginx/Apache (production)

### 7.2 Frontend → Backend Communication

**Pattern Actuel** (aspirationnel):
```javascript
// Chaque appel frontend pourrait avoir:
try {
  const response = await fetch('/api/v1/articles/');
  if (!response.ok) throw new Error(response.statusText);
  const data = await response.json();
  // Utiliser data pour remplir le UI
} catch (error) {
  console.error('API Error:', error);
  // Fallback ou afficher erreur
}
```

**Fallback Pattern** (actuellement utilisé):
```javascript
// Si API n'existe pas, charger données locales
try {
  // 1. Essayer API
  const response = await fetch('/api/v1/articles');
  data = await response.json();
} catch {
  // 2. Fallback: charger CSV
  const response = await fetch('../../data/output/verified_articles.csv');
  data = parseCSV(await response.text());
}
```

### 7.3 Sections Frontend (Tabs/Views)

Le dashboard principal (`index.html`) contient:

```
┌─ Home (Dashboard)
│  ├─ KPI Cards (Total articles, Sources, Languages, Avg credibility)
│  ├─ Chart: Articles by Source
│  ├─ Chart: Articles by Language
│  ├─ Chart: Articles by Category (future)
│  └─ Live ticker (scrolling news)
│
├─ Articles
│  ├─ List view (table)
│  │  ├─ Columns: Title, Source, Language, Score, Date
│  │  ├─ Filter: Source, Language, Credibility
│  │  └─ Sort: Date, Score, Title
│  │
│  └─ Detail view (modal/popup)
│     ├─ Full article content
│     ├─ Source credibility
│     ├─ Image (fetched from Wikipedia)
│     ├─ AI Analysis (if available)
│     └─ User ratings (reviews)
│
├─ Sources
│  ├─ List all 14 sources
│  ├─ Source credibility scores
│  ├─ Active/Inactive toggle
│  ├─ Articles count per source
│  └─ Language filter
│
├─ Statistics
│  ├─ Articles over time
│  ├─ Source distribution
│  ├─ Language breakdown
│  ├─ Credibility distribution
│  └─ Export reports (CSV, JSON, HTML)
│
└─ Settings (future)
   ├─ API connection status
   ├─ Theme toggle
   ├─ Refresh interval
   └─ Admin tools
```

### 7.4 JavaScript API Module (Futur: `frontend/js/api.js`)

**À créer pour intégration optimale**:

```javascript
// Configuration
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';
const API_VERSION = 'v1';

// ─────────────────────────────────────────
// ARTICLES ENDPOINTS
// ─────────────────────────────────────────
async function fetchArticles(skip = 0, limit = 50, filters = {}) {
  const params = new URLSearchParams({skip, limit, ...filters});
  const response = await fetch(`${API_BASE_URL}/api/v${API_VERSION}/articles/?${params}`);
  if (!response.ok) throw new Error('Failed to fetch articles');
  return await response.json();
}

async function fetchArticle(id) {
  const response = await fetch(`${API_BASE_URL}/api/v${API_VERSION}/articles/${id}`);
  if (!response.ok) throw new Error('Article not found');
  return await response.json();
}

async function fetchRecentArticles(limit = 50) {
  const response = await fetch(`${API_BASE_URL}/api/v${API_VERSION}/articles/recent/?limit=${limit}`);
  if (!response.ok) throw new Error('Failed to fetch recent articles');
  return await response.json();
}

async function fetchCredibleArticles(minScore = 0.75, limit = 50) {
  // Note: API uses 0.0-1.0, but endpoint says min_score as parameter
  const response = await fetch(
    `${API_BASE_URL}/api/v${API_VERSION}/articles/credible/?min_score=${minScore}&limit=${limit}`
  );
  if (!response.ok) throw new Error('Failed to fetch credible articles');
  return await response.json();
}

// ─────────────────────────────────────────
// SOURCES ENDPOINTS
// ─────────────────────────────────────────
async function fetchSources(skip = 0, limit = 100) {
  const response = await fetch(
    `${API_BASE_URL}/api/v${API_VERSION}/sources/?skip=${skip}&limit=${limit}`
  );
  if (!response.ok) throw new Error('Failed to fetch sources');
  return await response.json();
}

async function fetchActiveSources() {
  const response = await fetch(`${API_BASE_URL}/api/v${API_VERSION}/sources/active/`);
  if (!response.ok) throw new Error('Failed to fetch active sources');
  return await response.json();
}

// ─────────────────────────────────────────
// REVIEWS ENDPOINTS
// ─────────────────────────────────────────
async function createReview(articleId, userId, rating, comment = '') {
  const response = await fetch(`${API_BASE_URL}/api/v${API_VERSION}/reviews/`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      article_id: articleId,
      user_id: userId,
      rating,
      comment
    })
  });
  if (!response.ok) throw new Error('Failed to create review');
  return await response.json();
}

async function fetchArticleReviews(articleId, skip = 0, limit = 50) {
  const response = await fetch(
    `${API_BASE_URL}/api/v${API_VERSION}/reviews/article/${articleId}?skip=${skip}&limit=${limit}`
  );
  if (!response.ok) throw new Error('Failed to fetch reviews');
  return await response.json();
}

// ─────────────────────────────────────────
// UTILITY
// ─────────────────────────────────────────
async function testAPiConnection() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

export {
  fetchArticles,
  fetchArticle,
  fetchRecentArticles,
  fetchCredibleArticles,
  fetchSources,
  fetchActiveSources,
  createReview,
  fetchArticleReviews,
  testAPiConnection
};
```

### 7.5 Intégration dans `index.html`

**Pattern d'utilisation** (pseudo-code):

```html
<!-- Dans index.html -->
<script type="module">
  import * as API from './frontend/js/api.js';
  
  // On page load
  document.addEventListener('DOMContentLoaded', async () => {
    // Vérifier connexion API
    const apiAvailable = await API.testAPiConnection();
    
    if (apiAvailable) {
      // Charger depuis API
      const articles = await API.fetchArticles(0, 50);
      renderArticlesList(articles);
    } else {
      // Fallback CSV
      const articles = await loadCSVData();
      renderArticlesList(articles);
    }
  });
  
  // Quand utilisateur clique sur article
  async function showArticleDetail(articleId) {
    const article = await API.fetchArticle(articleId);
    const reviews = await API.fetchArticleReviews(articleId);
    
    // Merger article + reviews
    displayModal({
      ...article,
      reviews: reviews
    });
  }
  
  // Filter/Search
  async function filterArticles(filters) {
    const articles = await API.fetchArticles(0, 50, filters);
    renderArticlesList(articles);
  }
</script>
```

### 7.6 État Actuel du Frontend

**✅ Implémenté**:
- Dashboard UI moderne (dark/light theme)
- Sidebar navigation
- Topbar avec ticker live
- Articles display (table format possible)
- Statistics/KPI cards
- Charts (via Chart.js)
- Responsive design
- Filters/Search UI elements

**❌ À Implémenter**:
- Connexion API réelle (api.js module)
- Gestion data depuis API (au lieu de CSV)
- Modal de détail article
- Formulaire création review
- Actualisation temps réel (WebSockets future)
- Admin panel (pipeline management)

### 7.7 Développement Frontend

**Pour ajouter une nouvelle fonctionnalité**:

1. **Ajouter API function** dans `frontend/js/api.js`:
   ```javascript
   async function fetchMyNewFeature() {
     const response = await fetch(`${API_BASE_URL}/api/v1/new-endpoint`);
     if (!response.ok) throw new Error('Failed');
     return await response.json();
   }
   ```

2. **Ajouter UI section** dans `index.html`:
   ```html
   <div id="my-feature-section" class="panel card">
     <!-- Contenu -->
   </div>
   ```

3. **Ajouter event listener** dans `<script>`:
   ```javascript
   document.getElementById('my-feature-btn').addEventListener('click', async () => {
     const data = await fetchMyNewFeature();
     // Afficher data dans la UI
   });
   ```

### 7.8 CORS & Security

**CORS Configuration** (à ajouter en main.py):
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Sécurité Frontend**:
- ❌ Ne PAS stocker de tokens sensibles en localStorage (future: utiliser httpOnly cookies)
- ✅ Valider données côté frontend
- ✅ Afficher erreurs à l'utilisateur
- ✅ Retry logic pour connexions instables

---

## 8. RÈGLES MÉTIER CRITIQUES

### 7.1 Système de Crédibilité

```
Score Source: 0.0-1.0 (lookup dans TRUSTED_SOURCES)
   1.0      → BBC Sport, L'Équipe, RMC Sport (5 étoiles)
   0.85-0.9 → ESPN, Sky Sports, Eurosport (4 étoiles)
   0.60-0.75→ Hesport, Kooora, Arryadia (3 étoiles)
   0.30     → Unknown sources (1 étoile)

Score Article: Pondéré
   Source credibility ............. 40%
   Anti-spam detection ............ 20%
   Text quality analysis .......... 20%
   Keyword analysis ............... 20%
   ─────────────────────────────
   TOTAL ......................... 100% = 0.15-1.0

Spam Patterns (détection):
   - "cliquez ici"
   - URLs bit.ly
   - "casino", "poker", "betting"
   - "gagnez de l'argent", "vente exclusive"
```

### 8.2 Système de Classement (Ranking)

```
Critères de tri:
  • credibility     → Score article (0.0-1.0) DESC
  • date            → publish_date DESC (articles récents d'abord)
  • relevance       → Score pertinence + query DESC

Calcul Relevance:
  • Mots en titre: poids 2
  • Mots en contenu: poids 0.5

Exemple: "football champions"
  Article 1: titre="Football Champions", score=2
  Article 2: contenu="...football champions...", score=(2*0.5)=1
  → Article 1 ranking mieux
```

### 8.3 Gestion des Avis (Reviews)

```
Rating: 1-5 stars (validation stricte)
Moyenne: (sum des ratings) / count
Commentaire: Facultatif (peut être empty string)

Règles:
  • Un utilisateur = plusieurs avis possibles (même sur même article)
  • Un avis = lié à 1 article + 1 utilisateur
  • Suppression: Soft-delete possible (future)
```

### 8.4 Web Scraping Multilingue

```
Sources: 14 sources (15 avec futures)
───────────────────────────────────
Arabes (6):
  • Hesport
  • Le360 Sport
  • Arryadia
  • Kooora
  • FilGoal
  • Yalla Kora

Français (4):
  • L'Équipe
  • RMC Sport
  • Eurosport FR
  • Sport.fr

Anglais (4):
  • BBC Sport
  • Sky Sports
  • ESPN
  • Goal.com

Sélecteurs CSS personnalisés par site:
  • articles_selector: identifie conteneurs article
  • title_selector: récupère titres
  • link_selector: récupère URLs
  • date_selector: récupère dates

Délai entre requêtes: 2 + random(0-2) sec (politeness)
Headers: User-Agent moderne + Accept-Language multilingue
```

### 7.5 Enrichissement NLP

```
Clean text:
  • Supprime caractères contrôle
  • Supprime balises HTML
  • Normalise espaces
  • Limites: 500 chars pour summary

Summary extraction:
  • Divise en phrases
  • Sélectionne top 3 phrases
  • Max 500 caractères

Stopwords:
  • Anglais: 50+ words (the, a, and, ...)
  • Français: 40+ words (le, de, un, ...)
  • Arabe: 40+ words (في, من, ...)

Keyword extraction:
  • Filtre stopwords
  • Compte fréquences
  • Retourne top 5 mots

Sentiment analysis:
  • Positive words: bow "bon", "excellent", "great"
  • Negative words: bow "mauvais", "terrible", "bad"
  • Retourne: {sentiment, polarity, confidence}
```

---

## 8. CONVENTIONS DU PROJET

### 9.1 Nommage

**Fichiers & Dossiers**:
```
Files:    snake_case
          article_controller.py ✅
          articleController.py  ❌

Folders:  snake_case (pluriel)
          /repositories/  ✅
          /repository/    ⚠️ (moins courant)
          /services/      ✅
```

**Classes**:
```
PascalCase + suffixe rôle:
  ArticleController      ← Controller
  ArticleRepository      ← Repository
  ArticleService         ← Service
  ScraperService         ← Service
  NLPService            ← Service
  CredibilityService     ← Service
```

**Fonctions/Méthodes**:
```
snake_case():
  def get_articles()
  def create_user()
  def calculate_credibility()

Routes async:
  async def list_articles()
```

**Variables**:
```
snake_case:
  article = ...
  min_score = 0.8
  is_active = True

Constants:
  UPPERCASE_WITH_UNDERSCORES:
  TRUSTED_SOURCES = {...}
  SOURCES = [...]
  HEADERS = {...}
  SPAM_PATTERNS = [...]
```

### 9.2 Imports

**Structure d'Imports** (Top→Bottom order):
```python
# 1. Standard library
import os
import sys
import logging
from typing import List, Optional, Dict
from datetime import datetime

# 2. Third party
import requests
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

# 3. Local imports
from ..database.db import get_db
from ..database.models import Article
from ..repositories.article_repository import ArticleRepository
from ..services.ranking_service import RankingService
from ..schemas.schemas import ArticleResponse
```

**Imports Relatifs** (TOUJOURS utilisés):
```python
# ✅ BON (dans views/articles.py)
from ..controllers.article_controller import ArticleController
from ..database.db import get_db

# ❌ MAUVAIS (absolu)
from backend.controllers.article_controller import ArticleController
```

### 9.3 API Response Format

**Success 200**:
```json
{
  "id": 1,
  "title": "Article Title",
  "content": "...",
  "source_id": 1,
  "url": "https://...",
  "credibility_score": 0.85,
  "scrape_date": "2026-04-09T12:00:00",
  "language": "en"
}
```

**List 200**:
```json
[
  {id:1, title: "...", ...},
  {id:2, title: "...", ...}
]
```

**Error 400**:
```json
{
  "detail": "min_score must be between 0.0 and 1.0"
}
```

**Error 404**:
```json
{
  "detail": "Article not found"
}
```

### 9.4 Error Handling

**Pattern**:
```python
# Views: HTTPException
from fastapi import HTTPException

if not article:
    raise HTTPException(status_code=404, detail="Article not found")

# Controllers: ValueError, custom exceptions
if not 1 <= rating <= 5:
    raise ValueError("Rating must be between 1 and 5")

# Services: Log + return None
try:
    result = fetch_data()
except Exception as e:
    logger.error(f"Error: {e}")
    return None

# Repositories: Log + raise
except SQLAlchemyError as e:
    self.db.rollback()
    logger.error(f"Database error: {e}")
    raise
```

### 8.5 Logging

```python
import logging

logger = logging.getLogger(__name__)

# Levels utilisés
logger.debug("Message détaillé")        # Dev only
logger.info("✅ Operation successful")  # Normal flow
logger.warning("⚠️ Non-critical issue") # Attention
logger.error("❌ Error occurred")       # Problem
```

**Exemples du projet**:
```python
logger.info(f"📰 Scraping: {source.get('name')}")
logger.warning(f"Source inconnue: {source_name}")
logger.error(f"Erreur scraping {source}: {e}")
logger.info(f"Article created: {article_id}")
```

---

## 9. CE QUI NE DOIT JAMAIS ÊTRE MODIFIÉ

### 🔒 Interfaces Publiques Stables

```python
# TOUJOURS garantir ces signatures:

# Views endpoints (routes HTTP)
@router.get("/api/v1/articles")
async def list_articles(skip: int = 0, limit: int = 50, ...):

# Controllers
class ArticleController:
    def __init__(self, article_repo, ranking_service):
    def get_articles(self, skip: int, limit: int) -> List[Dict]:
    def get_credible_articles(self, min_score: float) -> List[Dict]:

# Repositories CRUD
class BaseRepository(Generic[T]):
    def create(self, obj: T) -> T:
    def get(self, id: int) -> Optional[T]:
    def get_all(self, skip: int, limit: int) -> List[T]:
    def update(self, id: int, obj: T) -> Optional[T]:
    def delete(self, id: int) -> bool:

# Database
def get_db() -> Generator[Session, None, None]:

# ORM Models (schema JAMAIS)
class Article(Base):
    __tablename__ = "articles"
    # Champs: id, title, content, source_id, url, language, credibility_score, scrape_date

# Pydantic Schemas
class ArticleResponse(BaseModel):
    id: int
    title: str
    credibility_score: float
```

### 🔒 Contrats Entre Couches

```
Views → Controllers:
  Controllers DOIT retourner: List[Dict] ou Dict ou bool
  Controllers NE DOIT retourner: HTTP responses, JSON strings

Controllers → Services:
  Services DOIT retourner: Dict, float, str, List
  Services NE DOIT retourner: DB objects, Session

Controllers → Repositories:
  Repositories DOIT retourner: ORM objects (Article, Source, User)
  Repositories NE DOIT retourner: Dicts (utiliser schemas)

Repositories ↔ Database:
  Seules Repositories communiquent avec DB
  Controllers/Services N'accèdent PAS à db.session directement
```

### 🔒 Formats de Données Critiques

```python
# Article dict format (partout)
{
    "id": int,
    "title": str,
    "content": str,
    "summary": Optional[str],
    "source_id": int,
    "url": str,
    "image_url": Optional[str],
    "publish_date": datetime,
    "scrape_date": datetime,
    "language": str,  # "en", "fr", "ar"
    "credibility_score": float  # 0.0-1.0
}

# Credibility scores: TOUJOURS 0.0-1.0 (jamais 0-100 ou 1-5)
0.0 = no credibility
0.5 = medium credibility
1.0 = full credibility

# Language codes: ISO 2-letter
"en", "fr", "ar", "es"
NE PAS: "english", "french", etc.
```

### 🚫 Interdictions Strictes

```
❌ Imports absolus (backend.models) → Utilisez relatifs (..models)
❌ Dépendances circulaires (Service → Repository → Service)
❌ Logique métier dans Views → Doit aller dans Controllers
❌ DB queries dans Controllers → Doit aller dans Repositories
❌ HTTP operations dans Services → Services = pur métier
❌ Modification ORM models signature → Casser repositories
❌ Suppressions en DB (cascade non défini) → Foreign key risks
```

---

## 11. INSTRUCTIONS POUR CLAUDE

### Quand tu travailles sur ce projet:

✅ **TU DOIS TOUJOURS**:
- Respecter l'architecture MVC strict (Views → Controllers → Services/Repos)
- Utiliser relative imports (`from ..module`)
- Retourner Dict/List depuis Controllers, jamais ORM objects au-dehors
- Logger les opérations importantes (`logger.info()`, `logger.error()`)
- Valider inputs au niveau Controller (min/max, types, plages)
- Utiliser try/except pour opérations I/O (requests, DB)
- Évaluer credibility_score pour tout article (0.0-1.0)
- Supporter 3 langues: Anglais, Français, Arabe (à minima)
- Tester avec les données réelles des 14 sources
- Documenter les nouvelles routes (docstrings)
- Mettre à jour requirements.txt si nouvelles dépendances

✅ **TU RESPECTES**:
- Nommage PascalCase pour classes, snake_case pour fonctions
- Conventions d'imports (stdlib → 3ème party → local)
- Pydantic schemas pour tous les API responses
- SQLAlchemy ORM uniquement pour DB accès
- Principes SOLID (Single Responsibility, etc.)
- Async/await pour routes FastAPI
- Gestion erreurs via HTTPException en Views

❌ **TU NE MODIFIES PAS**:
- Signatures des interfaces publiques (risque breaking change)
- ORM model structure (schema DB)
- API endpoint paths (clients dépendent dessus)
- Base données layout
- Constants TRUSTED_SOURCES, SOURCES, SPAM_PATTERNS

❌ **TU N'AJOUTES PAS DE LOGIQUE**:
- Dans Views (c'est Views → Controller)
- Dans Repositories (c'est Repository → Service si calcul)
- Dans ORM models (c'est data layer)
- Dans Schemas Pydantic (c'est validation seulement)

⚠️ **ATTENTION PARTICULIÈRE SUR**:
- **Circular imports**: Views → Controllers ← Services → Repositories ← Models
  Solution: Double-check avant import ordre
  
- **Credibility scoring**: TOUJOURS appliquer weighted formula (40% source + 20% spam + ...)
  NE PAS: Hard-code scores
  
- **Multilingue**: Text processing DOIT supporter ar/fr/en
  Test avec articles réels de chaque langue
  
- **Scraping respectueux**: Délai 2+ sec, User-Agent proper, Accept-Language
  NE PAS: Spammer des sites
  
- **Database migrations**: Si tu modifies models, créer upgrade path
  test.py réference old paths (config.settings) = WARNING: outdated!
  
- **Performance**: Limit=50 par défaut pour listes (pas fetcher 10k articles)
  Indexer les colonnes frequently queried
  
- **Stateless Services**: NLPService, CredibilityService, RankingService
  NE DOIT PAS: Garder state entre calls
  
- **Error messages**: Utilisateurs → français préféré
  Logs → peut être anglais/français mix

---

## ⚠️ PROBLÈMES DÉTECTÉS

### 🔴 High Priority

1. **AI Pipeline Missing**: `ai_agent/` est vide
   - Pipeline orchestration promised but not implemented
   - Classifier, collector, summarizer files referenced but missing

2. **Test File Outdated**: `test.py` import from old structure
   - References `config.settings`, `models.database`, `services.classifier_service`
   - These don't exist in current architecture
   - Needs updating to new backend structure

3. **Controllers Missing**: `controllers/__init__.py` imports 5 controllers
   - But only `article_controller.py` and `user_controller.py` exist
   - Missing: `SourceController`, `ReviewController`, `AIController`
   - Likely cause: incomplete migration from old structure

4. **Repositories Incomplete**: Only 2 repositories found (source, user)
   - Missing: `ArticleRepository`, `ReviewRepository`, `article_repository` 
   - Views import ArticleRepository but it doesn't exist
   - **Will break routes when trying to create ArticleController**

5. **JWT not fully integrated**: 
   - AuthService creates tokens but no endpoint to issue them
   - No @auth guard on protected endpoints
   - Password endpoints missing

### 🟡 Medium Priority

6. **No validation on created_at fields**: Should be server-provided
   - Client shouldn't send these
   - Need to update Pydantic schemas

7. **No pagination metadata**: API returns List but no total count
   - Future improvement: include {items: [], total: 100, page: 1}

8. **Image URLs**: image_url field but no extraction logic
   - Wikipedia fetch exists in NLPService but not called

9. **No update endpoints**: Only GET/POST, no PUT/PATCH for articles
   - Review system exists but no UPDATE endpoint

### 🟢 Low Priority / Future

10. **Personalized ranking not implemented**: 
    - `RankingService.personalized_ranking()` is stub

11. **No batch operations**: Can't scrape multiple articles at once
    - Single article response model only

12. **Frontend static**: No dynamic dashboard yet
    - index.html not analyzed (possible placeholder)

---

## 📋 CHECKLIST DE VALIDATION

Avant de merger du code, vérifie:

- [ ] Architecture respecte MVC (Views → Controllers → Services/Repos)
- [ ] Imports relatifs (`from ..`)
- [ ] Logging implementé (`logger.info()`, `.error()`)
- [ ] Credibility scores 0.0-1.0
- [ ] Language codes "en"/"fr"/"ar"
- [ ] Pydantic schemas utilisées pour responses
- [ ] Error handling via HTTPException en Views
- [ ] Docstrings sur toutes nouvelles fonctions
- [ ] requirements.txt à jour
- [ ] Pas de circular imports (test: `python -m py_compile`)
- [ ] Tests passent (si applicable)
- [ ] Routes documentées

---

## 🚀 NEXT STEPS

### Priority 1: Fix Critical Issues
1. Implement missing Controllers (Source, Review, AI)
2. Implement missing Repositories (Article, Review)
3. Update test.py to new architecture

### Priority 2: Implement AI Pipeline
1. Create `ai_agent/pipeline.py` (orchestration)
2. Create processors (classifier, collector, credibility, summarizer)
3. Integrate with existing services

### Priority 3: Features
1. Complete UPDATE/PUT endpoints
2. Implement authentication guards
3. Add JWT token endpoint
4. Dashboard interactivity (frontend)

---

## 📚 Quick Reference

```
GET    /api/v1/articles                   → ArticleController.get_articles()
GET    /api/v1/articles/credible/         → ArticleController.get_credible_articles()
GET    /api/v1/sources                    → SourceController.get_sources()
GET    /api/v1/reviews/article/{id}       → ReviewController.get_article_reviews()
POST   /api/v1/reviews                    → ReviewController.create_review()

ScraperService                            → Collects from 14 sources
CredibilityService                        → Scores articles 0.0-1.0
NLPService                                → Text processing, keywords, sentiment
RankingService                            → Sorts articles by criteria

Article {id, title, content, credibility_score, source_id, language, ...}
Source {id, name, url, credibility_score, is_active}
Review {id, article_id, user_id, rating(1-5), comment}
User {id, username, email, password_hash, is_active}
```

---

**Version**: 2.0.0  
**Last Update**: April 9, 2026  
**Status**: Active Development  
**Maintainer**: SportPulse Team
