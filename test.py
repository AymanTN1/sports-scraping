#!/usr/bin/env python3
"""
Test rapide de l'application SportPulse
Vérifie que tous les composants fonctionnent
"""

import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test des imports principaux"""
    success = True

    # Backend core
    try:
        from backend.core import settings
        print(f"✅ Configuration chargée (project={settings.project_name})")
    except ImportError as e:
        print(f"❌ Configuration: {e}")
        success = False

    # Database
    try:
        from backend.db import init_db, SessionLocal, Base
        print("✅ Module base de données OK")
    except ImportError as e:
        print(f"❌ Module DB: {e}")
        success = False

    # Models
    try:
        from backend.models import Article, Source
        print("✅ Modèles (Article, Source) OK")
    except ImportError as e:
        print(f"❌ Modèles: {e}")
        success = False

    # Repositories
    try:
        from backend.repositories import ArticleRepository, SourceRepository
        print("✅ Repositories OK")
    except ImportError as e:
        print(f"❌ Repositories: {e}")
        success = False

    # Services
    try:
        from backend.services import ArticleService, CsvIngestionService
        print("✅ Services OK")
    except ImportError as e:
        print(f"❌ Services: {e}")
        success = False

    # Routers
    try:
        from backend.routers import articles_router, system_router
        print("✅ Routers API OK")
    except ImportError as e:
        print(f"❌ Routers: {e}")
        success = False

    # FastAPI app
    try:
        from backend.main import app
        print("✅ Application FastAPI OK")
    except ImportError as e:
        print(f"❌ FastAPI app: {e}")
        success = False

    # Scraper
    try:
        from src.scraper import SOURCES, scrape_source
        print(f"✅ Scraper OK ({len(SOURCES)} sources)")
    except ImportError as e:
        print(f"❌ Scraper: {e}")
        success = False

    # NLP
    try:
        from src.ai_organizer import classify_article
        print("✅ Classificateur NLP OK")
    except ImportError as e:
        print(f"❌ Classificateur NLP: {e}")
        success = False

    # Credibility
    try:
        from src.source_verifier import get_credibility
        print("✅ Vérificateur de crédibilité OK")
    except ImportError as e:
        print(f"❌ Crédibilité: {e}")
        success = False

    return success


def test_database():
    """Test de la base de données"""
    try:
        from backend.db import init_db, SessionLocal
        from backend.models import Article

        init_db()
        print("✅ Tables créées / vérifiées")

        db = SessionLocal()
        count = db.query(Article).count()
        print(f"✅ Connexion DB OK ({count} articles en base)")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Erreur base de données: {e}")
        return False


def test_scraping():
    """Test rapide du scraping (1 source)"""
    try:
        from src.scraper import SOURCES, scrape_source
        src = SOURCES[0]
        articles = scrape_source(src, retries=1)
        real = [a for a in articles if len(a.get("title", "")) > 15]
        print(f"✅ Scraping {src['name']}: {len(real)} articles réels")
        return True
    except Exception as e:
        print(f"❌ Scraping: {e}")
        return False


def main():
    """Fonction principale de test"""
    print("🧪 Test de l'application SportPulse")
    print("=" * 50)

    print("\n📦 1. Tests des imports")
    print("-" * 50)
    imports_ok = test_imports()

    print("\n💾 2. Test de la base de données")
    print("-" * 50)
    db_ok = test_database()

    print("\n🌐 3. Test de scraping rapide")
    print("-" * 50)
    scrape_ok = test_scraping()

    # Résumé
    print("\n" + "=" * 50)
    results = [
        ("Imports", imports_ok),
        ("Base de données", db_ok),
        ("Scraping", scrape_ok),
    ]
    passed = sum(1 for _, ok in results if ok)
    print(f"📊 Résultat: {passed}/{len(results)} tests passés")

    if passed == len(results):
        print("\n✅ Tous les tests sont passés!")
        print("\n🚀 Pour démarrer l'application:")
        print("   python start.py")
        print("\n📖 API Docs: http://127.0.0.1:8000/api/docs")
    else:
        print("\n⚠️ Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")


if __name__ == "__main__":
    main()