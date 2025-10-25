# BlackBook Event Feed Service
# Pulls real events from Google News RSS and other sources
# Provides JSON API for the Rust prediction market backend

from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import feedparser
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import logging
import httpx
from enum import Enum
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION
# ============================================

app = FastAPI(
    title="BlackBook Event Feed Service",
    description="Real-time event feed for prediction markets",
    version="1.0.0"
)

# Add CORS for Rust backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Google News RSS feeds by category
GOOGLE_NEWS_FEEDS = {
    "tech": "https://news.google.com/news/rss/headlines/section/topic/TECHNOLOGY",
    "crypto": "https://news.google.com/news/rss/headlines/section/topic/CRYPTO",
    "business": "https://news.google.com/news/rss/headlines/section/topic/BUSINESS_AND_FINANCE",
    "ai": "https://news.google.com/news/rss/search?q=artificial%20intelligence",
    "startup": "https://news.google.com/news/rss/search?q=startup%20funding",
}

# Additional news sources
ALTERNATIVE_FEEDS = {
    "techcrunch": "https://techcrunch.com/feed/",
    "hackernews": "https://news.ycombinator.com/rss",
}

# ============================================
# DATA MODELS
# ============================================

class EventType(str, Enum):
    PRODUCT_LAUNCH = "product_launch"
    EARNINGS = "earnings"
    CONFERENCE = "conference"
    IPO = "ipo"
    ACQUISITION = "acquisition"
    REGULATION = "regulation"
    PARTNERSHIP = "partnership"
    BREAKTHROUGH = "breakthrough"
    MARKET_MOVEMENT = "market_movement"

class Event(BaseModel):
    id: str
    title: str
    description: str
    event_type: EventType
    source: str
    published_at: str
    url: str
    category: str
    confidence_score: float = 0.8
    tags: List[str] = []
    related_companies: List[str] = []

class EventFeed(BaseModel):
    category: str
    events: List[Event]
    total_count: int
    last_updated: str

# ============================================
# IN-MEMORY CACHE
# ============================================

event_cache = {}  # {category: {id: Event}}
cache_timestamp = {}  # {category: datetime}
CACHE_TTL_SECONDS = 300  # Refresh every 5 minutes

# ============================================
# UTILITY FUNCTIONS
# ============================================

def generate_event_id(title: str, published_at: str) -> str:
    """Generate unique event ID"""
    content = f"{title}:{published_at}"
    return hashlib.md5(content.encode()).hexdigest()[:16]

def parse_event_date(date_string: str) -> str:
    """Parse various date formats to ISO 8601"""
    try:
        # Try RFC 2822 format (most common in RSS)
        dt = datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %z")
        return dt.isoformat()
    except:
        try:
            # Try ISO 8601
            dt = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
            return dt.isoformat()
        except:
            # Fallback to current time
            return datetime.now().isoformat()

def extract_keywords(title: str, description: str) -> tuple[List[str], List[str]]:
    """Extract tags and related companies from title/description"""
    # Simple keyword extraction
    keywords_lower = (title + " " + description).lower()
    
    companies = []
    keywords = []
    
    # Common tech companies to track
    tech_companies = [
        "apple", "google", "microsoft", "amazon", "nvidia", "tesla", "openai",
        "meta", "twitter", "nvidia", "intel", "amd", "solana", "ethereum",
        "bitcoin", "stripe", "figma", "canva", "databricks", "anthropic"
    ]
    
    for company in tech_companies:
        if company in keywords_lower:
            companies.append(company.capitalize())
    
    # Extract hashtags
    words = title.split()
    for word in words:
        if word.startswith("#"):
            keywords.append(word[1:].lower())
    
    return keywords[:5], companies[:3]

async def fetch_feed(feed_url: str, category: str) -> List[Event]:
    """Fetch and parse RSS feed"""
    events = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(feed_url)
                feed = feedparser.parse(response.text)
            except:
                # Fallback: use synchronous fetch for some sources
                import requests
                response = requests.get(feed_url, timeout=10)
                feed = feedparser.parse(response.text)
        
        logger.info(f"📰 Fetched {len(feed.entries)} entries from {category}")
        
        for entry in feed.entries[:20]:  # Limit to 20 per feed
            try:
                title = entry.get("title", "")
                description = entry.get("summary", entry.get("description", ""))
                published = entry.get("published", datetime.now().isoformat())
                link = entry.get("link", "")
                
                if not title:
                    continue
                
                event_id = generate_event_id(title, published)
                tags, companies = extract_keywords(title, description)
                
                # Determine event type from keywords
                event_type = EventType.MARKET_MOVEMENT
                if any(word in title.lower() for word in ["launch", "announced", "release"]):
                    event_type = EventType.PRODUCT_LAUNCH
                elif any(word in title.lower() for word in ["earnings", "quarterly", "results"]):
                    event_type = EventType.EARNINGS
                elif any(word in title.lower() for word in ["conference", "summit", "keynote"]):
                    event_type = EventType.CONFERENCE
                elif any(word in title.lower() for word in ["ipo", "public offering"]):
                    event_type = EventType.IPO
                elif any(word in title.lower() for word in ["acquisition", "acquires", "acquired"]):
                    event_type = EventType.ACQUISITION
                elif any(word in title.lower() for word in ["regulation", "regulatory", "laws"]):
                    event_type = EventType.REGULATION
                elif any(word in title.lower() for word in ["partnership", "partners with", "collaboration"]):
                    event_type = EventType.PARTNERSHIP
                elif any(word in title.lower() for word in ["breakthrough", "breakthrough", "discovery"]):
                    event_type = EventType.BREAKTHROUGH
                
                event = Event(
                    id=event_id,
                    title=title,
                    description=description[:500],  # Limit description length
                    event_type=event_type,
                    source=category,
                    published_at=parse_event_date(published),
                    url=link,
                    category=category,
                    confidence_score=0.85,
                    tags=tags,
                    related_companies=companies
                )
                
                events.append(event)
                
            except Exception as e:
                logger.warning(f"⚠️  Error parsing entry: {e}")
                continue
        
        return events
    
    except Exception as e:
        logger.error(f"❌ Error fetching {category} feed: {e}")
        return []

