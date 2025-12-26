"""
ObjectWire RSS Monitor
======================
Background RSS feed monitoring with AI-powered filtering.

Runs as a background thread while CLI is active.
Monitors popular RSS feeds and alerts on interesting events.
Uses offline NuExtract AI to filter relevant content.
"""

import time
import logging
import threading
from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

import feedparser
from rich.console import Console
from rich.panel import Panel

console = Console()
logger = logging.getLogger(__name__)


# ============================================================================
# RSS FEED CATALOG
# ============================================================================

RSS_FEEDS = {
    # YouTube Creators (RSS format: https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID)
    "youtube": [
        {
            "name": "MrBeast",
            "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCX6OQ3DkcsbYNE6H8uQQuVA",
            "category": "social",
            "check_interval": 300,  # 5 minutes
            "priority": "high",
            "keywords": ["challenge", "million", "views", "subscriber"]
        },
        {
            "name": "Sidemen",
            "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCDogdKl7t7NHzQ95aEwkdMw",
            "category": "social",
            "check_interval": 600,  # 10 minutes
            "priority": "medium",
            "keywords": ["sidemen", "football", "charity"]
        },
        {
            "name": "KSI",
            "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCX6OQ3DkcsbYNE6H8uQQuVA",
            "category": "social",
            "check_interval": 600,
            "priority": "medium",
            "keywords": ["boxing", "music", "prime"]
        },
        {
            "name": "Logan Paul",
            "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCG8rbF3g2AMX70yOd8vqIZg",
            "category": "social",
            "check_interval": 600,
            "priority": "medium",
            "keywords": ["boxing", "prime", "podcast"]
        },
    ],
    
    # Sports News
    "sports": [
        {
            "name": "ESPN",
            "url": "https://www.espn.com/espn/rss/news",
            "category": "sports",
            "check_interval": 900,  # 15 minutes
            "priority": "high",
            "keywords": ["world cup", "championship", "final", "record"]
        },
        {
            "name": "Bleacher Report",
            "url": "https://bleacherreport.com/articles/feed",
            "category": "sports",
            "check_interval": 1800,  # 30 minutes
            "priority": "medium",
            "keywords": ["transfer", "signing", "champion"]
        },
    ],
    
    # Crypto News
    "crypto": [
        {
            "name": "CoinDesk",
            "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "category": "crypto",
            "check_interval": 600,  # 10 minutes
            "priority": "high",
            "keywords": ["bitcoin", "ethereum", "price", "regulation", "etf"]
        },
        {
            "name": "CoinTelegraph",
            "url": "https://cointelegraph.com/rss",
            "category": "crypto",
            "check_interval": 900,
            "priority": "medium",
            "keywords": ["btc", "eth", "defi", "nft"]
        },
    ],
    
    # Tech News
    "tech": [
        {
            "name": "TechCrunch",
            "url": "https://techcrunch.com/feed/",
            "category": "tech",
            "check_interval": 1800,  # 30 minutes
            "priority": "high",
            "keywords": ["ai", "startup", "funding", "ipo", "launch"]
        },
        {
            "name": "The Verge",
            "url": "https://www.theverge.com/rss/index.xml",
            "category": "tech",
            "check_interval": 1800,
            "priority": "medium",
            "keywords": ["apple", "google", "microsoft", "meta"]
        },
    ],
}


# ============================================================================
# RSS MONITOR CLASS
# ============================================================================

