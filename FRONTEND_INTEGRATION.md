# 🔌 Frontend-Backend Integration Guide

This guide explains how the frontend and backend are integrated and how to use them together.

## 📚 Quick Overview

The SportPulse application now has a complete FastAPI backend that serves data, manages pipelines, and provides AI analysis through a REST API. The frontend communicates with this backend instead of loading CSV files directly.

### Architecture

```
┌─────────────────────────────────────────────┐
│         Frontend (HTML + JavaScript)        │
│  web/index.html + frontend/js/api.js        │
└────────────┬────────────────────────────────┘
             │ HTTP Requests
             ▼
┌─────────────────────────────────────────────┐
│        FastAPI Backend (Python)             │
│  backend/main.py + routes                   │
└────────────┬────────────────────────────────┘
             │ Database Queries
             ▼
┌─────────────────────────────────────────────┐
│     SQLite Database (sportpulse.db)               │
│     or PostgreSQL (production)               │
└─────────────────────────────────────────────┘
```

## 🚀 Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file:

```bash
ANTHROPIC_API_KEY=sk_xxxxx
DATABASE_URL=sqlite:///./sportpulse.db
API_HOST=0.0.0.0
API_PORT=8000
```

### 3. Start the Backend

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 4. Access the Frontend

Open your browser to `http://localhost:8000/web/index.html` or serve it from your web server.

## 📡 API Endpoints

The frontend uses these endpoints:

### Articles
- **GET** `/api/articles/` - List articles with pagination
  ```javascript
  const data = await fetchArticlesFromAPI(page, pageSize, filters);
  ```

- **GET** `/api/articles/categories` - Get all categories
  ```javascript
  const categories = await fetchCategories();
  ```

- **GET** `/api/articles/sources` - Get all sources
  ```javascript
  const sources = await fetchSources();
  ```

- **GET** `/api/articles/stats` - Get statistics
  ```javascript
  const stats = await fetchArticleStats();
  ```

- **POST** `/api/articles/import-csv` - Import from CSV
  ```javascript
  await importArticlesFromCSV();
  ```

### Pipeline
- **POST** `/api/pipeline/run` - Start pipeline
  ```javascript
  const result = await runPipeline();
  ```

- **GET** `/api/pipeline/status/{id}` - Get status
  ```javascript
  const status = await getPipelineStatus(runId);
  ```

- **GET** `/api/pipeline/latest` - Latest pipeline run
  ```javascript
  const latest = await getLatestPipelineRun();
  ```

### AI Analysis
- **POST** `/api/ai/analyze` - Analyze article
  ```javascript
  const analysis = await analyzeArticleWithAPI(articleId, type);
  ```

- **GET** `/api/ai/{id}/general` - General analysis
- **GET** `/api/ai/{id}/summary` - Summary
- **GET** `/api/ai/{id}/detailed` - Detailed analysis
- **POST** `/api/ai/report-analysis` - Generate report

### Reports
- **GET** `/api/reports/latest` - Latest report
- **GET** `/api/reports/latest/html` - Download HTML
- **GET** `/api/reports/latest/json` - Download JSON
- **GET** `/api/reports/latest/txt` - Download TXT

## 🔄 Data Flow

### Loading Articles

```
Frontend (index.html)
  ├─ try: loadDataFromAPI()
  │  └─ fetch /api/articles/
  │     ├─ load from DB
  │     └─ return JSON
  │
  └─ catch: fallback to CSV
     ├─ fetch ../data/output/verified_articles.csv
     ├─ parse CSV in JavaScript
     └─ use local data
```

### AI Analysis

```
User clicks "Détails" on article
  │
  ├─ fetchPhoto() → Wikipedia API
  │
  └─ fetchAI() → analyzeArticleWithAPI()
     │
     └─ POST /api/ai/{id}/general
        └─ Backend calls Claude API
           └─ Returns analysis
```

### Running Pipeline

```
User clicks "Run Pipeline" (in admin panel - can be added)
  │
  └─ runPipeline()
     │
     └─ POST /api/pipeline/run
        ├─ Backend runs scraper
        ├─ Backend runs organizer
        ├─ Backend runs enricher
        ├─ Backend runs verifier
        ├─ Backend runs report generator
        └─ Updates database
```