async def refresh_cache(category: str):
    """Refresh event cache for a category"""
    if category not in GOOGLE_NEWS_FEEDS and category not in ALTERNATIVE_FEEDS:
        logger.warning(f"Unknown category: {category}")
        return
    
    feed_url = GOOGLE_NEWS_FEEDS.get(category) or ALTERNATIVE_FEEDS.get(category)
    logger.info(f"🔄 Refreshing {category} from {feed_url}")
    
    events = await fetch_feed(feed_url, category)
    
    # Store in cache with deduplication by ID
    if category not in event_cache:
        event_cache[category] = {}
    
    for event in events:
        event_cache[category][event.id] = event
    
    cache_timestamp[category] = datetime.now()
    logger.info(f"✅ Cached {len(events)} events for {category}")

# ============================================
# API ENDPOINTS
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize cache on startup"""
    logger.info("🚀 BlackBook Event Feed Service starting...")
    logger.info("Preloading event cache...")
    
    for category in list(GOOGLE_NEWS_FEEDS.keys())[:3]:  # Load first 3 categories
        await refresh_cache(category)

@app.get("/")
async def root():
    """Service info"""
    return {
        "service": "BlackBook Event Feed Service",
        "version": "1.0.0",
        "status": "running",
        "categories": list(GOOGLE_NEWS_FEEDS.keys()),
        "cached_categories": list(event_cache.keys()),
        "endpoints": {
            "GET /events": "Get events by category",
            "GET /events/all": "Get all cached events",
            "POST /refresh/{category}": "Refresh events for category",
            "GET /stats": "Service statistics",
            "GET /health": "Health check"
        }
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "cached_categories": len(event_cache),
        "total_events": sum(len(events) for events in event_cache.values())
    }

@app.get("/events", response_model=EventFeed)
async def get_events(
    category: str = Query("tech", description="Event category"),
    limit: int = Query(20, description="Max events to return")
):
    """Get events by category"""
    
    # Check cache freshness
    if category in cache_timestamp:
        age = (datetime.now() - cache_timestamp[category]).total_seconds()
        if age > CACHE_TTL_SECONDS:
            logger.info(f"Cache stale for {category}, refreshing...")
            await refresh_cache(category)
    else:
        # Not in cache, fetch
        await refresh_cache(category)
    
    events = list(event_cache.get(category, {}).values())[:limit]
    
    return EventFeed(
        category=category,
        events=events,
        total_count=len(events),
        last_updated=datetime.now().isoformat()
    )

@app.get("/events/all", response_model=dict)
async def get_all_events():
    """Get all cached events across all categories"""
    result = {}
    for category, events_dict in event_cache.items():
        result[category] = list(events_dict.values())
    
    return {
        "total_categories": len(result),
        "total_events": sum(len(events) for events in result.values()),
        "categories": result,
        "last_updated": datetime.now().isoformat()
    }

@app.post("/refresh/{category}")
async def refresh_events(category: str, background_tasks: BackgroundTasks):
    """Manually refresh events for a category"""
    
    if category not in GOOGLE_NEWS_FEEDS and category not in ALTERNATIVE_FEEDS:
        return {"error": f"Unknown category: {category}"}
    
    # Run refresh in background
    background_tasks.add_task(refresh_cache, category)
    
    return {
        "status": "refreshing",
        "category": category,
        "message": f"Events for {category} are being refreshed in background"
    }

@app.get("/stats")
async def get_stats():
    """Get service statistics"""
    return {
        "cached_categories": len(event_cache),
        "total_events": sum(len(events) for events in event_cache.values()),
        "by_category": {
            cat: len(events) for cat, events in event_cache.items()
        },
        "by_type": {
            event_type.value: sum(
                1 for events in event_cache.values()
                for event in events.values()
                if event.event_type == event_type
            )
            for event_type in EventType
        }
    }

@app.get("/search")
async def search_events(
    query: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Optional category filter")
):
    """Search events by query"""
    query_lower = query.lower()
    results = []
    
    categories_to_search = [category] if category else event_cache.keys()
    
    for cat in categories_to_search:
        for event in event_cache.get(cat, {}).values():
            if (query_lower in event.title.lower() or 
                query_lower in event.description.lower()):
                results.append(event)
    
    return {
        "query": query,
        "total_results": len(results),
        "results": results[:20]
    }

# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    print("""
    🏆 BlackBook Event Feed Service
    📍 Starting on http://localhost:8000
    🔗 Connect to Rust backend on http://localhost:3000
    """)
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
