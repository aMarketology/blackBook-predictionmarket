"""
ObjectWire Feed Monitor
=======================
Real-time RSS feed monitoring that runs in the background.

Features:
- Background thread monitoring
- NuExtract AI filtering for important events
- Auto-scrape every 5-30 minutes
- Database integration
- Popular feeds pre-configured
"""

import time
import logging
import threading
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False
    logging.warning("feedparser not installed. Run: pip install feedparser")

logger = logging.getLogger(__name__)


# Popular RSS Feeds Configuration
POPULAR_FEEDS = {
    # YouTube Creator Feeds (RSS format: https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID)
    "mrbeast": {
        "name": "MrBeast",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCX6OQ3DkcsbYNE6H8uQQuVA",
        "category": "social",
        "check_interval_minutes": 15,  # Check every 15 min for new videos
        "platform": "youtube",
        "creator_info": {
            "name": "MrBeast",
            "platform_id": "UCX6OQ3DkcsbYNE6H8uQQuVA",
            "subscribers": 250000000,  # ~250M subs
            "avg_views": 100000000  # ~100M avg views per video
        }
    },
    
    "sidemen": {
        "name": "Sidemen",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCDogdKl7t7NHzQ95aEwkdMw",
        "category": "social",
        "check_interval_minutes": 20,
        "platform": "youtube",
        "creator_info": {
            "name": "Sidemen",
            "platform_id": "UCDogdKl7t7NHzQ95aEwkdMw",
            "subscribers": 21000000,
            "avg_views": 10000000
        }
    },
    
    # News & Tech Feeds
    "techcrunch": {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "category": "tech",
        "check_interval_minutes": 30,
        "platform": "news"
    },
    
    "espn_nfl": {
        "name": "ESPN NFL",
        "url": "https://www.espn.com/espn/rss/nfl/news",
        "category": "sports",
        "check_interval_minutes": 30,
        "platform": "news"
    },
    
    "coindesk": {
        "name": "CoinDesk",
        "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "category": "crypto",
        "check_interval_minutes": 20,
        "platform": "news"
    }
}


@dataclass
class FeedEntry:
    """RSS feed entry."""
    feed_id: str
    title: str
    link: str
    published: datetime
    summary: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None


