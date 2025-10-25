# 🏆 BlackBook Event Feed Service

Real-time event data pulled from Google News RSS feeds and other sources for BlackBook prediction markets.

## 🚀 Quick Start

### Option 1: Using UV (Recommended)
```bash
# Install UV if not already installed
pip install uv

# Install dependencies
uv pip install -r requirements.txt

# Run the service
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Option 2: Using Python directly
```bash
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Option 3: Windows batch script
```bash
start.bat
```

## 📡 API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Get Events by Category
```bash
# Tech events
curl http://localhost:8000/events?category=tech&limit=20

# Crypto events
curl http://localhost:8000/events?category=crypto&limit=20

# Business events
curl http://localhost:8000/events?category=business&limit=10
```

### Get All Cached Events
```bash
curl http://localhost:8000/events/all
```

### Refresh Events for Category
```bash
curl -X POST http://localhost:8000/refresh/tech
```

### Search Events
```bash
curl "http://localhost:8000/search?query=apple&category=tech"
```

### Get Statistics
```bash
curl http://localhost:8000/stats
```

## 📊 Supported Categories

- **tech** - Technology news
- **crypto** - Cryptocurrency and blockchain
- **business** - Business & Finance
- **ai** - Artificial Intelligence
- **startup** - Startup funding and news

## 🔗 Integration with Rust Backend

The Rust backend (BlackBook) connects to this service:

```rust
// In Rust code
let events = fetch_from_event_service("http://localhost:8000/events?category=tech").await;
```

## 📝 Example Response

```json
{
  "category": "tech",
  "events": [
    {
      "id": "a1b2c3d4e5f6g7h8",
      "title": "Apple Announces New AI Features",
      "description": "Apple revealed advanced AI capabilities at their keynote...",
      "event_type": "product_launch",
      "source": "tech",
      "published_at": "2025-10-24T14:30:00+00:00",
      "url": "https://news.google.com/...",
      "category": "tech",
      "confidence_score": 0.85,
      "tags": ["ai", "apple", "keynote"],
      "related_companies": ["Apple", "OpenAI"]
    }
  ],
  "total_count": 20,
  "last_updated": "2025-10-24T15:00:00"
}
```

## 🛠️ Development

### Run with auto-reload
```bash
uv run uvicorn main:app --reload
```

### Run tests
```bash
uv run pytest tests/
```

### Accessing Docs
- OpenAPI docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔄 Event Refresh Schedule

- Events are cached for 5 minutes (300 seconds)
- After cache expires, next request will trigger a refresh
- Manual refresh available via POST /refresh/{category}
- Background tasks handle refreshes without blocking

## 📈 Features

✅ Real-time Google News RSS feeds  
✅ Event categorization (product launch, earnings, etc.)  
✅ Company detection in titles/descriptions  
✅ Tag extraction from headlines  
✅ Configurable cache TTL  
✅ Search functionality  
✅ JSON API for easy integration  
✅ CORS enabled for all origins  
✅ Automatic event deduplication  

## 🐛 Troubleshooting

### Port already in use
```bash
uv run uvicorn main:app --host 127.0.0.1 --port 8001
```

### SSL certificate errors
The service uses HTTP by default. For HTTPS, use a reverse proxy like nginx.

### No events returned
Check that:
1. Service is running on port 8000
2. RSS feeds are accessible
3. Check logs for fetch errors
4. Try manual refresh: `POST /refresh/tech`

## 📚 Related Files

- `main.py` - FastAPI application
- `requirements.txt` - Python dependencies
- `pyproject.toml` - UV configuration
- `start.bat` - Windows startup script

## 🚀 Next Steps

1. Start this service: `start.bat` (Windows) or `uv run uvicorn main:app ...`
2. In another terminal, start the Rust backend: `cargo run` in the blackbook directory
3. The Rust backend will query this service for real events
4. Markets are automatically created from events
