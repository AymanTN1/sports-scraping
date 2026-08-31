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

        # Premier scrape différé de 10s après le boot
        try:
            loop = asyncio.get_event_loop()
            loop.call_later(10.0, lambda: asyncio.ensure_future(self.run_pipeline()))
        except Exception:
            pass

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
        Exécution synchrone du pipeline de scraping rapide (20 sources essentielles).
        Appelé dans un thread via run_in_executor.
        """
        self._log("🔄 Lancement du scraping en direct...")
        try:
            from backend.db import SessionLocal
            from backend.services.live_scraper import run_live_scrape

            with SessionLocal() as db:
                result = run_live_scrape(db)
                self._log(
                    f"✅ Scraping terminé: {result.get('new_inserted', 0)} nouveaux transferts, "
                    f"{result.get('total_in_db', 0)} total en base."
                )
        except Exception as e:
            self._log(f"❌ Erreur scraping: {e}")
            logger.error("Live scrape error in scheduler: %s", e, exc_info=True)

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
