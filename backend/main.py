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

        # ── 2. Bootstrap CSV → DB si la base est vide ──
        try:
            with SessionLocal() as db:
                try:
                    result = CsvIngestionService(db).bootstrap_if_needed()
                    if result:
                        logger.info("Database bootstrapped from %s", result.source_file)
                except Exception as exc:
                    db.rollback()
                    logger.warning("Database bootstrap skipped: %s", exc)
        except Exception as exc:
            logger.warning("Database session startup skipped: %s", exc)

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
# IMAGE PROXY — Résout définitivement le blocage Wikimedia
# Le navigateur bloque les images Wikimedia cross-origin
# (OpaqueResponseBlocking / NS_BINDING_ABORTED).
# Ce proxy fetch l'image côté serveur et la renvoie au client.
# ═══════════════════════════════════════════════════════════
import hashlib as _img_hashlib
from functools import lru_cache as _lru_cache

_IMG_PROXY_HEADERS = {
    "User-Agent": "MercatoPulseApp/2.0 (https://mercatopulse.live) requests/2.31.0"
}

# Simple in-memory cache (up to 200 images, ~100MB max)
_image_cache: dict = {}
_IMAGE_CACHE_MAX = 200


@app.get("/api/v1/image-proxy")
async def image_proxy(url: str = Query(..., description="URL of the image to proxy")):
    """Proxy an external image through the server to avoid CORS/OpaqueResponseBlocking."""
    import requests as _requests

    if not url or not url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL")

    # Only allow wikimedia and thesportsdb domains for security
    allowed_domains = ["upload.wikimedia.org", "www.thesportsdb.com", "thesportsdb.com"]
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.hostname not in allowed_domains:
        raise HTTPException(status_code=403, detail="Domain not allowed")

    # Strip tracking query params from wikimedia URLs
    clean_url = url.split("?")[0] if "upload.wikimedia.org" in url else url

    # Check cache
    cache_key = _img_hashlib.md5(clean_url.encode()).hexdigest()
    if cache_key in _image_cache:
        cached = _image_cache[cache_key]
        return Response(
            content=cached["data"],
            media_type=cached["content_type"],
            headers={"Cache-Control": "public, max-age=86400", "X-Image-Proxy": "hit"},
        )

    # Fetch from origin
    try:
        r = _requests.get(clean_url, headers=_IMG_PROXY_HEADERS, timeout=8, stream=True)
        if not r.ok:
            raise HTTPException(status_code=r.status_code, detail="Upstream error")

        content_type = r.headers.get("Content-Type", "image/jpeg")
        data = r.content

        # Cache if not too large (max 2MB per image)
        if len(data) < 2 * 1024 * 1024:
            if len(_image_cache) >= _IMAGE_CACHE_MAX:
                # Evict oldest entry
                oldest_key = next(iter(_image_cache))
                del _image_cache[oldest_key]
            _image_cache[cache_key] = {"data": data, "content_type": content_type}

        return Response(
            content=data,
            media_type=content_type,
            headers={"Cache-Control": "public, max-age=86400", "X-Image-Proxy": "miss"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Image proxy error for %s: %s", clean_url[:80], e)
        raise HTTPException(status_code=502, detail="Failed to fetch image")


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
