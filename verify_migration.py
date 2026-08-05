#!/usr/bin/env python3
"""
verify_migration.py - Script de vérification de la structure du projet
Vérifie que tous les modules du backend et du moteur sont présents et fonctionnels
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_file_exists(path):
    """Vérifie qu'un fichier existe"""
    return os.path.isfile(path)


def check_import(module_name):
    """Vérifie qu'un module peut être importé"""
    try:
        __import__(module_name)
        return True, "✅"
    except ImportError as e:
        return False, f"❌ ImportError: {e}"
    except Exception as e:
        return False, f"⚠️ {e}"


def main():
    """Lance les vérifications"""
    print("\n" + "=" * 70)
    print("🔍 VÉRIFICATION DE LA STRUCTURE SPORTPULSE")
    print("=" * 70 + "\n")

    base_path = os.path.dirname(os.path.abspath(__file__))

    total_checks = 0
    passed_checks = 0

    # Structure requise — vérifie les fichiers réels
    required_structure = {
        "Backend Core": [
            ("backend/__init__.py", "backend"),
            ("backend/main.py", "backend.main"),
            ("backend/core/__init__.py", "backend.core"),
            ("backend/core/config.py", "backend.core.config"),
        ],
        "Database": [
            ("backend/db/__init__.py", "backend.db"),
            ("backend/db/base.py", None),
            ("backend/db/session.py", None),
        ],
        "Models & Schemas": [
            ("backend/models/__init__.py", "backend.models"),
            ("backend/models/article.py", None),
            ("backend/models/source.py", None),
        ],
        "Repositories": [
            ("backend/repositories/__init__.py", "backend.repositories"),
        ],
        "Services": [
            ("backend/services/__init__.py", "backend.services"),
            ("backend/services/article_service.py", None),
            ("backend/services/ingestion_service.py", None),
        ],
        "API Routers": [
            ("backend/routers/__init__.py", "backend.routers"),
        ],
        "Moteur de Scraping (src/)": [
            ("src/scraper.py", "src.scraper"),
            ("src/ai_organizer.py", "src.ai_organizer"),
            ("src/source_verifier.py", None),
            ("src/report_generator.py", "src.report_generator"),
            ("src/data_enricher.py", "src.data_enricher"),
            ("src/scheduler.py", None),
            ("src/run_pipeline.py", None),
        ],
        "Frontend": [
            ("web/index.html", None),
        ],
        "Configuration": [
            ("requirements.txt", None),
            ("start.py", None),
            (".gitignore", None),
        ],
    }

    for section, files in required_structure.items():
        print(f"\n📋 {section}")
        print("-" * 70)

        for file_rel, module_name in files:
            file_path = os.path.join(base_path, file_rel)
            total_checks += 1

            if check_file_exists(file_path):
                if module_name:
                    success, msg = check_import(module_name)
                    if success:
                        print(f"  ✅ {file_rel} (import OK)")
                        passed_checks += 1
                    else:
                        print(f"  ⚠️  {file_rel} (fichier OK, {msg})")
                else:
                    print(f"  ✅ {file_rel}")
                    passed_checks += 1
            else:
                print(f"  ❌ {file_rel} — MANQUANT")

    # Résumé
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ FINAL")
    print("=" * 70)
    print(f"✅ Fichiers présents et fonctionnels: {passed_checks}/{total_checks}")

    if passed_checks == total_checks:
        print("\n🎉 STRUCTURE COMPLÈTE!")
        print("   Tous les modules du projet sont en place.")
        return 0
    else:
        print(f"\n⚠️  {total_checks - passed_checks} problème(s) détecté(s)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
