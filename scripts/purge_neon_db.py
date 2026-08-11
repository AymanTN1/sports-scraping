#!/usr/bin/env python3
"""
purge_neon_db.py — Script de purge directe de la base Neon PostgreSQL.
Supprime tous les articles non-football (Business Insider, Yahoo Finance, etc.)
et revalide tous les articles restants avec le filtre corrigé.

Usage:
    py scripts/purge_neon_db.py --db-url "postgresql://..."
    ou bien définir DATABASE_URL dans l'environnement.
"""
from __future__ import annotations

import argparse
import os
import sys

# Ajouter le répertoire racine au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("❌ psycopg2 n'est pas installé. Lancez: pip install psycopg2-binary")
    sys.exit(1)

from src.mercato_nlp import is_football_mercato_article, BLOCKED_SOURCE_DOMAINS


def get_db_url(args) -> str:
    url = getattr(args, "db_url", None) or os.environ.get("DATABASE_URL", "")
    if not url:
        print("❌ Aucune DATABASE_URL fournie.")
        print("   Usage: py scripts/purge_neon_db.py --db-url 'postgresql://user:pass@host/db'")
        print("   Ou définissez la variable d'environnement DATABASE_URL")
        sys.exit(1)
    # Neon requires sslmode=require
    if "?" not in url and "neon.tech" in url:
        url += "?sslmode=require"
    return url


def purge_non_football(db_url: str, dry_run: bool = False) -> None:
    print(f"\n🔗 Connexion à la base de données...")
    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # 1. Compter les articles actuels
    cur.execute("SELECT COUNT(*) as total FROM articles")
    total = cur.fetchone()["total"]
    print(f"📊 Articles dans la base: {total}")

    # 2. Récupérer tous les articles avec le nom de la source
    cur.execute("""
        SELECT a.id, a.title, a.summary, s.name as source
        FROM articles a
        LEFT JOIN sources s ON a.source_id = s.id
        ORDER BY a.id
    """)
    articles = cur.fetchall()

    to_delete = []
    for art in articles:
        title = art["title"] or ""
        summary = art["summary"] or ""
        source = art["source"] or ""
        
        # Vérifier si c'est un article football valide
        if not is_football_mercato_article(title, summary, source=source):
            to_delete.append(art["id"])
            print(f"  🗑️  À supprimer: [{source}] {title[:70]}")

    print(f"\n📊 Bilan:")
    print(f"   Total articles: {total}")
    print(f"   À supprimer: {len(to_delete)}")
    print(f"   À conserver: {total - len(to_delete)}")

    if dry_run:
        print("\n🔍 Mode DRY-RUN — aucune modification appliquée.")
        conn.close()
        return

    if not to_delete:
        print("\n✅ Aucun article à supprimer — base déjà propre!")
        conn.close()
        return

    confirm = input(f"\nSupprimer {len(to_delete)} articles? (oui/non): ").strip().lower()
    if confirm not in ("oui", "o", "yes", "y"):
        print("❌ Annulé.")
        conn.close()
        return

    # 3. Supprimer par batch
    batch_size = 100
    for i in range(0, len(to_delete), batch_size):
        batch = to_delete[i:i + batch_size]
        cur.execute("DELETE FROM articles WHERE id = ANY(%s)", (batch,))
    
    conn.commit()
    
    # 4. Compter les restants
    cur.execute("SELECT COUNT(*) as remaining FROM articles")
    remaining = cur.fetchone()["remaining"]
    
    print(f"\n✅ Purge terminée!")
    print(f"   Supprimés: {len(to_delete)}")
    print(f"   Restants: {remaining}")
    
    cur.close()
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Purge Neon DB non-football articles")
    parser.add_argument("--db-url", help="PostgreSQL connection URL")
    parser.add_argument("--dry-run", action="store_true", help="Preview without deleting")
    args = parser.parse_args()

    db_url = get_db_url(args)
    purge_non_football(db_url, dry_run=args.dry_run)
