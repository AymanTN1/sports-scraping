# MercatoPULSE — Dockerfile (Multi-Stage Build)
# Stage 1: Builder — installe les dépendances dans un layer isolé
FROM python:3.11-slim AS builder

WORKDIR /app

# Installer les outils de build système (pour psycopg2, lxml)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier uniquement requirements.txt pour profiter du layer caching Docker
COPY requirements.txt .

# Installer les dépendances dans un répertoire isolé
RUN pip install --upgrade pip && \
    pip install --user --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------
# Stage 2: Runner — image minimale de production (aucun tool de build)
FROM python:3.11-slim AS runner

# Utilisateur non-root pour la sécurité (principe du moindre privilège)
RUN addgroup --system mercato && adduser --system --ingroup mercato mercato

WORKDIR /app

# Copier uniquement les packages installés depuis le builder
COPY --from=builder /root/.local /home/mercato/.local

# Copier le code applicatif
COPY backend/ ./backend/
COPY src/ ./src/
COPY web/ ./web/
COPY data/ ./data/
COPY Procfile .

# Définir le PATH pour les binaires pip --user
ENV PATH=/home/mercato/.local/bin:$PATH \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Basculer vers l'utilisateur non-root
USER mercato

# Port exposé par uvicorn
EXPOSE 8000

# Health check Docker natif
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health').raise_for_status()"

# Point d'entrée de production
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
