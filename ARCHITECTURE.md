# ObjectWire - System Architecture

## Overview
ObjectWire is an AI-powered event pipeline that scrapes social media events, generates prediction markets, and serves them via API to a blockchain and frontend.

```
┌─────────────────┐
│   RSS Feeds     │
│  External APIs  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         CLI (Event Pipeline)             │
│  ┌────────────┐  ┌─────────┐  ┌────────┐│
│  │  Scraper   │→ │   AI    │→ │  DB    ││
│  │  Module    │  │ Parser  │  │ Layer  ││
│  └────────────┘  └─────────┘  └────┬───┘│
│                                     │    │
│  ┌────────────┐  ┌──────────────┐  │    │
│  │ Blockchain │  │  API Server  │←─┘    │
│  │  Interface │  │  (Express)   │       │
│  └────────────┘  └──────┬───────┘       │
└──────────────────────────┼───────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │  Next.js Web   │
                  │   Frontend     │
                  └────────────────┘
```

---

## Component Architecture

### 1. Input Layer
**Purpose**: Collect raw data from various sources

#### RSS Feed Processor (`src/objectwire/feed_processor.py`)
- Parse RSS/Atom feeds from news sites, social platforms
- Extract article URLs and metadata
- Queue articles for processing
- Support: ESPN, TechCrunch, CoinDesk, Twitter RSS proxies

#### External API Integrations (`src/objectwire/oracles/`)
- `youtube.py` - YouTube Data API v3 (video stats, channels)
- `twitter.py` - Twitter/X API (tweet metrics, engagement)
- `github.py` - GitHub API (repo stars, releases)
- `twitch.py` - Twitch API (stream viewers, followers)

---

### 2. Processing Layer (Core Pipeline)

#### Scraper Module (`src/objectwire/scraper.py`)
**Current**: Exists in `cli.py` as `scrape_url()` function
**Refactor To**:
```python
class Scraper:
    def scrape_url(url: str) -> ScrapedContent
    def scrape_batch(urls: List[str]) -> List[ScrapedContent]
    def validate_content(content: str) -> bool
```

#### AI Parser (`src/objectwire/llama_engine.py`)
**Current**: Implemented with NuExtract
**Enhance**:
- Add batch processing (5-10 articles at once)
- Add confidence scores for extractions
- Add validation layer for parsed data

#### DB Layer (`src/objectwire/database.py`) ⚠️ NEW
**Purpose**: Persistent storage for all events and metadata

**Schema**:
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    market_id TEXT UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    source_url TEXT,
    freeze_date TEXT,
    resolution_date TEXT,
    yes_prob REAL,
    no_prob REAL,
    no_change_prob REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending', -- pending, posted, resolved
    blockchain_tx_id TEXT,
    article_generated BOOLEAN DEFAULT 0
);

CREATE TABLE scrape_history (
    id INTEGER PRIMARY KEY,
    url TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN,
    error_message TEXT,
    event_id INTEGER REFERENCES events(id)
);

