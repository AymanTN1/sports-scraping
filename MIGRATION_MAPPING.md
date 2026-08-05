# 🔄 Migration Mapping: src/ → backend/

## Complete File Mapping

### 📰 Web Scraper
```
src/scraper.py (200+ lines)
    ↓↓↓
backend/services/scraper_service.py

✅ Migrated Components:
  • SOURCES array (15+ sports news sources)
  • ScraperService class
  • scrape_articles() method - Multi-source scraping
  • scrape_url() method - Individual URL fetching
  • _scrape_source() - Per-source extraction
  • _extract_article() - Article parsing
  
🌍 Languages Integrated:
  🇦🇪 Arabic (6 sources)   | 🇫🇷 French (4 sources)   | 🇬🇧 English (4 sources)
  
✨ Features:
  • Selenium + BeautifulSoup parsing
  • CSS selector-based extraction
  • User-Agent headers + timeouts
  • Multi-language support
  • Automatic URL absolutization
  • Error handling with retries
```

---

### 🧹 Data Enricher / NLP
```
src/data_enricher.py (150+ lines)
    ↓↓↓
backend/services/nlp_service.py

✅ Migrated Components:
  • clean_text() - Text sanitization
  • extract_summary() - Intelligent summarization
  • fetch_wikipedia_image() - Wikipedia API integration
  • extract_keywords() - TF-IDF keyword extraction
  • get_sentiment() - Sentiment analysis
  • enrich_article() - Complete article enrichment
  
🧪 Features:
  • 6 regex patterns for text cleaning
  • Stopwords for AR/FR/EN
  • Multi-language Wikipedia fallback
  • Sentiment scoring (positive/negative/neutral)
  • Keyword frequency analysis
  • Complete article enrichment pipeline
```

---

### ✅ Source Verification / Credibility
```
src/source_verifier.py (100+ lines)
    ↓↓↓
backend/services/credibility_service.py

✅ Migrated Components:
  • TRUSTED_SOURCES dict - 30+ sources with 1-5 star ratings
  • get_source_credibility() - Source scoring (0.0-1.0)
  • calculate_article_credibility() - Article evaluation
  • verify_article() - Complete verification
  • _detect_spam() - Spam detection
  • _analyze_text_quality() - Grammar/structure analysis
  • _analyze_keywords() - Positive/negative word analysis
  
📊 Features:
  • 5-star rating system (normalized 0.0-1.0)
  • SPAM pattern detection (8 patterns)
  • Text quality scoring
  • Keyword-based credibility boost/penalty
  • Trust level classification
  • Weighted scoring (40% source, 20% spam, 20% quality, 20% keywords)
```

---

### 📊 Filtering & Organization
```
src/filtre.py (100+ lines)
    ↓↓↓
backend/services/ranking_service.py

✅ Migrated Components:
  • rank_articles() - Multi-factor ranking
  • filter_articles() - Advanced filtering
  • _calculate_ranking_score() - Scoring logic
  • _calculate_recency_score() - Time-based scoring
  • _calculate_engagement_score() - Review-based scoring
  
🎯 Features:
  • 5-factor weighted ranking:
    - Credibility (40%)
    - Recency (20%)
    - Engagement (15%)
    - Source (15%)
    - Keywords (10%)
  • Advanced filtering:
    - By language (ar/fr/en)
    - By source
    - By credibility threshold
    - By keywords
    - By max age (hours)
    - Verified-only flag
  • Recency decay (1h→100%, 7 days→10%, older→10%)
```

---

### 🤖 AI Organization / Pipeline
```
src/ai_organizer.py (150+ lines) + src/run_pipeline.py (100+ lines)
    ↓↓↓
backend/ai_agent/pipeline.py

✅ Migrated Components:
  • AIPipeline class - Main orchestrator
  • process_pipeline() - 5-stage processing
  • Pipeline logging & monitoring
  • Error handling & reporting
  
5️⃣ Processing Stages:
  1️⃣  Scraping Stage
      Input: Source list
      Output: Raw articles
      Component: ScraperService
      
  2️⃣  NLP Enrichment Stage
      Input: Raw articles
      Output: Enriched articles (summary, keywords, sentiment, wiki image)
      Component: NLPService
      
  3️⃣  Credibility Verification Stage
      Input: Enriched articles
      Output: Verified articles (score, trust level)
      Filter: Only articles with score >= 0.6
      Component: CredibilityService
      
  4️⃣  Ranking & Filtering Stage
      Input: Verified articles
      Output: Ranked articles (sorted by ranking score)
      Apply: User filters (language, source, age, etc.)
      Component: RankingService
      
  5️⃣  Storage Stage
      Input: Ranked articles
      Output: Saved to database
      Component: ArticleRepository

📊 Result Structure:
  {
    "status": "completed",
    "articles_processed": 45,
    "articles_verified": 32,
    "steps": {
      "scraping": {"status": "completed", "articles_found": 150},
      "nlp": {"status": "completed", "articles_enriched": 150},
      "credibility": {"status": "completed", "articles_verified": 32},
      "ranking": {"status": "completed", "articles_ranked": 32},
      "storage": {"status": "completed", "articles_saved": 32}
    },
    "errors": [],
    "start_time": "2024-03-19T...",
    "end_time": "2024-03-19T..."
  }
```

