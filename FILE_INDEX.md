# 📑 SportPulse Project - File Index & Navigation Guide

## 🎯 Start Here

**New to the project?** → Read these files in order:
1. [README_BACKEND.md](#) - Quick overview
2. [QUICKSTART.txt](#) - Setup instructions  
3. [COMPLETION_REPORT.md](#) - What was done

---

## 📚 Documentation Files

### Main Documentation

| File | Purpose | Status |
|------|---------|--------|
| **README_BACKEND.md** | Backend overview & quick start | ✅ Ready |
| **COMPLETION_REPORT.md** | Migration completion summary | ✅ Ready |
| **MIGRATION_SUMMARY.md** | Detailed service integration | ✅ Ready |
| **MIGRATION_MAPPING.md** | src/ → backend/ mapping | ✅ Ready |
| **SERVICE_USAGE_GUIDE.py** | Code examples & patterns | ✅ Ready |
| **QUICKSTART.txt** | Copy-paste commands | ✅ Ready |

### Project Files

| File | Purpose |
|------|---------|
| **verify_migration.py** | Run verification (13/13 checks) |
| **requirements.txt** | Python dependencies |
| **start.py** | Legacy startup script |

---

## 🏗️ Backend Structure

### Services Layer (Business Logic)
```
backend/services/
├── scraper_service.py           ⭐ 15+ sources, real data
├── nlp_service.py               ⭐ Text processing + Wikipedia
├── credibility_service.py       ⭐ TRUSTED_SOURCES + scoring
├── ranking_service.py           ⭐ 5-factor ranking
├── auth_service.py
├── review_service.py
├── user_service.py
└── __init__.py
```

### AI Agent (Orchestration)
```
backend/ai_agent/
├── pipeline.py                  ⭐ 5-stage pipeline
├── classifier.py
├── collector.py
├── credibility.py
├── summarizer.py
└── __init__.py
```

### Controllers (HTTP Logic)
```
backend/controllers/
├── ai_controller.py
├── article_controller.py
├── source_controller.py
├── review_controller.py
├── user_controller.py
└── __init__.py
```

### Data Access (Repository Pattern)
```
backend/repositories/
├── base_repository.py           (Generic CRUD)
├── article_repository.py        (Article queries)
├── source_repository.py
├── review_repository.py
├── user_repository.py
└── __init__.py
```

### Database (ORM)
```
backend/database/
├── db.py                        (Config + SessionLocal)
├── models.py                    (SQLAlchemy models)
└── __init__.py
```

### API Routes (REST)
```
backend/views/
├── articles.py                  (GET /articles/...)
├── sources.py                   (GET /sources/...)
├── reviews.py                   (POST /reviews/...)
└── __init__.py
```

### Data Validation
```
backend/schemas/
├── schemas.py                   (Pydantic models)
└── __init__.py
```

### Entry Point
```
backend/
├── main.py                      (FastAPI app)
└── __init__.py
```

---

## 🔗 Service Integration Map

```
ScraperService (scraper_service.py)
  ├─ Scrapes 15+ sources
  ├─ Returns: Raw articles
  └─ Used by: AIPipeline

        ↓
        
NLPService (nlp_service.py)
  ├─ Cleans text
  ├─ Fetches Wikipedia images
  ├─ Extracts keywords
  ├─ Analyzes sentiment
  ├─ Returns: Enriched articles
  └─ Used by: AIPipeline

        ↓
        
CredibilityService (credibility_service.py)
  ├─ Scores source credibility
  ├─ Calculates article credibility
  ├─ Detects SPAM
  ├─ Returns: Verified articles
  └─ Used by: AIPipeline

        ↓
        
RankingService (ranking_service.py)
  ├─ Ranks articles (5 factors)
  ├─ Filters by multiple criteria
  ├─ Returns: Ranked articles
  └─ Used by: AIPipeline

        ↓
        
AIPipeline (pipeline.py)
  ├─ Orchestrates all services
  ├─ Handles errors
  ├─ Logs progress
  └─ Stores results → Repository

        ↓
        
ArticleRepository (article_repository.py)
  ├─ Saves to database
  └─ Queries articles

        ↓
        
Database
  ├─ SQLite (default)
  └─ PostgreSQL (production)
```

---

## 📋 File Locations

### Where to Find Things

**I want to...**

**Scrape articles**
→ `backend/services/scraper_service.py`

**Process text**
→ `backend/services/nlp_service.py`

**Check credibility**
→ `backend/services/credibility_service.py`

**Rank articles**
→ `backend/services/ranking_service.py`

**Run full pipeline**
→ `backend/ai_agent/pipeline.py`

**Build API handlers**
→ `backend/controllers/*.py`

**Create REST endpoints**
→ `backend/views/*.py`

**Query database**
→ `backend/repositories/*.py`

**Define database models**
→ `backend/database/models.py`

**Validate data**
→ `backend/schemas/schemas.py`

**Start the app**
→ `backend/main.py`

---

## 🧪 Testing & Verification

### Run Verification
```bash
cd c:\Users\ayman\sportpulse
python verify_migration.py
```

Expected output:
```
✅ Fichiers correctement migrés: 13/13
🎉 MIGRATION RÉUSSIE!
```

### Test Services Individually

**Test Scraper**
```python
from backend.services.scraper_service import ScraperService
scraper = ScraperService()
articles = scraper.scrape_articles()[:3]
```

**Test NLP**
```python
from backend.services.nlp_service import NLPService
nlp = NLPService()
keywords = nlp.extract_keywords("Messi scored a goal", language="en")
```

**Test Credibility**
```python
from backend.services.credibility_service import CredibilityService
cred = CredibilityService()
score = cred.get_source_credibility("BBC Sport")
```

**Test Pipeline**
```python
from backend.ai_agent.pipeline import AIPipeline
from backend.services import *
pipeline = AIPipeline(ScraperService(), NLPService(), CredibilityService(), RankingService())
result = pipeline.process_pipeline()
```

---

## 🚀 Quick Commands

### Setup
```bash
cd c:\Users\ayman\sportpulse
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Run Backend
```bash
cd backend
uvicorn main:app --reload
# Open: http://localhost:8000/api/docs
```

### Verify Migration
```bash
python verify_migration.py
```

### Test Specific Service
```bash
python
>>> from backend.services.scraper_service import ScraperService
>>> service = ScraperService()
>>> print(len(service.sources))  # Should print 15+
```

---

## 📊 Migration Stats

| Metric | Value |
|--------|-------|
| Services Migrated | 5/5 ✅ |
| Files Verified | 13/13 ✅ |
| Documentation Files | 6 ✅ |
| API Endpoints | 12+ ✅ |
| Languages Supported | 3 (AR/FR/EN) ✅ |
| News Sources | 15 ✅ |
| Credible Sources Scored | 30+ ✅ |

---

## 🎓 Learning Path

### Beginner
1. Read [README_BACKEND.md](#)
2. Run [QUICKSTART.txt](#) commands
3. Visit http://localhost:8000/api/docs
4. Test endpoints in browser

### Intermediate
1. Read [SERVICE_USAGE_GUIDE.py](#)
2. Test each service individually
3. Try pipeline.process_pipeline()
4. Write simple tests

### Advanced
1. Read [MIGRATION_MAPPING.md](#)
2. Study [MIGRATION_SUMMARY.md](#)
3. Review source code
4. Implement custom filters
5. Add new API endpoints

---

## 🔍 Key Classes & Methods

### ScraperService
- `scrape_articles(sources)` → List[Dict]
- `scrape_url(url)` → str (HTML)

### NLPService
- `clean_text(text)` → str
- `extract_summary(text)` → str
- `fetch_wikipedia_image(query)` → Dict
- `extract_keywords(text)` → List[str]
- `get_sentiment(text)` → Dict

### CredibilityService
- `get_source_credibility(source_name)` → float
- `calculate_article_credibility(article)` → float
- `verify_article(article)` → Dict

### RankingService
- `rank_articles(articles)` → List[Dict]
- `filter_articles(articles, filters)` → List[Dict]

### AIPipeline
- `process_pipeline(sources, filters)` → Dict

---

## 📞 Support

**Need help?** Check these files:
- **Quick Start**: [QUICKSTART.txt](#)
- **Code Examples**: [SERVICE_USAGE_GUIDE.py](#)
- **API Docs**: http://localhost:8000/api/docs
- **Troubleshooting**: [README_BACKEND.md](#)

---

## ✅ Checklist

Progress tracking:
- ✅ Backend structure created
- ✅ Services implemented
- ✅ Pipeline orchestrated
- ✅ API routes defined
- ✅ Database models created
- ✅ Validation schemas added
- ✅ Verification passed
- ✅ Documentation complete
- ⏳ Integration tests (next)
- ⏳ Frontend connection (next)
- ⏳ Production deployment (next)

---

**Last Updated**: March 19, 2024  
**Status**: ✅ READY FOR DEVELOPMENT

