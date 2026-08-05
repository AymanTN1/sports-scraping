import logging
import json
import asyncio
import os
from pathlib import Path
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import sys

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
        if self.scheduler.get_job("daily_scrape"):
            return
        self.scheduler.add_job(
            self.run_pipeline,
            CronTrigger(
                hour=settings.scheduler_hour,
                minute=settings.scheduler_minute,
                timezone=settings.scheduler_timezone,
            ),
            id='daily_scrape'
        )
        self.scheduler.start()
        logger.info(
            "Scheduler started. Daily scrape at %02d:%02d (%s)",
            settings.scheduler_hour,
            settings.scheduler_minute,
            settings.scheduler_timezone,
        )

    async def run_pipeline(self):
        if self.status["state"] == "running":
            return
            
        self.status["state"] = "running"
        self.status["progress"] = []
        self.status["error"] = None
        self._notify()

        try:
            base_dir = Path(__file__).parent.parent
            script_path = base_dir / "src" / "run_pipeline.py"
            process_env = {
                **os.environ,
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUTF8": "1",
            }
            
            process = await asyncio.create_subprocess_exec(
                sys.executable, str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=base_dir,
                env=process_env,
            )

            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                decoded = line.decode('utf-8', errors='replace').strip()
                if decoded:
                    self.status["progress"].append(decoded)
                    self._notify()

            await process.wait()
            
            if process.returncode == 0:
                self.status["state"] = "done"
            else:
                self.status["state"] = "error"
                self.status["error"] = f"Pipeline failed with code {process.returncode}"
                
        except Exception as e:
            self.status["state"] = "error"
            self.status["error"] = str(e)
            logger.error(f"Pipeline error: {e}")
        finally:
            self.status["last_run"] = datetime.utcnow().isoformat()
            self._notify()

    def _notify(self):
        msg = json.dumps(self.status)
        for queue in self.listeners:
            queue.put_nowait(msg)

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
