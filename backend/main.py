#!/usr/bin/env python3
# MercatoPULSE API v3.1.0
from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response, StreamingResponse
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

base_dir = Path(__file__).resolve().parent.parent
web_dir = base_dir / "web"
data_images = base_dir / "data" / "images"
docs_reports = base_dir / "docs" / "reports"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.is_serverless:
        # ── 1. Initialisation de la base de données ──
        try:
            init_db()
            logger.info("✅ Base de données initialisée.")
        except Exception as exc:
            logger.warning("init_db startup skipped: %s", exc)

        # ── 2. Synchronisation CSV → Base de données (3400+ articles) en tâche de fond ──
        async def _async_sync_db():
            import asyncio
            await asyncio.sleep(0.5)
            try:
                with SessionLocal() as db:
                    csv_service = CsvIngestionService(db)
                    csv_path = csv_service.get_default_csv_path()
                    if csv_path:
                        logger.info("🔄 Synchronisation DB depuis %s...", csv_path.name)
                        result = csv_service.import_csv(csv_path)
                        total_in_db = csv_service.article_repository.count()
                        logger.info("✅ Database sync complete: %d insérés, %d mis à jour (Total DB: %d)",
                                    result.inserted_count, result.updated_count, total_in_db)
            except Exception as exc:
                logger.warning("Database sync error: %s", exc)

        import asyncio
        asyncio.create_task(_async_sync_db())

        # ── 3. Démarrage du scheduler automatique ──
        try:
            from src.scheduler import scheduler_instance

            scheduler_instance.start()
            logger.info("✅ Scheduler automatique démarré avec succès.")
        except ImportError as exc:
            logger.warning("Scheduler not found: %s", exc)
        except Exception as exc:
            logger.warning("⚠️ Scheduler startup skipped: %s", exc)
    else:
        logger.info("Mode serverless détecté — scheduler désactivé.")

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
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router)
app.include_router(articles_router)


@app.get("/health")
@app.get("/api/health")
@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "service": "MercatoPULSE API", "version": settings.project_version}


# ═══════════════════════════════════════════════════════════
# IMAGE PROXY HAUTE PERFORMANCE & RÉSILIENCE
# Résout les blocages CORS, OpaqueResponseBlocking (ORB),
# et les erreurs 400 Wikimedia sur les formats thumbnails.
# ═══════════════════════════════════════════════════════════
import hashlib as _img_hashlib
import re as _img_re
from urllib.parse import unquote as _unquote

_IMG_PROXY_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Referer": "https://www.google.com/",
}

# In-memory LRU cache
_image_cache: dict = {}
_IMAGE_CACHE_MAX = 500

_TRANSPARENT_GIF = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"


@app.get("/api/v1/image-proxy")
async def image_proxy(url: str = Query(..., description="URL of the image to proxy")):
    """Proxy image endpoint that fetches external photos securely with thumbnail fallback."""
    import requests as _requests

    if not url or not isinstance(url, str):
        raise HTTPException(status_code=400, detail="Invalid URL")

    # Clean and unquote URL (handle double URL-encoded parameters)
    clean_url = _unquote(url).strip()
    while "%" in clean_url and ("%2" in clean_url or "%3" in clean_url):
        clean_url = _unquote(clean_url)

    if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Invalid URL protocol")

    # Check cache
    cache_key = _img_hashlib.md5(clean_url.encode()).hexdigest()
    if cache_key in _image_cache:
        cached = _image_cache[cache_key]
        return Response(
            content=cached["data"],
            media_type=cached["content_type"],
            headers={
                "Cache-Control": "public, max-age=86400",
                "Access-Control-Allow-Origin": "*",
                "X-Image-Proxy": "hit",
            },
        )

    # Build fallback candidates (for wikimedia thumbnail errors)
    urls_to_try = [clean_url]
    if "upload.wikimedia.org" in clean_url and "/thumb/" in clean_url:
        orig_url = _img_re.sub(r"/thumb/(.+)/[^/]+$", r"/\1", clean_url)
        if orig_url != clean_url:
            urls_to_try.append(orig_url)

    for u in urls_to_try:
        try:
            r = _requests.get(u, headers=_IMG_PROXY_HEADERS, timeout=6, stream=True)
            if r.ok:
                content_type = r.headers.get("Content-Type", "image/jpeg")
                if not content_type.startswith("image/"):
                    content_type = "image/jpeg"
                data = r.content
                if len(data) > 0:
                    if len(data) < 4 * 1024 * 1024:
                        if len(_image_cache) >= _IMAGE_CACHE_MAX:
                            oldest_key = next(iter(_image_cache))
                            del _image_cache[oldest_key]
                        _image_cache[cache_key] = {"data": data, "content_type": content_type}
                    return Response(
                        content=data,
                        media_type=content_type,
                        headers={
                            "Cache-Control": "public, max-age=86400",
                            "Access-Control-Allow-Origin": "*",
                            "X-Image-Proxy": "miss",
                        },
                    )
        except Exception as e:
            logger.debug("Image proxy fetch failed for %s: %s", u[:60], e)

    # Graceful fallback: return 1x1 transparent GIF with 200 OK so UI renders monogram cleanly without 400 error
    return Response(
        content=_TRANSPARENT_GIF,
        media_type="image/gif",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
            "X-Image-Proxy": "fallback",
        },
    )


@app.api_route("/api/v1/admin/sync-db", methods=["GET", "POST"])
async def sync_database_endpoint():
    """Force re-synchronisation de la base de données depuis verified_articles.csv."""
    import traceback
    try:
        with SessionLocal() as db:
            csv_service = CsvIngestionService(db)
            csv_path = csv_service.get_default_csv_path()
            if not csv_path:
                return {"status": "error", "message": "Fichier CSV introuvable"}
            result = csv_service.import_csv(csv_path)
            total = csv_service.article_repository.count()
            return {
                "status": "success",
                "source_file": csv_path.name,
                "inserted": result.inserted_count,
                "updated": result.updated_count,
                "total_articles": total,
            }
    except Exception as e:
        logger.exception("Error during sync_database_endpoint")
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}


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

web_assets = web_dir / "assets"
if web_assets.exists():
    app.mount("/assets", StaticFiles(directory=str(web_assets)), name="assets")


@app.get("/")
async def serve_index():
    for candidate in [
        web_dir / "index.html",
        base_dir / "web" / "index.html",
        Path.cwd() / "web" / "index.html",
        Path("/var/task/web/index.html"),
    ]:
        if candidate.exists():
            try:
                content = candidate.read_text(encoding="utf-8")
                return HTMLResponse(content=content)
            except Exception:
                return FileResponse(candidate)

    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html>
        <head><title>MercatoPulse API</title></head>
        <body style="font-family:sans-serif; background:#090C15; color:#F8FAFC; padding:40px; text-align:center;">
            <h1 style="color:#00FF87;">⚽ MercatoPulse API v3.1.0</h1>
            <p>API de veille et revue de presse sportive en direct.</p>
            <p><a href="/api/docs" style="color:#00E5FF; text-decoration:none;">📄 Documentation Swagger (/api/docs)</a></p>
            <p><a href="/api/v1/articles" style="color:#00FF87; text-decoration:none;">📊 Endpoints Articles (/api/v1/articles)</a></p>
        </body>
        </html>
        """
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