## 🛠️ Frontend JavaScript API

The frontend uses a JavaScript API module (`frontend/js/api.js`) that provides these functions:

### Core Functions

```javascript
// Articles
fetchArticlesFromAPI(page, pageSize, filters)
fetchCategories()
fetchSources()
fetchArticleStats()
importArticlesFromCSV()

// Pipeline
runPipeline()
getPipelineStatus(runId)
getLatestPipelineRun()
monitorPipeline(runId, callback)

// Reports
getLatestReport()
getReportHTML()
getReportJSON()

// AI
analyzeArticleWithAPI(articleId, analysisType)
streamAnalysisFromAPI(articleId, analysisType, element)

// Utility
loadDataFromAPI()
convertAPIArticles(apiData)
```

## 🔐 Environment Variables

Required:
- `ANTHROPIC_API_KEY` - For AI analysis features

Optional:
- `DATABASE_URL` - Database connection string (default: SQLite)
- `API_HOST` - API host (default: 0.0.0.0)
- `API_PORT` - API port (default: 8000)
- `CORS_ORIGINS` - Allowed origins for CORS

## 🐛 Troubleshooting

### API Not Responding

1. Check if backend is running
   ```bash
   curl http://localhost:8000/health
   ```

2. Check CORS settings - frontend and backend must be on same or allowed origins

3. Check browser console for errors

### Articles Not Loading

```javascript
// Try importing from CSV
await importArticlesFromCSV();

// Check API response
const data = await fetchArticlesFromAPI(1, 100);
console.log(data);
```

### AI Analysis Errors

- Verify `ANTHROPIC_API_KEY` is set
- Check API key is valid
- Check rate limits haven't been exceeded

### Database Errors

- Delete `sportpulse.db` and restart backend to recreate
- Check `DATABASE_URL` in `.env`
- For PostgreSQL, verify connection string

## 📊 Testing

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# List articles
curl http://localhost:8000/api/articles?page=1

# Get categories
curl http://localhost:8000/api/articles/categories

# Import from CSV
curl -X POST http://localhost:8000/api/articles/import-csv

# Run pipeline
curl -X POST http://localhost:8000/api/pipeline/run

# Check pipeline status
curl http://localhost:8000/api/pipeline/status/1
```

### Test in Browser Console

```javascript
// Load API module first
const script = document.createElement('script');
script.src = '../frontend/js/api.js';
document.head.appendChild(script);

// Then test
const articles = await fetchArticlesFromAPI(1, 10);
console.log(articles);
```

## 🚀 Production Deployment

### Using Gunicorn + Nginx

```bash
# Install Gunicorn
pip install gunicorn

# Run backend
gunicorn -w 4 -b 0.0.0.0:8000 backend.main:app

# Configure Nginx as reverse proxy
```

### Using Docker

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment for Production

```
ANTHROPIC_API_KEY=sk_production_key
DATABASE_URL=postgresql://user:pass@prod-db:5432/sportpulse
API_HOST=api.example.com
CORS_ORIGINS=["https://example.com"]
```

## 📝 Modifying the Frontend

To add a new feature that uses the API:

1. Add API function to `frontend/js/api.js`
2. Include it in the HTML or call from JavaScript
3. Update the data handling in your component

Example:

```javascript
// Add to frontend/js/api.js
async function fetchNewFeature() {
  const response = await fetch(`${API_BASE_URL}/new-endpoint`);
  if (!response.ok) throw new Error('Failed');
  return await response.json();
}

// Use in HTML
async function myFeature() {
  const data = await fetchNewFeature();
  // Handle data
}
```

## 🔄 Deployment Workflow

1. **Development**
   ```bash
   python -m uvicorn backend.main:app --reload
   ```

2. **Testing**
   ```bash
   # Run tests
   pytest backend/routes/
   ```

3. **Production**
   ```bash
   gunicorn -w 4 backend.main:app
   ```

## 📞 Support

- API Documentation: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- GitHub Issues: [your-repo]

## 📄 License

MIT License - See LICENSE file for details
