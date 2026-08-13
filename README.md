# MercatoPULSE — Real-Time Football Transfer Intelligence Platform

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/PostgreSQL-Neon_DB-4169E1?style=for-the-badge&logo=postgresql&logoColor=white"/>
  <img src="https://img.shields.io/badge/Groq_AI-Llama_3.3_70B-F55036?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/Terraform-IaC-7B42BC?style=for-the-badge&logo=terraform&logoColor=white"/>
  <img src="https://img.shields.io/badge/SonarQube-Quality_Gate-4E9BCD?style=for-the-badge&logo=sonarqube&logoColor=white"/>
  <img src="https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge"/>
</p>

<p align="center">
  <b>Collecte · Analyse · Déduplication · Distribution — 45+ sources football mondiales en temps réel</b>
</p>

---

## 📌 Vue d'Ensemble

**MercatoPULSE** est une plateforme full-stack de surveillance et d'intelligence mercato football. Le système agrège **45+ sources spécialisées** (*Sky Sports, L'Équipe, Marca, BBC Sport, Foot Mercato, Fabrizio Romano feeds...*) en **4 langues** (FR, EN, ES, IT), déduplique sémantiquement les rumeurs redondantes grâce à un pipeline IA, et distribue les données enrichies via une API REST haute-performance et un dashboard web interactif.

---

## 1️⃣ Architecture Globale du Système

```mermaid
graph TB
    subgraph CLIENTS["👥 Clients"]
        BROWSER["🖥️ Browser / Dashboard\nInterface Web Terminal"]
        MOBILE["📱 Mobile / Intégrations\nConsommateurs API"]
    end

    subgraph EDGE["🌐 Couche Réseau (Edge)"]
        CF["☁️ Cloudflare\nDDoS Protection · WAF · CDN"]
        NGINX["⚙️ NGINX Reverse Proxy\nLoad Balancing · Rate Limiting · TLS Termination"]
        CF --> NGINX
    end

    subgraph APP["⚡ Couche Application (Render Cloud)"]
        API["🔌 FastAPI (Uvicorn)\nAsync REST API + SSE"]
        SCHED["⏰ APScheduler\nPipeline Cron (toutes les 15 min)"]
        PIPELINE["🔄 Pipeline Scraping + IA\nOrchestration Multi-Étapes"]
    end

    subgraph INTELLIGENCE["🧠 Couche Intelligence & NLP"]
        GROQ["🤖 Groq API\nLlama 3.3 70B (LLM)"]
        NLP["📖 Moteur NLP Local\nRègles, Regex, Dictionnaires"]
        DEDUP["🔄 Déduplicateur Sémantique\nSemantic Hash + Merge"]
        PHOTO["🖼️ Photo Asset Resolver\nWikimedia + TheSportsDB"]

        GROQ -- "Fallback si quota/erreur" --> NLP
    end

    subgraph SCRAPING["🕷️ Couche Scraping"]
        RSS["📡 RSS/XML Scraper\n45+ Flux Multi-Langues"]
        FILTER["🛡️ Filtre NLP\nÉlimination Hors-Sujet"]
        RSS --> FILTER
    end

    subgraph DATA["🗄️ Couche Persistance"]
        PG[("🐘 Neon PostgreSQL\nArticles · Sources · Hashes")]
        REDIS[("⚡ Redis (Cache)\nAPI Response Cache · Session Store")]
        S3["☁️ Object Storage (S3-Compatible)\nPhotos Joueurs · Assets Statiques"]
    end

    CLIENTS --> CF
    NGINX --> API
    API --> PG
    API --> REDIS
    SCHED --> PIPELINE
    PIPELINE --> SCRAPING
    FILTER --> GROQ
    GROQ --> DEDUP
    NLP --> DEDUP
    DEDUP --> PHOTO
    PHOTO --> S3
    DEDUP --> PG

    style CLIENTS fill:#0f172a,stroke:#38bdf8,color:#e2e8f0
    style EDGE fill:#1e1b4b,stroke:#818cf8,color:#e2e8f0
    style APP fill:#052e16,stroke:#4ade80,color:#e2e8f0
    style INTELLIGENCE fill:#431407,stroke:#fb923c,color:#e2e8f0
    style SCRAPING fill:#1c1917,stroke:#a8a29e,color:#e2e8f0
    style DATA fill:#0c4a6e,stroke:#38bdf8,color:#e2e8f0
```