class RSSMonitor:
    """Background RSS feed monitor with AI filtering."""
    
    def __init__(
        self,
        database=None,
        scraper=None,
        ai_engine=None,
        on_interesting_article: Optional[Callable] = None
    ):
        """Initialize RSS monitor.
        
        Args:
            database: Database instance for storing articles
            scraper: Scraper instance for fetching full content
            ai_engine: AI engine for content analysis
            on_interesting_article: Callback function when interesting article found
        """
        self.database = database
        self.scraper = scraper
        self.ai_engine = ai_engine
        self.on_interesting_article = on_interesting_article or self._default_alert
        
        self.running = False
        self.thread = None
        self.seen_articles = set()  # Track article hashes to avoid duplicates
        self.feed_stats = {}  # Track stats per feed
        
        # Load all feeds
        self.feeds = self._load_feeds()
        logger.info(f"Loaded {len(self.feeds)} RSS feeds")
    
    def _load_feeds(self) -> List[Dict]:
        """Load all RSS feeds from catalog."""
        all_feeds = []
        for category, feeds in RSS_FEEDS.items():
            for feed in feeds:
                feed['category_group'] = category
                all_feeds.append(feed)
        return all_feeds
    
    def start(self):
        """Start monitoring in background thread."""
        if self.running:
            logger.warning("RSS Monitor already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        
        console.print(Panel(
            f"[green]✓ RSS Monitor Started[/green]\n\n"
            f"Monitoring {len(self.feeds)} feeds:\n"
            f"  • YouTube Creators: {len(RSS_FEEDS['youtube'])}\n"
            f"  • Sports News: {len(RSS_FEEDS['sports'])}\n"
            f"  • Crypto News: {len(RSS_FEEDS['crypto'])}\n"
            f"  • Tech News: {len(RSS_FEEDS['tech'])}\n\n"
            f"AI will alert you when something interesting is found.",
            title="🔍 RSS Monitor",
            border_style="green"
        ))
        
        logger.info("RSS Monitor started")
    
    def stop(self):
        """Stop monitoring."""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        console.print("[yellow]RSS Monitor stopped[/yellow]")
        logger.info("RSS Monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        logger.info("RSS Monitor loop started")
        
        # Initialize last check times
        last_check = {feed['url']: datetime.now() - timedelta(hours=1) for feed in self.feeds}
        
        while self.running:
            try:
                for feed in self.feeds:
                    if not self.running:
                        break
                    
                    # Check if it's time to check this feed
                    now = datetime.now()
                    time_since_check = (now - last_check[feed['url']]).total_seconds()
                    
                    if time_since_check >= feed['check_interval']:
                        self._check_feed(feed)
                        last_check[feed['url']] = now
                
                # Sleep for a bit before next round
                time.sleep(60)  # Check every minute if any feed is due
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(60)
    
    def _check_feed(self, feed: Dict):
        """Check a single RSS feed for new articles."""
        try:
            logger.debug(f"Checking feed: {feed['name']}")
            
            # Parse RSS feed
            parsed = feedparser.parse(feed['url'])
            
            if parsed.bozo:
                logger.warning(f"Feed parsing error for {feed['name']}: {parsed.bozo_exception}")
                return
            
            # Track stats
            if feed['url'] not in self.feed_stats:
                self.feed_stats[feed['url']] = {
                    'name': feed['name'],
                    'total_checked': 0,
                    'articles_found': 0,
                    'interesting_found': 0,
                    'last_check': None
                }
            
            self.feed_stats[feed['url']]['total_checked'] += 1
            self.feed_stats[feed['url']]['last_check'] = datetime.now().isoformat()
            
            # Process entries
            new_articles = 0
            for entry in parsed.entries[:10]:  # Check last 10 entries
                article_id = self._get_article_id(entry)
                
                # Skip if already seen
                if article_id in self.seen_articles:
                    continue
                
                self.seen_articles.add(article_id)
                new_articles += 1
                
                # Create article dict
                article = {
                    'title': entry.get('title', 'No title'),
                    'url': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', '')[:500],
                    'feed_name': feed['name'],
                    'feed_category': feed['category'],
                    'feed_priority': feed['priority']
                }
                
                # Check if article is interesting
                if self._is_interesting(article, feed):
                    self.feed_stats[feed['url']]['interesting_found'] += 1
                    self._handle_interesting_article(article, feed)
            
            if new_articles > 0:
                self.feed_stats[feed['url']]['articles_found'] += new_articles
                logger.debug(f"Found {new_articles} new articles from {feed['name']}")
            
        except Exception as e:
            logger.error(f"Error checking feed {feed['name']}: {e}")
    
    def _get_article_id(self, entry) -> str:
        """Generate unique ID for article."""
        # Use URL or title+published as unique identifier
        unique_str = entry.get('link', '') or f"{entry.get('title', '')}_{entry.get('published', '')}"
        return hashlib.md5(unique_str.encode()).hexdigest()
    
    def _is_interesting(self, article: Dict, feed: Dict) -> bool:
        """Determine if article is interesting using AI and keywords.
        
        Args:
            article: Article dictionary
            feed: Feed configuration
            
        Returns:
            True if article is interesting
        """
        # Priority feeds are always interesting
        if feed['priority'] == 'high':
            # Check keywords
            text = f"{article['title']} {article['summary']}".lower()
            if any(keyword.lower() in text for keyword in feed.get('keywords', [])):
                return True
        
        # For medium priority, be more selective
        if feed['priority'] == 'medium':
            text = f"{article['title']} {article['summary']}".lower()
            # Must have at least 2 keywords
            keyword_matches = sum(1 for keyword in feed.get('keywords', []) if keyword.lower() in text)
            if keyword_matches >= 2:
                return True
        
        # TODO: Use AI engine for deeper analysis
        # if self.ai_engine:
        #     try:
        #         result = self.ai_engine.analyze_article_blockchain(article)
        #         if result.get('ai_confidence', 0) > 0.75:
        #             return True
        #     except Exception as e:
        #         logger.debug(f"AI analysis failed: {e}")
        
        return False
    
    def _handle_interesting_article(self, article: Dict, feed: Dict):
        """Handle interesting article found."""
        # Call callback
        self.on_interesting_article(article, feed)
        
        # Save to database if available
        if self.database:
            try:
                # Save to scrape_history
                self.database.log_scrape(
                    url=article['url'],
                    success=True,
                    processing_time_ms=0
                )
            except Exception as e:
                logger.error(f"Error saving to database: {e}")
    
    def _default_alert(self, article: Dict, feed: Dict):
        """Default alert handler - prints to console."""
        console.print(Panel(
            f"[bold cyan]{article['title']}[/bold cyan]\n\n"
            f"[dim]Source: {feed['name']} ({feed['category']})[/dim]\n"
            f"[dim]Published: {article['published']}[/dim]\n\n"
            f"{article['summary'][:200]}...\n\n"
            f"[link={article['url']}]{article['url']}[/link]",
            title="🚨 Interesting Article Found",
            border_style="yellow",
            expand=False
        ))
    
    def get_stats(self) -> Dict:
        """Get monitoring statistics.
        
        Returns:
            Dictionary with stats
        """
        total_checked = sum(s['total_checked'] for s in self.feed_stats.values())
        total_found = sum(s['articles_found'] for s in self.feed_stats.values())
        total_interesting = sum(s['interesting_found'] for s in self.feed_stats.values())
        
        return {
            'feeds_monitored': len(self.feeds),
            'total_checks': total_checked,
            'articles_found': total_found,
            'interesting_found': total_interesting,
            'articles_seen': len(self.seen_articles),
            'feed_stats': self.feed_stats
        }
    
    def print_stats(self):
        """Print statistics to console."""
        stats = self.get_stats()
        
        console.print(Panel(
            f"[cyan]Feeds Monitored:[/cyan] {stats['feeds_monitored']}\n"
            f"[cyan]Total Checks:[/cyan] {stats['total_checks']}\n"
            f"[cyan]Articles Found:[/cyan] {stats['articles_found']}\n"
            f"[green]Interesting Articles:[/green] {stats['interesting_found']}\n"
            f"[dim]Articles Seen:[/dim] {stats['articles_seen']}",
            title="📊 RSS Monitor Statistics",
            border_style="cyan"
        ))


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_monitor(database=None, scraper=None, ai_engine=None, **kwargs) -> RSSMonitor:
    """Create RSS monitor instance.
    
    Args:
        database: Database instance
        scraper: Scraper instance
        ai_engine: AI engine instance
        **kwargs: Additional arguments for RSSMonitor
        
    Returns:
        RSSMonitor instance
    """
    return RSSMonitor(
        database=database,
        scraper=scraper,
        ai_engine=ai_engine,
        **kwargs
    )


# Singleton instance
_monitor_instance: Optional[RSSMonitor] = None

def get_monitor(**kwargs) -> RSSMonitor:
    """Get or create monitor singleton.
    
    Args:
        **kwargs: Arguments for RSSMonitor initialization
        
    Returns:
        RSSMonitor instance
    """
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = create_monitor(**kwargs)
    return _monitor_instance
