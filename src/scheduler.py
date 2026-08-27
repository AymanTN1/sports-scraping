"""
scheduler.py — MercatoPULSE Automatic Scraping Scheduler
Exécute le pipeline de scraping directement en Python (in-process)
et importe automatiquement les résultats dans la base de données.
"""

import logging
import json
import asyncio
import os
from pathlib import Path
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import sys

# Ensure project root is in sys.path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from backend.core import settings

logger = logging.getLogger(__name__)


class ScraperScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.status = {
            "state": "idle",
            "progress": [],
            "last_run": None,
            "error": None
        }
        self.listeners = set()

    def start(self):
        if self.scheduler.running:
            return
        if self.scheduler.get_job("scrape_job"):
            return

        interval_minutes = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "30"))

        if interval_minutes > 0:
            self.scheduler.add_job(
                self.run_pipeline,
                'interval',
                minutes=interval_minutes,
                id='scrape_job'
            )
            logger.info(
                "Scheduler démarré. Scraping automatique toutes les %d minutes.",
                interval_minutes,
            )
        else:
            self.scheduler.add_job(
                self.run_pipeline,
                CronTrigger(
                    hour=settings.scheduler_hour,
                    minute=settings.scheduler_minute,
                    timezone=settings.scheduler_timezone,
                ),
                id='scrape_job'
            )
            logger.info(
                "Scheduler démarré. Scraping quotidien à %02d:%02d (%s)",
                settings.scheduler_hour,
                settings.scheduler_minute,
                settings.scheduler_timezone,
            )
        self.scheduler.start()

        # Premier scrape immédiat au démarrage (en tâche de fond)
        logger.info("🚀 Lancement du premier scrape immédiat au démarrage...")
        asyncio.ensure_future(self.run_pipeline())

    def _log(self, message: str):
        """Ajoute un message de progression et notifie les listeners SSE."""
        self.status["progress"].append(message)
        logger.info(message)
        self._notify()

    async def run_pipeline(self):
        """
        Pipeline de scraping COMPLET exécuté in-process :
        1. Scrape toutes les sources RSS
        2. Enrichit via AI Organizer (Groq + NLP local)
        3. Importe directement dans la base de données PostgreSQL/SQLite
        """
        if self.status["state"] == "running":
            logger.info("Pipeline déjà en cours, skip.")
            return

        self.status["state"] = "running"
        self.status["progress"] = []
        self.status["error"] = None
        self._notify()

        try:
            # Exécuter le pipeline dans un thread pour ne pas bloquer l'event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._run_pipeline_sync)

            self.status["state"] = "done"
            self._log("✅ Pipeline complet terminé avec succès.")

        except Exception as e:
            self.status["state"] = "error"
            self.status["error"] = str(e)
            logger.error("❌ Pipeline error: %s", e, exc_info=True)
            self._log(f"❌ Erreur pipeline: {e}")
        finally:
            self.status["last_run"] = datetime.utcnow().isoformat()
            self._notify()

    def _run_pipeline_sync(self):
        """
        Exécution synchrone du pipeline complet.
        Appelé dans un thread via run_in_executor.
        """
        import pandas as pd

        base_dir = Path(__file__).resolve().parent.parent
        output_dir = base_dir / "data" / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        # ═══════════════════════════════════════════
        # ÉTAPE 1 : Scraping de toutes les sources RSS
        # ═══════════════════════════════════════════
        self._log("🔄 ÉTAPE 1/3 : Scraping des sources RSS en cours...")
        try:
            from src.scraper import scrape_all_sources
            df_raw = scrape_all_sources()
        except Exception as e:
            self._log(f"❌ Erreur scraping: {e}")
            raise

        if df_raw is None or df_raw.empty:
            self._log("⚠️ Aucun article collecté, pipeline terminé.")
            return

        raw_count = len(df_raw)
        self._log(f"✅ {raw_count} articles bruts collectés lors de cette passe.")

        # Accumuler et fusionner avec le CSV brut existant
        raw_path = output_dir / "articles_raw.csv"
        if raw_path.exists():
            try:
                df_prev_raw = pd.read_csv(raw_path)
                df_raw_all = pd.concat([df_raw, df_prev_raw], ignore_index=True)
                df_raw_all = df_raw_all.drop_duplicates(subset=["title"]).reset_index(drop=True)
            except Exception:
                df_raw_all = df_raw
        else:
            df_raw_all = df_raw
        df_raw_all.to_csv(raw_path, index=False, encoding="utf-8-sig")

        # ═══════════════════════════════════════════
        # ÉTAPE 2 : Enrichissement AI (Groq + NLP local)
        # ═══════════════════════════════════════════
        self._log("🧠 ÉTAPE 2/3 : Enrichissement AI et classification...")
        try:
            from src.ai_organizer import process_dataset
            from src.mercato_nlp import is_football_mercato_article

            df_enriched = process_dataset(df_raw)

            # Filtre de sécurité football
            keep_mask = []
            for _, row in df_enriched.iterrows():
                t = str(row.get("title", ""))
                s = str(row.get("summary", ""))
                src = str(row.get("source", ""))
                keep_mask.append(is_football_mercato_article(t, s, source=src))
            df_enriched = df_enriched[keep_mask].reset_index(drop=True)

        except Exception as e:
            self._log(f"⚠️ Enrichissement AI échoué ({e}), utilisation des données brutes.")
            df_enriched = df_raw

        # Sauvegarder et accumuler les CSV enrichis
        organized_path = output_dir / "organized_articles.csv"
        verified_path = output_dir / "verified_articles.csv"

        if verified_path.exists():
            try:
                df_prev = pd.read_csv(verified_path)
                combined = pd.concat([df_enriched, df_prev], ignore_index=True)
                if "semantic_hash" in combined.columns:
                    combined["_dedup_key"] = combined["semantic_hash"].fillna(combined["title"])
                else:
                    combined["_dedup_key"] = combined["title"]
                df_final = combined.drop_duplicates(subset=["_dedup_key"]).drop(columns=["_dedup_key"], errors="ignore").reset_index(drop=True)
            except Exception:
                df_final = df_enriched
        else:
            df_final = df_enriched

        df_final.to_csv(organized_path, index=False, encoding="utf-8-sig")
        df_final.to_csv(verified_path, index=False, encoding="utf-8-sig")

        enriched_count = len(df_final)
        self._log(f"✅ {enriched_count} articles cumulés validés dans le catalogue.")

        # ═══════════════════════════════════════════
        # ÉTAPE 3 : Import dans la base de données
        # ═══════════════════════════════════════════
        self._log("💾 ÉTAPE 3/3 : Import dans la base de données...")
        try:
            from backend.db import SessionLocal
            from backend.services import CsvIngestionService

            with SessionLocal() as db:
                ingestion = CsvIngestionService(db)
                result = ingestion.import_csv(verified_path)
                self._log(
                    f"✅ DB mis à jour: {result.inserted_articles} nouveaux, "
                    f"{result.updated_articles} mis à jour, "
                    f"{result.total_articles} total en base."
                )
        except Exception as e:
            self._log(f"⚠️ Import DB échoué: {e}")
            logger.error("DB import error: %s", e, exc_info=True)

    def _notify(self):
        msg = json.dumps(self.status)
        for queue in list(self.listeners):
            try:
                queue.put_nowait(msg)
            except Exception:
                pass

    async def stream_progress(self):
        queue = asyncio.Queue()
        self.listeners.add(queue)
        try:
            yield json.dumps(self.status)
            while True:
                msg = await queue.get()
                yield msg
        finally:
            self.listeners.remove(queue)

scheduler_instance = ScraperScheduler()