---

## 2️⃣ Pipeline de Données IA — Flux Détaillé

```mermaid
sequenceDiagram
    participant CRON as ⏰ APScheduler
    participant SCRAPER as 🕷️ Scraper RSS
    participant FILTER as 🛡️ NLP Filter
    participant GROQ as 🤖 Groq LLM
    participant NLP as 📖 Local NLP
    participant DEDUP as 🔄 Deduplicator
    participant PHOTO as 🖼️ Photo Resolver
    participant DB as 🐘 Neon PostgreSQL

    CRON->>SCRAPER: Déclenche le pipeline (toutes les 15 min)
    SCRAPER->>SCRAPER: Collecte 45+ flux RSS (FR/EN/ES/IT)
    SCRAPER->>FILTER: Résultats bruts (~300-500 articles)
    FILTER->>FILTER: Filtre NLP (mots-clés mercato, domaines bloqués)
    Note over FILTER: Élimine les articles hors football (0€ de coût)
    FILTER->>GROQ: Articles candidats (~150-200 articles)

    alt Groq API Disponible
        GROQ->>GROQ: Analyse structurée JSON par article
        Note over GROQ: Extrait: joueur, clubs, montant, ligue,\nstatut, crédibilité, résumé Fabrizio Romano
        GROQ-->>DEDUP: Résultats enrichis + semantic_hash
    else Rate Limit / Erreur / Pas de clé
        GROQ-->>NLP: Fallback automatique
        NLP->>NLP: Extraction par regex + dictionnaires
        NLP-->>DEDUP: Résultats locaux
    end

    DEDUP->>DEDUP: Normalise les hashes (joueur__from__to)
    DEDUP->>DEDUP: Fusionne les doublons inter-sources
    DEDUP->>PHOTO: Articles uniques enrichis
    PHOTO->>PHOTO: Résout portrait HD (Wikimedia PageImages)
    PHOTO->>PHOTO: Résout badge de club (TheSportsDB)
    PHOTO-->>DB: Articles finaux avec assets visuels
    DB-->>CRON: Pipeline terminé (stats & durée)
```

---

## 3️⃣ Architecture Base de Données (ERD)

```mermaid
erDiagram
    SOURCES {
        int id PK
        string name
        string language
        float credibility_score
        string base_url
        bool active
        datetime created_at
        datetime updated_at
    }

    ARTICLES {
        int id PK
        string external_key UK
        text title
        text url
        string raw_date
        datetime published_at
        string language
        string category
        string league
        string sentiment
        string player_name
        string from_club
        string to_club
        text transfer_fee
        float fee_numeric
        string status
        text summary
        text image_url
        text image_caption
        float credibility_score
        string semantic_hash
        int source_id FK
        datetime created_at
        datetime updated_at
    }

    SOURCES ||--o{ ARTICLES : "a publié"
```

---

## 4️⃣ CI/CD Pipeline & DevSecOps

