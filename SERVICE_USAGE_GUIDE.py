"""
SERVICE INTEGRATION GUIDE - How Each Migrated Service Works
"""

# ============================================================================
# 1. SCRAPER SERVICE - Web scraping with 15+ sources
# ============================================================================

from backend.services.scraper_service import ScraperService

scraper = ScraperService()

# Scrape all sources (returns list of articles)
articles = scraper.scrape_articles()
# Output: [
#   {
#     "title": "Messi marque!", 
#     "url": "https://...",
#     "source": "L'Équipe",
#     "language": "fr",
#     "publish_date": "2024-03-19T10:30:00",
#     "scrape_date": "2024-03-19T11:00:00"
#   },
#   ...
# ]

# Scrape specific sources only
arabic_sources = [s for s in scraper.sources if s["lang"] == "ar"]
articles = scraper.scrape_articles(sources=arabic_sources)

# Fetch raw HTML from a URL
html = scraper.scrape_url("https://example.com/article")


# ============================================================================
# 2. NLP SERVICE - Text processing and enrichment
# ============================================================================

from backend.services.nlp_service import NLPService

nlp = NLPService()

# Clean text
dirty_text = "  Messi   a marqué!!! <script>alert('hack')</script>  "
clean = nlp.clean_text(dirty_text)
# Output: "Messi a marqué!!!"

# Extract summary
long_text = "Messi is a legendary footballer. He won many trophies. He played for PSG."
summary = nlp.extract_summary(long_text, max_sentences=2)
# Output: "Messi is a legendary footballer. He won many trophies."

# Fetch Wikipedia image
image = nlp.fetch_wikipedia_image("Lionel Messi", language="en")
# Output: {
#   "url": "https://upload.wikimedia.org/...",
#   "description": "Argentine footballer",
#   "source": "Wikipedia (en)",
#   "fetch_date": "2024-03-19T..."
# }

# Extract keywords
keywords = nlp.extract_keywords("Messi scored against Barcelona", language="en", top_n=3)
# Output: ["messi", "scored", "barcelona"]

# Sentiment analysis
sentiment = nlp.get_sentiment("This is an amazing performance!")
# Output: {
#   "sentiment": "positive",
#   "polarity": 0.8,
#   "confidence": 0.95,
#   "positive_count": 1,
#   "negative_count": 0
# }

# Complete article enrichment
article = {
    "title": "Messi marque",
    "content": "Messi a marqué 2 buts...",
    "language": "fr"
}
enriched = nlp.enrich_article(article)
# Output: article with added:
# - cleaned_title, cleaned_content
# - summary
# - keywords
# - sentiment
# - wiki_image
# - enriched_date


# ============================================================================
# 3. CREDIBILITY SERVICE - Verify sources and articles
# ============================================================================

from backend.services.credibility_service import CredibilityService

credibility = CredibilityService()

# Get source credibility score (0.0-1.0)
score = credibility.get_source_credibility("BBC Sport")
# Output: 1.0 (excellent)

score = credibility.get_source_credibility("Unknown Blog")
# Output: 0.3 (unknown)

# Calculate article credibility
article = {
    "title": "Messi scores",
    "content": "Messi scored a goal...",
    "source": "BBC Sport",
    "keywords": ["messi", "goal"]
}
cred_score = credibility.calculate_article_credibility(article)
# Output: 0.85 (good credibility)

# Complete verification
verification = credibility.verify_article(article)
# Output: {
#   "article_id": None,
#   "title": "Messi scores",
#   "source": "BBC Sport",
#   "credibility_score": 0.85,
#   "source_credibility": 1.0,
#   "verified": True,  # Because 0.85 >= 0.60
#   "trust_level": "élevé ⭐⭐⭐⭐",
#   "verification_date": "2024-03-19T..."
# }


# ============================================================================
# 4. RANKING SERVICE - Rank and filter articles
# ============================================================================

from backend.services.ranking_service import RankingService

ranking = RankingService()

# Rank articles (adds ranking_score and sorts by score)
articles = [
    {"title": "Article 1", "credibility_score": 0.9, "keywords": ["sports"]},
    {"title": "Article 2", "credibility_score": 0.5, "keywords": []},
    {"title": "Article 3", "credibility_score": 0.95, "keywords": ["football", "goals"]},
]
ranked = ranking.rank_articles(articles)
# Output: ranked by ranking_score descending

# Filter articles
filters = {
    "language": "fr",
    "source": "L'Équipe",
    "min_credibility": 0.6,
    "max_age_hours": 24,
    "verified_only": True,
    "keywords": ["messi"]
}
filtered = ranking.filter_articles(articles, filters)
# Output: List of articles matching ALL criteria


# ============================================================================
# 5. AI PIPELINE - Complete 5-stage processing
# ============================================================================

from backend.ai_agent.pipeline import AIPipeline
from backend.services.scraper_service import ScraperService
from backend.services.nlp_service import NLPService
from backend.services.credibility_service import CredibilityService
from backend.services.ranking_service import RankingService

# Initialize all services
scraper = ScraperService()
nlp = NLPService()
credibility = CredibilityService()
ranking = RankingService()

# Create pipeline
pipeline = AIPipeline(scraper, nlp, credibility, ranking)