---

## 📋 Comparison Table

| Feature | src/ | backend/ | Status |
|---------|------|----------|--------|
| **Scraping** | scraper.py | services/scraper_service.py | ✅ Migrated |
| **Text Processing** | data_enricher.py | services/nlp_service.py | ✅ Migrated |
| **Credibility** | source_verifier.py | services/credibility_service.py | ✅ Migrated |
| **Filtering** | filtre.py | services/ranking_service.py | ✅ Migrated |
| **Pipeline** | ai_organizer.py + run_pipeline.py | ai_agent/pipeline.py | ✅ Migrated |
| **API Endpoints** | ❌ None | backend/views/ | ✅ New |
| **Database** | CSV output | database/ + repositories/ | ✅ Enhanced |
| **ORM** | ❌ None | database/models.py | ✅ New |
| **Validation** | ❌ None | schemas/ | ✅ New |
| **Controllers** | ❌ None | controllers/ | ✅ New |

---

## 🔗 Code Flow Mapping

### Original Flow (src/)
```
User Script (CLI)
  ↓
run_pipeline.py
  ├→ scraper.py (raw articles)
  ├→ data_enricher.py (enrich)
  ├→ source_verifier.py (verify)
  ├→ filtre.py (rank & filter)
  └→ Output to CSV
```

### New Flow (backend/)
```
HTTP Request
  ↓
View (articles.py, sources.py, etc.)
  ↓
Controller (ai_controller.py)
  ↓
AIPipeline (ai_agent/pipeline.py)
  ├→ ScraperService (scraper_service.py)
  ├→ NLPService (nlp_service.py)
  ├→ CredibilityService (credibility_service.py)
  ├→ RankingService (ranking_service.py)
  └→ ArticleRepository (article_repository.py)
      ↓
    Database (SQLAlchemy models)
  ↓
Response (JSON)
```

---

## 📦 Package Structure

### Services Layer
```python
# Direct replacements from src/
from backend.services.scraper_service import ScraperService
from backend.services.nlp_service import NLPService
from backend.services.credibility_service import CredibilityService
from backend.services.ranking_service import RankingService

# Each service is a self-contained, testable component
scraper = ScraperService()
articles = scraper.scrape_articles()
```

### AI Pipeline
```python
# Orchestrator for complete processing
from backend.ai_agent.pipeline import AIPipeline

pipeline = AIPipeline(scraper, nlp, credibility, ranking, repository)
result = pipeline.process_pipeline(sources, filters)
```

### Controllers
```python
# Handle HTTP requests
from backend.controllers.ai_controller import AIController

controller = AIController(pipeline, repository)
result = controller.process_articles()
```

### Views
```python
# FastAPI routes
from backend.views import articles, sources

@router.get("/articles")
def list_articles():
    # Calls controller which calls pipeline which calls services
```

---

## ✨ Benefits of Migration

| Aspect | Before (src/) | After (backend/) |
|--------|---------------|-----------------|
| **Reusability** | Single-use scripts | Reusable services |
| **Testing** | Hard to test | Easy to test (each service independent) |
| **Scaling** | Monolithic | Microservices-ready |
| **Access** | CLI only | REST API + Python |
| **Storage** | CSV files | Database (SQLite/PostgreSQL) |
| **Validation** | Manual | Pydantic schemas |
| **Error Handling** | Basic try-except | Comprehensive logging |
| **Monitoring** | No metrics | Pipeline metrics in result |
| **Deployment** | Run as script | Production-ready app |

---

## 🔄 Migration Equivalencies

| Function | Before Location | After Location | Status |
|----------|-----------------|-----------------|--------|
| scrape_articles() | scraper.py:scrape() | services/scraper_service.py:scrape_articles() | ✅ Identical logic |
| clean_text() | data_enricher.py:clean_text() | services/nlp_service.py:clean_text() | ✅ Identical logic |
| get_credibility() | source_verifier.py:get_credibility() | services/credibility_service.py:get_source_credibility() | ✅ Identical logic |
| rank_articles() | filtre.py:rank() | services/ranking_service.py:rank_articles() | ✅ Enhanced |
| process() | ai_organizer.py:process() | ai_agent/pipeline.py:process_pipeline() | ✅ Identical logic |

---

## 📝 How to Use After Migration

### Before (src/)
```bash
# Run as standalone script
python src/run_pipeline.py

# Output: CSV files in data/output/
```

### After (backend/)
```python
# Option 1: Via REST API
curl http://localhost:8000/api/v1/articles/recent

# Option 2: Direct Python
from backend.ai_agent.pipeline import AIPipeline
from backend.services import *

pipeline = AIPipeline(...)
result = pipeline.process_pipeline()

# Option 3: Via Controllers
from backend.controllers import AIController
controller = AIController(...)
result = controller.process_articles()
```

---

## ✅ Verification

All functionality has been preserved and enhanced:

```bash
✅ 15+ sources maintained
✅ Multi-language support (AR/FR/EN)
✅ Text cleaning preserved
✅ Wikipedia integration preserved
✅ Credibility scoring preserved
✅ Ranking logic preserved
✅ Pipeline orchestration preserved
✅ Error handling improved
✅ Database persistence added ➕
✅ REST API added ➕
✅ Validation added ➕
```