```mermaid
flowchart LR
    subgraph DEV["💻 Developer Workflow"]
        CODE["Code Push\n(Git Branch)"]
        PR["Pull Request\n(Code Review)"]
    end

    subgraph SAST["🔐 Static Analysis (DevSecOps)"]
        BANDIT["🐍 Bandit\nSecurity SAST (Python)"]
        SECRETS["🔑 Gitleaks\nSecret Detection"]
        SQ["📊 SonarQube\nCode Quality Gate\nCoverage · Duplications · Bugs"]
    end

    subgraph TESTS["🧪 Test Suite"]
        UNIT["✅ pytest Unit Tests\nModels · Services · NLP Engine"]
        INT["🔗 pytest Integration Tests\nAPI Endpoints · DB Queries"]
        COV["📈 Coverage Report\n(Codecov)"]
    end

    subgraph BUILD["📦 Build & Package"]
        DOCKER_BUILD["🐳 Docker Build\nMulti-stage Dockerfile"]
        DOCKER_PUSH["📤 Docker Push\nGHCR / Docker Hub"]
    end

    subgraph IaC["🏗️ Infrastructure as Code"]
        TERRAFORM["🟣 Terraform\nProvision Neon DB · Render Service\n· Cloudflare DNS · Redis"]
        PLAN["📋 terraform plan\n(PR Preview)"]
        APPLY["⚙️ terraform apply\n(CD Merge)"]
        TERRAFORM --> PLAN --> APPLY
    end

    subgraph DEPLOY["🚀 Deployment (Render)"]
        STAGING["🟡 Staging Environment\nPreview Deploy"]
        PROD["🟢 Production Environment\nmercatopulse-api.onrender.com"]
        SMOKE["🔍 Smoke Tests\n/api/v1/health Check"]
        STAGING --> SMOKE --> PROD
    end

    subgraph MONITOR["📡 Monitoring & Observability"]
        LOGS["📋 Structured Logging\n(JSON + Render Logs)"]
        METRICS["📊 Metrics & Uptime\n(UptimeRobot / Grafana)"]
        ALERTS["🚨 Alerting\n(PagerDuty / Slack Webhook)"]
        LOGS --> METRICS --> ALERTS
    end

    CODE --> PR
    PR --> SECRETS
    PR --> BANDIT
    PR --> SQ
    SECRETS & BANDIT & SQ --> UNIT
    UNIT --> INT --> COV
    COV --> DOCKER_BUILD --> DOCKER_PUSH
    DOCKER_PUSH --> STAGING
    DOCKER_PUSH --> APPLY
    PROD --> MONITOR

    style DEV fill:#0f172a,stroke:#38bdf8,color:#e2e8f0
    style SAST fill:#450a0a,stroke:#f87171,color:#e2e8f0
    style TESTS fill:#052e16,stroke:#4ade80,color:#e2e8f0
    style BUILD fill:#1e3a5f,stroke:#60a5fa,color:#e2e8f0
    style IaC fill:#3b0764,stroke:#a78bfa,color:#e2e8f0
    style DEPLOY fill:#14532d,stroke:#86efac,color:#e2e8f0
    style MONITOR fill:#451a03,stroke:#fbbf24,color:#e2e8f0
```

---

## 5️⃣ Architecture Microservices & Backend (Clean Architecture)

```mermaid
graph TB
    subgraph ENTRYPOINTS["🌐 Entry Points"]
        HTTP["HTTP REST\n/api/v1/*"]
        SSE["SSE Stream\n/api/v1/pipeline/stream"]
        CRON_JOB["Background Job\nAPScheduler"]
    end

    subgraph API_LAYER["📡 API Layer (FastAPI Routers)"]
        AR["Articles Router\n/articles GET · POST · DELETE"]
        SR["System Router\n/health · /stats"]
    end

    subgraph SERVICE_LAYER["💼 Service Layer"]
        AS["ArticleService\nlist · get · filter · stats"]
        IS["CsvIngestionService\nimport_csv · bootstrap"]
        PS["PipelineService\ntrigger · status · purge"]
    end

    subgraph REPO_LAYER["🗃️ Repository Layer"]
        AR2["ArticleRepository\nCRUD + Complex Queries"]
        SR2["SourceRepository\nlist_all · count"]
    end

    subgraph DOMAIN["🧩 Domain Models (SQLAlchemy ORM)"]
        ART["Article\nid · title · status · semantic_hash · fee_numeric..."]
        SRC["Source\nid · name · language · credibility_score"]
    end

    subgraph INFRA["⚙️ Infrastructure Adapters"]
        ORM["SQLAlchemy 2.0 Session\nPydantic v2 Schemas"]
        MIGRATE["Auto-Migration DDL\nALTER TABLE IF NOT EXISTS"]
        CACHE["Redis Cache Layer\nResponse Caching · Rate Limit Store"]
    end

    HTTP & SSE & CRON_JOB --> API_LAYER
    AR & SR --> SERVICE_LAYER
    AS & IS & PS --> REPO_LAYER
    AR2 & SR2 --> DOMAIN
    DOMAIN --> INFRA

    style ENTRYPOINTS fill:#0c4a6e,stroke:#38bdf8,color:#e2e8f0
    style API_LAYER fill:#0f172a,stroke:#818cf8,color:#e2e8f0
    style SERVICE_LAYER fill:#052e16,stroke:#4ade80,color:#e2e8f0
    style REPO_LAYER fill:#1c1917,stroke:#a8a29e,color:#e2e8f0
    style DOMAIN fill:#431407,stroke:#fb923c,color:#e2e8f0
    style INFRA fill:#1e1b4b,stroke:#818cf8,color:#e2e8f0
```

