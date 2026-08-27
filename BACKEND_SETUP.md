# 🚀 SportPulse Backend Setup Guide

This guide explains how to set up and run the FastAPI backend for the SportPulse Sports Press Review application.

## 📋 Prerequisites

- Python 3.8+
- pip or conda
- PostgreSQL 12+ (optional, but recommended for production)
- Anthropic API key for AI analysis features

## 🔧 Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and add your configuration:

```
ANTHROPIC_API_KEY=sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DATABASE_URL=sqlite:///./sportpulse.db
API_HOST=0.0.0.0
API_PORT=8000
```

### 3. Initialize Database

The database tables are created automatically on first run. To manually initialize:

```bash
python -c "from backend.database import init_db; init_db(); print('Database initialized!')"
```

## 🏃 Running the Backend

### Development Mode

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Production Mode

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📡 API Endpoints

### Articles
- `GET /api/articles/` - List all articles with pagination
- `GET /api/articles/{id}` - Get single article
- `GET /api/articles/categories` - List all categories
- `GET /api/articles/sources` - List all sources
- `GET /api/articles/stats` - Get statistics
- `POST /api/articles/import-csv` - Import from CSV

### Pipeline
- `POST /api/pipeline/run` - Start pipeline execution
- `GET /api/pipeline/status/{run_id}` - Get pipeline status
- `GET /api/pipeline/latest` - Get latest pipeline run
- `GET /api/pipeline/runs` - List all pipeline runs

### Reports
- `GET /api/reports/latest` - Get latest report
- `GET /api/reports/by-date/{date}` - Get report by date
- `GET /api/reports/latest/html` - Download HTML report
- `GET /api/reports/latest/json` - Download JSON report
- `GET /api/reports/latest/txt` - Download text report

### AI Analysis
- `POST /api/ai/analyze` - Analyze article with AI
- `GET /api/ai/{article_id}/general` - General analysis
- `GET /api/ai/{article_id}/summary` - AI summary
- `GET /api/ai/{article_id}/detailed` - Detailed analysis
- `POST /api/ai/report-analysis` - Generate report introduction

## 🗄️ Database Setup

### SQLite (Default)

Works out of the box. Database file: `sportpulse.db`

### PostgreSQL (Recommended for Production)

1. Install PostgreSQL
2. Create database:
   ```bash
   createdb sportpulse
   ```

3. Update `.env`:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/sportpulse
   ```

4. Install psycopg2:
   ```bash
   pip install psycopg2-binary
   ```

## 🔄 Integration with Frontend

The frontend should be configured to call the backend API:

```javascript
// Update API_BASE_URL in your frontend code
const API_BASE_URL = 'http://localhost:8000/api';

// Fetch articles
const response = await fetch(`${API_BASE_URL}/articles?page=1`);
const data = await response.json();
```

## 🧪 Testing

### Import CSV Data

```bash
curl -X POST http://localhost:8000/api/articles/import-csv
```

### Get Articles

```bash
curl http://localhost:8000/api/articles?page=1
```

### Run Pipeline

```bash
curl -X POST http://localhost:8000/api/pipeline/run
```

### Analyze Article

```bash
curl -X POST http://localhost:8000/api/ai/analyze \
  -H "Content-Type: application/json" \
  -d '{"article_id": 1, "analysis_type": "general"}'
```

## 📊 Monitoring

### Check Health

```bash
curl http://localhost:8000/health
```

### View API Docs

Open browser: `http://localhost:8000/docs`

### Monitor Pipeline

```bash
curl http://localhost:8000/api/pipeline/latest
```

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Change port
python -m uvicorn backend.main:app --port 8001
```

### Database Connection Error

- Check DATABASE_URL in `.env`
- Verify PostgreSQL is running (if using PostgreSQL)
- Delete `sportpulse.db` and restart if using SQLite

### ANTHROPIC_API_KEY Not Found

- Ensure `.env` file exists with API key
- Check environment variable is properly set
- Verify API key is valid on Anthropic dashboard

### CORS Errors

- Update CORS_ORIGINS in `.env`
- For development: use wildcard `["*"]`
- For production: specify exact origins

## 📚 Project Structure

```
backend/
├── main.py           # FastAPI application
├── database.py       # Database setup
├── models.py         # SQLAlchemy models
├── schemas.py        # Pydantic request/response schemas
├── routes/
│   ├── articles.py   # Articles endpoints
│   ├── pipeline.py   # Pipeline execution endpoints
│   ├── reports.py    # Report endpoints
│   └── ai.py         # AI analysis endpoints
└── __init__.py
```

## 🔐 Security Considerations

1. **API Keys**: Never commit `.env` files
2. **CORS**: Restrict origins in production
3. **Database**: Use PostgreSQL for production
4. **HTTPS**: Use reverse proxy (nginx) with SSL
5. **Rate Limiting**: Implement rate limiting for production

## 📝 Development

### Adding New Endpoints

1. Create route file in `backend/routes/`
2. Define router and endpoints
3. Include router in `backend/main.py`
4. Update frontend to call new endpoints

### Modifying Models

1. Edit `backend/models.py`
2. Create database migration (if using Alembic)
3. Or delete `sportpulse.db` to recreate from scratch

## 🚀 Deployment

### Using Docker

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Using systemd

Create `/etc/systemd/system/sportpulse.service`:

```ini
[Unit]
Description=SportPulse Sports Press Review API
After=network.target

[Service]
Type=notify
User=sportpulse
WorkingDirectory=/var/www/sportpulse
ExecStart=/var/www/sportpulse/.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start sportpulse
sudo systemctl status sportpulse
```

## 📞 Support

For issues or questions:
1. Check API docs: `http://localhost:8000/docs`
2. Review logs in terminal
3. Check GitHub issues

## 📄 License

This project is licensed under the MIT License.
