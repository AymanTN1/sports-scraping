#!/usr/bin/env python3
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from backend.core import settings
from backend.db import SessionLocal, init_db
from backend.routers import articles_router, system_router
from backend.services import CsvIngestionService

try:
    from sse_starlette.sse import EventSourceResponse  # type: ignore
except ImportError:
    EventSourceResponse = None


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

base_dir = Path(__file__).parent.parent
web_dir = base_dir / "web"
data_images = base_dir / "data" / "images"
docs_reports = base_dir / "docs" / "reports"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with SessionLocal() as db:
        try:
            from backend.models import Article
            from src.mercato_nlp import is_football_mercato_article

            # Purger immédiatement tous les anciens articles hors-sujet en base
            from src.mercato_nlp import BLOCKED_SOURCE_DOMAINS, clean_text_norm
            all_articles = db.query(Article).all()
            deleted_count = 0
            for art in all_articles:
                source_name = art.source.name if art.source and hasattr(art.source, "name") else (art.source if isinstance(art.source, str) else "")
                title = art.title or ""
                summary = art.summary or ""
                # Bloquer Business Insider, Yahoo Finance, etc. + filtre NLP corrigé
                source_norm = clean_text_norm(source_name)
                source_blocked = any(blocked in source_norm for blocked in BLOCKED_SOURCE_DOMAINS) if source_norm else False
                if source_blocked or not is_football_mercato_article(title, summary, source=source_name):
                    db.delete(art)
                    deleted_count += 1
            if deleted_count > 0:
                db.commit()
                logger.info("Purged %d non-football articles from database on startup", deleted_count)

            result = CsvIngestionService(db).bootstrap_if_needed()
            if result:
                logger.info("Database bootstrapped from %s", result.source_file)
        except Exception as exc:  # pragma: no cover - defensive startup logging
            db.rollback()
            logger.warning("Database startup processing skipped: %s", exc)

    try:
        from src.scheduler import scheduler_instance

        scheduler_instance.start()
    except ImportError as exc:
        logger.warning("Scheduler not found: %s", exc)
    except Exception as exc:  # pragma: no cover - defensive startup logging
        logger.warning("Scheduler startup skipped: %s", exc)

    yield


app = FastAPI(
    title=settings.project_name,
    description="API de veille et revue de presse sportive — SportPulse",
    version=settings.project_version,
    docs_url=settings.docs_url,
    openapi_url=settings.openapi_url,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router)
app.include_router(articles_router)


@app.post("/api/v1/scrape/run")
async def run_pipeline(background_tasks: BackgroundTasks):
    from src.scheduler import scheduler_instance

    background_tasks.add_task(scheduler_instance.run_pipeline)
    return {"status": "started"}


@app.get("/api/v1/scrape/status")
async def scrape_status():
    from src.scheduler import scheduler_instance

    return scheduler_instance.status


async def _scrape_stream_events():
    from src.scheduler import scheduler_instance

    async for message in scheduler_instance.stream_progress():
        yield f"data: {message}\n\n"


@app.get("/api/v1/scrape/stream")
async def scrape_stream():
    if EventSourceResponse is not None:
        from src.scheduler import scheduler_instance

        return EventSourceResponse(scheduler_instance.stream_progress())
    return StreamingResponse(_scrape_stream_events(), media_type="text/event-stream")


@app.get("/api/v1/reports")
async def get_reports():
    if not docs_reports.exists():
        return []
    reports = [file.name for file in docs_reports.glob("index_*.html")]
    return sorted(reports, reverse=True)


@app.post("/api/v1/reports/generate")
async def generate_reports():
    from src.report_generator import generate_daily_report

    with SessionLocal() as db:
        csv_path = CsvIngestionService(db).get_default_csv_path()
    if not csv_path:
        raise HTTPException(status_code=404, detail="Aucun fichier d'articles disponible")

    result = generate_daily_report(csv_path)
    if not result:
        raise HTTPException(status_code=500, detail="Generation du rapport impossible")
    return result


if data_images.exists():
    app.mount("/images", StaticFiles(directory=str(data_images)), name="images")
if docs_reports.exists():
    app.mount("/reports", StaticFiles(directory=str(docs_reports)), name="reports")


@app.get("/")
async def serve_index():
    return FileResponse(web_dir / "index.html")


if web_dir.exists():
    app.mount("/", StaticFiles(directory=str(web_dir)), name="web")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