---

## 6️⃣ Infrastructure as Code — Terraform

```mermaid
graph LR
    subgraph TERRAFORM_STATE["📁 Terraform State"]
        BACKEND_TF["Remote Backend\n(S3 + DynamoDB Lock)"]
    end

    subgraph MODULES["📦 Terraform Modules"]
        MOD_DB["module: neon_database\nPostgreSQL Instance\nConnection String"]
        MOD_RENDER["module: render_service\nDocker Deploy Config\nEnv Variables · Autoscaling"]
        MOD_CF["module: cloudflare_dns\nDNS Records · WAF Rules\nPage Rules · SSL Mode Full"]
        MOD_REDIS["module: upstash_redis\nServerless Cache\nGEO Replication"]
    end

    subgraph ENVS["🌿 Environments"]
        ENV_STAGING["staging.tfvars\nSingle Instance\nDev DB"]
        ENV_PROD["production.tfvars\nMulti-Instance\nNeon DB Prod"]
    end

    BACKEND_TF --> MOD_DB & MOD_RENDER & MOD_CF & MOD_REDIS
    ENV_STAGING & ENV_PROD --> TERRAFORM_STATE
```

---

## 7️⃣ Sécurité & Conformité (DevSecOps)

```mermaid
graph TD
    subgraph CODE_SECURITY["🔐 Code Security (SAST/SCA)"]
        BANDIT2["Bandit\nAnalyse de vulnérabilités Python"]
        DEPS["pip-audit / Safety\nDépendances CVE Check"]
        SECRETS2["Gitleaks\nDétection de secrets dans le code"]
    end

    subgraph INFRA_SECURITY["🛡️ Infrastructure Security"]
        WAF["Cloudflare WAF\nOWASP Top 10 Rule Sets"]
        RATELIMIT["NGINX Rate Limiting\nIP Throttling · Bot Detection"]
        TLS["TLS 1.3 Strict\nHSTS · OCSP Stapling"]
        ENV_VAULT["Secrets Management\nRender Env Vars (Encrypted at rest)"]
    end

    subgraph RUNTIME_SECURITY["🔒 Runtime Security"]
        JWT["JWT / API Key Auth\nBearer Token Validation"]
        CORS["CORS Policy\nAllowList Origins Only"]
        SQLI["SQLAlchemy Parameterized Queries\nSQL Injection Prevention"]
        SANITIZE["Input Sanitization\nPydantic Validators + Regex Escaping"]
    end

    subgraph MONITORING_SEC["👁️ Security Monitoring"]
        AUDIT["Audit Logs\nAll API Calls Logged (JSON)"]
        ANOMALY["Uptime Monitoring\nAnomaly Detection · Alerting"]
    end

    CODE_SECURITY --> INFRA_SECURITY --> RUNTIME_SECURITY --> MONITORING_SEC
```