class FeedMonitor:
    """Real-time RSS feed monitor with background processing."""
    
    def __init__(
        self,
        feeds: Optional[Dict] = None,
        check_interval: int = 300,  # 5 minutes default
        use_ai_filter: bool = True,
        min_ai_confidence: float = 0.75,
        database=None,
        scraper=None,
        ai_engine=None
    ):
        """Initialize feed monitor.
        
        Args:
            feeds: Dictionary of feeds to monitor (uses POPULAR_FEEDS if None)
            check_interval: Default check interval in seconds
            use_ai_filter: Use AI to filter important events
            min_ai_confidence: Minimum AI confidence for filtering
            database: Database instance for storage
            scraper: Scraper instance for content extraction
            ai_engine: LlamaEngine instance for AI filtering
        """
        if not FEEDPARSER_AVAILABLE:
            raise ImportError("feedparser is required. Install with: pip install feedparser")
        
        self.feeds = feeds or POPULAR_FEEDS
        self.check_interval = check_interval
        self.use_ai_filter = use_ai_filter
        self.min_ai_confidence = min_ai_confidence
        self.database = database
        self.scraper = scraper
        self.ai_engine = ai_engine
        
        # Track seen entries to avoid duplicates
        self.seen_entries: Set[str] = set()
        
        # Monitoring state
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Statistics
        self.stats = {
            'total_checks': 0,
            'total_entries': 0,
            'filtered_entries': 0,
            'important_events': 0,
            'errors': 0
        }
        
        logger.info(f"Initialized FeedMonitor with {len(self.feeds)} feeds")
    
    def start(self):
        """Start background feed monitoring."""
        if self.is_running:
            logger.warning("Feed monitor already running")
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info(f"🚀 Feed monitor started (checking {len(self.feeds)} feeds)")
        print(f"✅ Monitoring {len(self.feeds)} RSS feeds in background...")
        print(f"   • MrBeast YouTube (every 15 min)")
        print(f"   • Sidemen YouTube (every 20 min)")
        print(f"   • TechCrunch (every 30 min)")
        print(f"   • ESPN NFL (every 30 min)")
        print(f"   • CoinDesk (every 20 min)")
    
    def stop(self):
        """Stop background feed monitoring."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Feed monitor stopped")
        print("🛑 Feed monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop (runs in background thread)."""
        logger.info("Monitor loop started")
        
        # Track last check time for each feed
        last_check: Dict[str, datetime] = {}
        
        while self.is_running:
            try:
                current_time = datetime.utcnow()
                
                # Check each feed based on its interval
                for feed_id, feed_config in self.feeds.items():
                    interval_minutes = feed_config.get('check_interval_minutes', 30)
                    interval_seconds = interval_minutes * 60
                    
                    # Check if it's time to update this feed
                    last_check_time = last_check.get(feed_id)
                    if last_check_time is None or (current_time - last_check_time).total_seconds() >= interval_seconds:
                        self._check_feed(feed_id, feed_config)
                        last_check[feed_id] = current_time
                
                # Sleep for a short time before next check
                time.sleep(60)  # Check every minute to see if any feed needs updating
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                self.stats['errors'] += 1
                time.sleep(60)
    
    def _check_feed(self, feed_id: str, feed_config: Dict):
        """Check a single feed for new entries.
        
        Args:
            feed_id: Feed identifier
            feed_config: Feed configuration
        """
        try:
            url = feed_config['url']
            feed_name = feed_config['name']
            
            logger.info(f"📡 Checking feed: {feed_name} ({feed_id})")
            
            # Parse RSS feed
            feed = feedparser.parse(url)
            
            if feed.bozo:  # Feed parsing error
                logger.warning(f"Feed parsing error for {feed_name}: {feed.bozo_exception}")
                return
            
            self.stats['total_checks'] += 1
            
            # Process entries (newest first)
            new_entries = []
            for entry in feed.entries[:10]:  # Check last 10 entries
                entry_id = entry.get('id') or entry.get('link')
                
                # Skip if we've seen this entry before
                if entry_id in self.seen_entries:
                    continue
                
                # Mark as seen
                self.seen_entries.add(entry_id)
                
                # Parse published date
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                else:
                    published = datetime.utcnow()
                
                # Create FeedEntry
                feed_entry = FeedEntry(
                    feed_id=feed_id,
                    title=entry.get('title', 'Untitled'),
                    link=entry.get('link', ''),
                    published=published,
                    summary=entry.get('summary', ''),
                    content=entry.get('content', [{}])[0].get('value', ''),
                    author=entry.get('author', feed_name)
                )
                
                new_entries.append(feed_entry)
                self.stats['total_entries'] += 1
            
            if new_entries:
                logger.info(f"✨ Found {len(new_entries)} new entries from {feed_name}")
                print(f"\n🆕 {len(new_entries)} new entries from {feed_name}")
                
                # Process new entries
                for entry in new_entries:
                    self._process_entry(entry, feed_config)
            
            # Update feed check time in database
            if self.database:
                try:
                    # Get feed from database
                    feeds = self.database.list_feeds(enabled_only=False)
                    existing_feed = next((f for f in feeds if f['url'] == url), None)
                    
                    if existing_feed:
                        self.database.update_feed_check(existing_feed['id'], len(new_entries))
                    else:
                        # Add feed to database
                        self.database.add_feed(
                            url=url,
                            title=feed_name,
                            category=feed_config.get('category')
                        )
                except Exception as e:
                    logger.error(f"Database error: {e}")
        
        except Exception as e:
            logger.error(f"Error checking feed {feed_id}: {e}")
            self.stats['errors'] += 1
    
    def _process_entry(self, entry: FeedEntry, feed_config: Dict):
        """Process a feed entry with AI filtering.
        
        Args:
            entry: FeedEntry to process
            feed_config: Feed configuration
        """
        try:
            print(f"   📰 {entry.title[:80]}...")
            
            # If AI filtering is disabled, save directly
            if not self.use_ai_filter or not self.ai_engine or not self.scraper:
                print(f"      ⏭️  Skipping AI filter (disabled)")
                return
            
            # Scrape full content
            scraped = self.scraper.scrape_url(entry.link)
            
            if not scraped.success:
                logger.warning(f"Failed to scrape {entry.link}")
                print(f"      ⚠️  Failed to scrape content")
                return
            
            # Use AI to analyze content
            print(f"      🤖 Analyzing with NuExtract AI...")
            
            # Build content for AI
            content_dict = {
                'title': scraped.title,
                'content': scraped.content[:1500],  # Limit content length
                'url': entry.link,
                'domain': scraped.domain
            }
            
            # Extract event data with AI
            try:
                event = self.ai_engine.analyze_article_blockchain(content_dict)
                
                if not event:
                    print(f"      ⏭️  No event detected")
                    self.stats['filtered_entries'] += 1
                    return
                
                # Check AI confidence if available
                confidence = getattr(event, 'ai_confidence', 0.0)
                if confidence < self.min_ai_confidence:
                    print(f"      ⏭️  Low confidence ({confidence:.2f})")
                    self.stats['filtered_entries'] += 1
                    return
                
                # This is an important event!
                print(f"      ✅ Important event detected! (confidence: {confidence:.2f})")
                print(f"         Title: {event.title}")
                print(f"         Category: {event.category}")
                
                self.stats['important_events'] += 1
                
                # Save to database
                if self.database:
                    event_data = {
                        'market_id': event.market_id,
                        'title': event.title,
                        'description': event.description,
                        'category': event.category,
                        'source_url': entry.link,
                        'freeze_date': event.freeze_date,
                        'resolution_date': event.resolution_date,
                        'yes_prob': event.yes_prob,
                        'no_prob': event.no_prob,
                        'no_change_prob': event.no_change_prob,
                        'status': 'pending',
                        'raw_content': scraped.content[:2000],
                        'ai_confidence': confidence
                    }
                    
                    event_id = self.database.save_event(event_data)
                    print(f"         💾 Saved to database (ID: {event_id})")
                    
                    # Log scrape history
                    self.database.log_scrape(
                        url=entry.link,
                        success=True,
                        event_id=event_id,
                        processing_time_ms=scraped.metadata.get('processing_time_ms')
                    )
            
            except Exception as e:
                logger.error(f"AI analysis error: {e}")
                print(f"      ❌ AI analysis failed: {e}")
                self.stats['filtered_entries'] += 1
        
        except Exception as e:
            logger.error(f"Error processing entry: {e}")
            print(f"      ❌ Processing error: {e}")
    
    def get_stats(self) -> Dict:
        """Get monitoring statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            **self.stats,
            'feeds_monitored': len(self.feeds),
            'is_running': self.is_running,
            'seen_entries': len(self.seen_entries)
        }
    
    def add_feed(self, feed_id: str, feed_config: Dict):
        """Add a new feed to monitor.
        
        Args:
            feed_id: Unique feed identifier
            feed_config: Feed configuration
        """
        self.feeds[feed_id] = feed_config
        logger.info(f"Added feed: {feed_config['name']}")
    
    def remove_feed(self, feed_id: str):
        """Remove a feed from monitoring.
        
        Args:
            feed_id: Feed identifier to remove
        """
        if feed_id in self.feeds:
            feed_name = self.feeds[feed_id]['name']
            del self.feeds[feed_id]
            logger.info(f"Removed feed: {feed_name}")
    
    def list_feeds(self) -> List[Dict]:
        """List all monitored feeds.
        
        Returns:
            List of feed configurations
        """
        return [
            {
                'id': feed_id,
                **config
            }
            for feed_id, config in self.feeds.items()
        ]


# Singleton instance
_monitor_instance: Optional[FeedMonitor] = None

def get_monitor(**kwargs) -> FeedMonitor:
    """Get or create feed monitor instance.
    
    Args:
        **kwargs: Arguments for FeedMonitor initialization
        
    Returns:
        FeedMonitor instance
    """
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = FeedMonitor(**kwargs)
    return _monitor_instance


def start_monitoring(database=None, scraper=None, ai_engine=None):
    """Start feed monitoring in the background.
    
    Args:
        database: Database instance
        scraper: Scraper instance
        ai_engine: LlamaEngine instance
    """
    monitor = get_monitor(
        database=database,
        scraper=scraper,
        ai_engine=ai_engine
    )
    monitor.start()
    return monitor


def stop_monitoring():
    """Stop feed monitoring."""
    global _monitor_instance
    if _monitor_instance:
        _monitor_instance.stop()