# Stage 1: Scraping - Collect articles
# Stage 2: NLP - Enrich with keywords, summaries, sentiment
# Stage 3: Credibility - Verify and score
# Stage 4: Ranking - Sort and filter
# Stage 5: Storage - Save to database

result = pipeline.process_pipeline(filters={"language": "fr"})

# Output: {
#   "status": "completed",
#   "articles_processed": 45,
#   "articles_verified": 32,
#   "start_time": "2024-03-19T...",
#   "end_time": "2024-03-19T...",
#   "steps": {
#     "scraping": {"status": "completed", "articles_found": 150},
#     "nlp": {"status": "completed", "articles_enriched": 150},
#     "credibility": {"status": "completed", "articles_verified": 32},
#     "ranking": {"status": "completed", "articles_ranked": 32},
#     "storage": {"status": "completed", "articles_saved": 32}
#   },
#   "errors": []
# }


# ============================================================================
# 6. COMPLETE WORKFLOW EXAMPLE
# ============================================================================

"""
Real-world usage example: Process and store sports articles
"""

from backend.ai_agent.pipeline import AIPipeline
from backend.services import ScraperService, NLPService, CredibilityService, RankingService
from backend.repositories.article_repository import ArticleRepository
from backend.database.db import SessionLocal

# Initialize database session
db = SessionLocal()

# Initialize services
scraper = ScraperService()
nlp = NLPService()
credibility = CredibilityService()
ranking = RankingService()

# Create repository
repo = ArticleRepository(db)

# Create pipeline
pipeline = AIPipeline(scraper, nlp, credibility, ranking, repo)

# Define filters for French articles only
filters = {
    "language": "fr",
    "min_credibility": 0.6,  # Only credible articles
    "max_age_hours": 48,      # Only last 2 days
    "verified_only": True,    # Already verified
}

# Run the complete pipeline
print("🚀 Starting processing pipeline...")
result = pipeline.process_pipeline(filters=filters)

# Print results
print(f"\n📊 Pipeline Results:")
print(f"  Total processed: {result['articles_processed']}")
print(f"  Verified: {result['articles_verified']}")
print(f"  Status: {result['status']}")

if result['errors']:
    print(f"\n⚠️  Errors encountered:")
    for error in result['errors']:
        print(f"  - {error}")

# Clean up
db.close()


# ============================================================================
# 7. TESTING EACH SERVICE INDEPENDENTLY
# ============================================================================

"""
Unit testing pattern for services
"""

def test_scraper():
    scraper = ScraperService()
    assert len(scraper.sources) >= 15
    assert scraper.headers is not None
    
    # Test source extraction
    articles = scraper.scrape_articles(scraper.sources[:1])  # One source only
    assert isinstance(articles, list)
    if articles:
        assert "title" in articles[0]
        assert "url" in articles[0]
        assert "source" in articles[0]

def test_nlp():
    nlp = NLPService()
    
    # Test text cleaning
    dirty = "  Hello  <script>bad</script>  World  "
    clean = nlp.clean_text(dirty)
    assert "<script>" not in clean
    assert "Hello" in clean
    
    # Test summary extraction
    text = "Sentence 1. Sentence 2. Sentence 3."
    summary = nlp.extract_summary(text)
    assert len(summary) < len(text)

def test_credibility():
    cred = CredibilityService()
    
    # Test source scoring
    bbc_score = cred.get_source_credibility("BBC Sport")
    assert 0 <= bbc_score <= 1.0
    assert bbc_score > 0.9  # BBC should be highly credible
    
    # Test article scoring
    article = {"title": "Test", "content": "Test content", "source": "BBC Sport"}
    score = cred.calculate_article_credibility(article)
    assert 0 <= score <= 1.0

def test_ranking():
    rank = RankingService()
    
    # Test filtering
    articles = [
        {"title": "A", "language": "fr", "credibility_score": 0.8},
        {"title": "B", "language": "en", "credibility_score": 0.9},
    ]
    
    filtered = rank.filter_articles(articles, {"language": "fr"})
    assert len(filtered) == 1
    assert filtered[0]["title"] == "A"
    
    # Test ranking
    ranked = rank.rank_articles(articles)
    assert ranked[0]["ranking_score"] >= ranked[-1]["ranking_score"]


# ============================================================================
# 8. INTEGRATION WITH FASTAPI CONTROLLERS
# ============================================================================

"""
How services connect to HTTP endpoints via controllers
"""

# backend/controllers/ai_controller.py usage:

from backend.controllers.ai_controller import AIController
from backend.ai_agent.pipeline import AIPipeline

# Controller uses services internally
controller = AIController(pipeline, repository)

# When HTTP request comes in:
# GET /api/v1/articles/process

# Controller calls:
articles = controller.process_articles(
    language="fr",
    min_credibility=0.6
)

# Which internally calls pipeline which calls all services


# ============================================================================
# SUMMARY
# ============================================================================

"""
Services work together as:

1. HTTP Request arrives
2. View (FastAPI router) receives it
3. Controller handles business logic
4. Controller calls Pipeline
5. Pipeline orchestrates all services:
   - ScraperService → gets raw articles
   - NLPService → enriches with keywords, summaries
   - CredibilityService → verifies authenticity
   - RankingService → sorts by importance
6. Repository saves to database
7. Response returned as JSON

Each service is:
- Independent and testable
- Reusable in different contexts
- Easy to mock for testing
- Production-ready
"""