---

## 8️⃣ Groq AI Brain Engine — Décision Logic

```mermaid
flowchart TD
    IN["📰 Article Brut\n(Titre + Résumé + Source + Langue)"]

    PRECHECK{"🛡️ Pré-filtre NLP\nMots-clés football?"}
    DISCARD["🗑️ Article Rejeté\n(hors sujet)"]

    GROQ_AVAIL{"🔑 GROQ_API_KEY\ndisponible?"}

    GROQ_CALL["🤖 Groq API\nllama-3.3-70b-versatile\n(Prompt structuré JSON)"]

    GROQ_OK{"✅ Réponse OK\n& JSON valide?"}

    RETRY["🔄 Retry + Backoff\n(max 2 tentatives)"]

    LOCAL["📖 Moteur NLP Local\nRegex + Dictionnaires Mercato"]

    EXTRACT["📦 Résultats Structurés\njoueur · clubs · montant\nligue · statut · crédibilité\nfabrizio_title · fabrizio_summary"]

    HASH["#️⃣ Semantic Hash\njoueur__from__to (normalisé)"]

    DEDUP2{"🔄 Hash déjà\nen base?"}

    MERGE["🔀 Fusion d'Articles\n(garde le plus complet)"]
    INSERT["✅ Nouvel Article\nInséré en DB"]

    PHOTO_RES["🖼️ Photo Resolver\nWikimedia + TheSportsDB"]

    FINAL["💾 Neon PostgreSQL\nArticle enrichi persisté"]

    IN --> PRECHECK
    PRECHECK -- Non --> DISCARD
    PRECHECK -- Oui --> GROQ_AVAIL
    GROQ_AVAIL -- Non --> LOCAL
    GROQ_AVAIL -- Oui --> GROQ_CALL
    GROQ_CALL --> GROQ_OK
    GROQ_OK -- Non --> RETRY
    RETRY -- Échec --> LOCAL
    GROQ_OK -- Oui --> EXTRACT
    LOCAL --> EXTRACT
    EXTRACT --> HASH
    HASH --> DEDUP2
    DEDUP2 -- Oui --> MERGE --> FINAL
    DEDUP2 -- Non --> INSERT --> PHOTO_RES --> FINAL

    style DISCARD fill:#450a0a,stroke:#f87171,color:#e2e8f0
    style GROQ_CALL fill:#431407,stroke:#fb923c,color:#e2e8f0
    style LOCAL fill:#1c1917,stroke:#a8a29e,color:#e2e8f0
    style FINAL fill:#052e16,stroke:#4ade80,color:#e2e8f0
```

---

## 9️⃣ Monitoring & Observabilité

```mermaid
graph LR
    subgraph APP_TELEMETRY["📊 Application Telemetry"]
        STRUCTURED_LOGS["Structured Logging\n(Python logging · JSON format)"]
        API_METRICS["API Metrics\nLatence · Status Codes · Throughput"]
        PIPELINE_STATS["Pipeline Stats\nArticles/run · Doublons · Erreurs"]
    end

    subgraph INFRA_MONITORING["🖥️ Infrastructure Monitoring"]
        UPTIME["UptimeRobot\n/api/v1/health Polling (1 min)"]
        RENDER_DASH["Render Dashboard\nCPU · RAM · Deploys · Logs"]
    end

    subgraph ALERTING["🚨 Alerting"]
        SLACK["Slack Webhook\nDeploy Success / Failure"]
        EMAIL["Email Alert\nDowntime Notification"]
    end

    subgraph QUALITY["📈 Code Quality"]
        SONAR["SonarQube\nCode Smells · Coverage\nSecurity Hotspots · Bugs"]
        CODECOV["Codecov\nCoverage Trend (pytest)"]
    end

    APP_TELEMETRY --> ALERTING
    INFRA_MONITORING --> ALERTING
    QUALITY -.->|"PR Gate"| APP_TELEMETRY
```