CREATE TABLE creators (
    id INTEGER PRIMARY KEY,
    name TEXT,
    platform TEXT,
    platform_id TEXT,
    followers INTEGER,
    avg_engagement REAL,
    tracked_since TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 3. Output Layer

#### Blockchain Interface (`src/objectwire/blockchain.py`)
**Current**: `post_to_blockchain()` in `cli.py`
**Refactor To**:
```python
class BlockchainClient:
    def __init__(self, api_url: str)
    def post_event(event: BlockchainEvent) -> Response
    def get_event(market_id: str) -> BlockchainEvent
    def list_events() -> List[BlockchainEvent]
    def resolve_event(market_id: str, outcome: str) -> Response
```

#### API Server (`server/api.js`) ⚠️ NEW
**Tech Stack**: Express.js + SQLite
**Endpoints**:
```
GET  /api/events              # List all events
GET  /api/events/:market_id   # Get single event
POST /api/events              # Create event (from CLI)
PUT  /api/events/:market_id   # Update event
GET  /api/creators            # List tracked creators
GET  /api/stats               # System statistics
GET  /api/health              # Health check
```

**Directory Structure**:
```
server/
├── api.js           # Main Express app
├── routes/
│   ├── events.js    # Event routes
│   ├── creators.js  # Creator routes
│   └── stats.js     # Stats routes
├── db/
│   └── sqlite.js    # DB connection
├── package.json
└── .env
```

---

### 4. Frontend Layer

#### Next.js Website (`frontend/`) ⚠️ NEW
**Pages**:
- `/` - Homepage with featured events
- `/events` - Browse all prediction markets
- `/events/[id]` - Event detail page
- `/creators` - Tracked creators dashboard
- `/about` - About ObjectWire

**Tech Stack**:
- Next.js 14 (App Router)
- TailwindCSS
- shadcn/ui components
- React Query for data fetching

---

## Data Flow

### Flow 1: RSS → DB → API → Frontend
```
1. RSS Feed URL → feed_processor.py
2. Extract 10 articles → scraper.scrape_batch()
3. AI parses articles → llama_engine.analyze_article_blockchain()
4. Save to DB → database.save_events()
5. API exposes → GET /api/events
6. Frontend fetches → Display cards
```

### Flow 2: Manual Scrape → Blockchain
```
1. User: objectwire scrape URL --post
2. Scraper extracts content
3. AI generates BlockchainEvent
4. Save to DB (status='pending')
5. Post to blockchain API
6. Update DB (status='posted', blockchain_tx_id)
7. Prompt: "Write article?" → gemini_writer.py
```

### Flow 3: Scheduled Pipeline (Future)
```
1. Cron job: objectwire pipeline run
2. Check RSS feeds (every 30 min)
3. Scrape new articles
4. AI batch process
5. Auto-post high-confidence events
6. Update DB + blockchain
```

---

## CLI Command Structure (Enhanced)

```bash
# Current commands (keep)
objectwire scrape <url>              # Scrape single URL
objectwire scrape <url> --post       # Scrape + post to blockchain
objectwire scrape <url> --json       # JSON output

# New pipeline commands
objectwire pipeline start            # Start full pipeline (RSS + processing)
objectwire pipeline stop             # Stop pipeline
objectwire pipeline status           # Show pipeline status

# Feed commands
objectwire feed add <url>            # Add RSS feed to watch list
objectwire feed list                 # List all watched feeds
objectwire feed process <url>        # Process single feed now

# Database commands
objectwire db query "SELECT..."      # Run SQL query
objectwire db stats                  # Show DB statistics
objectwire db export events.json     # Export all events

# API commands
objectwire api start                 # Start Express API server
objectwire api test                  # Test API endpoints

# Creator tracking
objectwire creator add "MrBeast" youtube UCX6OQ3DkcsbYNE6H8uQQuVA
objectwire creator list
objectwire creator stats "MrBeast"
```

---

## Implementation Phases

### Phase 1: Database Layer (Week 1)
- [ ] Create `src/objectwire/database.py`
- [ ] Design SQLite schema (events, scrape_history, creators)
- [ ] Add CRUD operations
- [ ] Migrate existing file-based logs to DB
- [ ] Update CLI to use DB instead of files

### Phase 2: Modular Refactor (Week 1-2)
- [ ] Extract scraper logic to `scraper.py`
- [ ] Extract blockchain logic to `blockchain.py`
- [ ] Create `feed_processor.py` for RSS
- [ ] Update `cli.py` to orchestrate modules

### Phase 3: API Server (Week 2)
- [ ] Create `server/` directory with Express.js
- [ ] Implement REST endpoints
- [ ] Connect to SQLite DB
- [ ] Add CORS for frontend
- [ ] Deploy on localhost:3001

### Phase 4: Frontend (Week 3-4)
- [ ] Initialize Next.js project in `frontend/`
- [ ] Design UI with Tailwind + shadcn/ui
- [ ] Implement pages (home, events, creators)
- [ ] Connect to API server
- [ ] Deploy

### Phase 5: Integration (Week 4)
- [ ] End-to-end testing
- [ ] Pipeline automation
- [ ] Monitoring & logging
- [ ] Documentation

---

## Technology Stack Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| CLI | Python + Click + Rich | User interface |
| AI Model | NuExtract 1.5 (llama.cpp) | Event extraction |
| Database | SQLite | Persistent storage |
| API Server | Express.js + Node.js | REST API |
| Frontend | Next.js 14 + Tailwind | Web interface |
| Blockchain | Custom API (localhost:1234) | Event posting |
| Article Writer | Google Gemini 2.0 | Content generation |

---

## File Structure (Target)

```
url_scraper_agent.py/
├── src/
│   └── objectwire/
│       ├── cli.py              # Main CLI orchestrator
│       ├── scraper.py          # Web scraping module
│       ├── llama_engine.py     # AI extraction engine
│       ├── database.py         # SQLite DB layer ⚠️ NEW
│       ├── blockchain.py       # Blockchain client ⚠️ NEW
│       ├── feed_processor.py   # RSS feed parser ⚠️ NEW
│       ├── gemini_writer.py    # Article generation (Gemini 2.0)
│       └── oracles/            # External API integrations ⚠️ NEW
│           ├── youtube.py
│           ├── twitter.py
│           └── github.py
├── server/                     # Express API server ⚠️ NEW
│   ├── api.js
│   ├── routes/
│   └── db/
├── frontend/                   # Next.js website ⚠️ NEW
│   ├── app/
│   ├── components/
│   └── public/
├── logs/                       # Legacy logs (migrate to DB)
├── models/                     # AI model files
├── tests/
└── README.md
```

---

## Next Steps

1. **Immediate**: Implement database layer (`database.py`)
2. **This Week**: Refactor CLI to use modular components
3. **Next Week**: Build Express.js API server
4. **Month 1**: Launch Next.js frontend
5. **Month 2**: Full pipeline automation

See `ROADMAP.md` for detailed milestones.