---

## 🛠️ Stack Technologique Complète

| Couche | Technologie | Rôle |
|---|---|---|
| **Language** | Python 3.10+ | Runtime principal |
| **API Framework** | FastAPI + Uvicorn | REST API async, SSE, OpenAPI |
| **Data Validation** | Pydantic v2 | Schémas + validation runtime |
| **ORM** | SQLAlchemy 2.0 | Abstraction DB, sessions, migrations |
| **Base de Données** | Neon PostgreSQL (Cloud) / SQLite | Persistance des données |
| **Cache** | Redis (Upstash Serverless) | Cache API, rate limiting |
| **AI / LLM** | Groq API (`llama-3.3-70b`) | Analyse, extraction, rédaction |
| **NLP Local** | Regex + Dictionnaires | Fallback sans coût |
| **Scraping** | Requests + LXML + BeautifulSoup4 | Collecte RSS/XML |
| **Planification** | APScheduler | Pipeline automatique (cron) |
| **Frontend** | HTML5 + CSS Vanilla + JS ES6+ | Dashboard Terminal Web |
| **Reverse Proxy** | NGINX | Load balancing, TLS, rate limiting |
| **CDN / WAF** | Cloudflare | DDoS, cache edge, WAF |
| **Conteneurisation** | Docker + Docker Compose | Build reproductible, multi-stage |
| **IaC** | Terraform | Provisioning Cloud déclaratif |
| **CI/CD** | GitHub Actions | Build, test, deploy automatisé |
| **GitOps / CD** | Argo CD | Déploiement déclaratif Kubernetes |
| **Code Quality** | SonarQube | Quality Gate + Hotspots |
| **Security SAST** | Bandit + Gitleaks | Vulnérabilités & secrets |
| **Tests** | pytest + pytest-cov | Tests unitaires & intégration |
| **Hosting** | Render Cloud | Déploiement API production |
| **Secrets** | Render Env Vars / Vault | Gestion sécurisée des clés |
| **Monitoring** | UptimeRobot + Render Logs | Disponibilité & alerting |

---

## 🚀 Installation & Démarrage Local

```bash
# 1. Cloner le dépôt
git clone https://github.com/AymanTN1/sports-scraping.git
cd sports-scraping

# 2. Environnement virtuel
python -m venv .venv
# Windows : .venv\Scripts\activate
# Linux/macOS : source .venv/bin/activate

# 3. Dépendances
pip install -r requirements.txt

# 4. Variables d'environnement (optionnel)
cp .env.example .env  # Configurer GROQ_API_KEY, DATABASE_URL

# 5. Démarrage
uvicorn backend.main:app --reload --port 8000
```

| Interface | URL |
|---|---|
| 🖥️ Dashboard Web | `http://127.0.0.1:8000/` |
| 📖 Swagger UI | `http://127.0.0.1:8000/api/docs` |
| 🔌 Live API (Prod) | [https://mercatopulse-api.onrender.com](https://mercatopulse-api.onrender.com) |

---

## 🔌 Endpoints REST API

| Méthode | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/articles` | Articles paginés (filtres : ligue, club, statut, recherche) |
| `GET` | `/api/v1/articles/{id}` | Détail d'un article |
| `GET` | `/api/v1/articles/leagues` | Championnats représentés |
| `GET` | `/api/v1/articles/clubs` | Clubs identifiés |
| `GET` | `/api/v1/articles/stats` | Statistiques globales |
| `POST` | `/api/v1/articles/import-csv` | Ingestion des données analysées |
| `POST` | `/api/v1/articles/trigger-pipeline` | Déclenche le scraping immédiat |
| `POST` | `/api/v1/articles/purge-non-football` | Purge des articles hors-sujet |
| `GET` | `/api/v1/health` | Health check système |

---

## 📄 Licence

Distribué sous licence **MIT**. Voir [LICENSE](LICENSE) pour plus d'informations.
