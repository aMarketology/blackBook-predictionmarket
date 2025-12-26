"""
ObjectWire Database Layer
=========================
SQLite database for storing events, scraping history, and creator metrics.

Schema:
- events: Prediction market events with blockchain fields
- scrape_history: Track all scraping attempts
- creators: Social media creator database
"""

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager for ObjectWire."""
    
    def __init__(self, db_path: str = "objectwire.db"):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file (default: objectwire.db)
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dicts
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Events table - stores all prediction market events
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    market_id TEXT UNIQUE NOT NULL,
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
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    blockchain_tx_id TEXT,
                    article_generated BOOLEAN DEFAULT 0,
                    article_path TEXT,
                    raw_content TEXT,
                    ai_confidence REAL
                )
            """)
            
            # Scrape history - track all scraping attempts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scrape_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    event_id INTEGER,
                    processing_time_ms INTEGER,
                    FOREIGN KEY (event_id) REFERENCES events(id)
                )
            """)
            
            # Creators table - social media creator tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS creators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    platform_id TEXT,
                    followers INTEGER,
                    avg_engagement REAL,
                    total_events INTEGER DEFAULT 0,
                    tracked_since TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    UNIQUE(platform, platform_id)
                )
            """)
            
            # RSS feeds table - tracked feeds
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rss_feeds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT,
                    category TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    check_interval_minutes INTEGER DEFAULT 30,
                    last_checked TIMESTAMP,
                    total_articles_found INTEGER DEFAULT 0,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_market_id ON events(market_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_status ON events(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_category ON events(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scrape_history_url ON scrape_history(url)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_creators_platform ON creators(platform)")
            
            logger.info(f"Database initialized at {self.db_path}")
    
    # ==================== EVENT OPERATIONS ====================
    
    def save_event(self, event: Dict[str, Any]) -> int:
        """Save a prediction event to the database.
        
        Args:
            event: Event dictionary with blockchain fields
            
        Returns:
            event_id: Database ID of created event
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO events (
                    market_id, title, description, category, source_url,
                    freeze_date, resolution_date, yes_prob, no_prob, no_change_prob,
                    status, raw_content, ai_confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.get('market_id'),
                event.get('title'),
                event.get('description'),
                event.get('category'),
                event.get('source_url'),
                event.get('freeze_date'),
                event.get('resolution_date'),
                event.get('yes_prob'),
                event.get('no_prob'),
                event.get('no_change_prob'),
                event.get('status', 'pending'),
                event.get('raw_content'),
                event.get('ai_confidence', 0.0)
            ))
            event_id = cursor.lastrowid
            logger.info(f"Saved event {event_id}: {event.get('title')}")
            return event_id
    
    def get_event(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Get event by market_id.
        
        Args:
            market_id: Unique market identifier
            
        Returns:
            Event dictionary or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE market_id = ?", (market_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_event_by_id(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Get event by database ID.
        
        Args:
            event_id: Database ID
            
        Returns:
            Event dictionary or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_events(
        self, 
        status: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List events with optional filtering.
        
        Args:
            status: Filter by status (pending, posted, resolved)
            category: Filter by category
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            List of event dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM events WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def update_event_status(
        self, 
        market_id: str, 
        status: str,
        blockchain_tx_id: Optional[str] = None
    ) -> bool:
        """Update event status and blockchain transaction ID.
        
        Args:
            market_id: Event market ID
            status: New status (pending, posted, resolved)
            blockchain_tx_id: Transaction ID from blockchain
            
        Returns:
            True if updated successfully
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE events 
                SET status = ?, blockchain_tx_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE market_id = ?
            """, (status, blockchain_tx_id, market_id))
            
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Updated event {market_id} status to {status}")
            return success
    
    def mark_article_generated(self, market_id: str, article_path: str) -> bool:
        """Mark that article was generated for this event.
        
        Args:
            market_id: Event market ID
            article_path: Path to generated article file
            
        Returns:
            True if updated successfully
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE events 
                SET article_generated = 1, article_path = ?, updated_at = CURRENT_TIMESTAMP
                WHERE market_id = ?
            """, (article_path, market_id))
            return cursor.rowcount > 0
    
    # ==================== SCRAPE HISTORY ====================
    
    def log_scrape(
        self,
        url: str,
        success: bool,
        event_id: Optional[int] = None,
        error_message: Optional[str] = None,
        processing_time_ms: Optional[int] = None
    ) -> int:
        """Log a scraping attempt.
        
        Args:
            url: URL that was scraped
            success: Whether scraping succeeded
            event_id: Associated event ID if successful
            error_message: Error message if failed
            processing_time_ms: Processing time in milliseconds
            
        Returns:
            scrape_history_id: Database ID of log entry
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scrape_history (
                    url, success, event_id, error_message, processing_time_ms
                ) VALUES (?, ?, ?, ?, ?)
            """, (url, success, event_id, error_message, processing_time_ms))
            return cursor.lastrowid
    
    def get_scrape_history(self, url: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get scrape history with optional URL filter.
        
        Args:
            url: Filter by specific URL (optional)
            limit: Maximum number of results
            
        Returns:
            List of scrape history entries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if url:
                cursor.execute("""
                    SELECT * FROM scrape_history 
                    WHERE url = ? 
                    ORDER BY scraped_at DESC 
                    LIMIT ?
                """, (url, limit))
            else:
                cursor.execute("""
                    SELECT * FROM scrape_history 
                    ORDER BY scraped_at DESC 
                    LIMIT ?
                """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== CREATOR OPERATIONS ====================
    
    def add_creator(
        self,
        name: str,
        platform: str,
        platform_id: str,
        followers: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """Add or update a creator.
        
        Args:
            name: Creator name
            platform: Platform (youtube, twitter, twitch, etc.)
            platform_id: Platform-specific ID
            followers: Follower count
            metadata: Additional metadata as dict
            
        Returns:
            creator_id: Database ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO creators (name, platform, platform_id, followers, metadata)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(platform, platform_id) DO UPDATE SET
                    name = excluded.name,
                    followers = excluded.followers,
                    metadata = excluded.metadata,
                    last_updated = CURRENT_TIMESTAMP
            """, (name, platform, platform_id, followers, metadata_json))
            
            return cursor.lastrowid
    
    def get_creator(self, platform: str, platform_id: str) -> Optional[Dict[str, Any]]:
        """Get creator by platform and ID.
        
        Args:
            platform: Platform name
            platform_id: Platform-specific ID
            
        Returns:
            Creator dictionary or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM creators 
                WHERE platform = ? AND platform_id = ?
            """, (platform, platform_id))
            row = cursor.fetchone()
            
            if row:
                creator = dict(row)
                if creator.get('metadata'):
                    creator['metadata'] = json.loads(creator['metadata'])
                return creator
            return None
    
    def list_creators(self, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all tracked creators.
        
        Args:
            platform: Filter by platform (optional)
            
        Returns:
            List of creator dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if platform:
                cursor.execute("""
                    SELECT * FROM creators 
                    WHERE platform = ? 
                    ORDER BY followers DESC
                """, (platform,))
            else:
                cursor.execute("""
                    SELECT * FROM creators 
                    ORDER BY followers DESC
                """)
            
            creators = []
            for row in cursor.fetchall():
                creator = dict(row)
                if creator.get('metadata'):
                    creator['metadata'] = json.loads(creator['metadata'])
                creators.append(creator)
            
            return creators
    
    # ==================== RSS FEED OPERATIONS ====================
    
    def add_feed(self, url: str, title: Optional[str] = None, category: Optional[str] = None) -> int:
        """Add RSS feed to watch list.
        
        Args:
            url: Feed URL
            title: Feed title
            category: Feed category
            
        Returns:
            feed_id: Database ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rss_feeds (url, title, category)
                VALUES (?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    title = excluded.title,
                    category = excluded.category
            """, (url, title, category))
            return cursor.lastrowid
    
    def list_feeds(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """List RSS feeds.
        
        Args:
            enabled_only: Only return enabled feeds
            
        Returns:
            List of feed dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if enabled_only:
                cursor.execute("SELECT * FROM rss_feeds WHERE enabled = 1")
            else:
                cursor.execute("SELECT * FROM rss_feeds")
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_feed_check(self, feed_id: int, articles_found: int):
        """Update feed last checked timestamp and article count.
        
        Args:
            feed_id: Feed database ID
            articles_found: Number of articles found in this check
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE rss_feeds 
                SET last_checked = CURRENT_TIMESTAMP,
                    total_articles_found = total_articles_found + ?
                WHERE id = ?
            """, (articles_found, feed_id))
    
    # ==================== STATISTICS ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics.
        
        Returns:
            Dictionary with various statistics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total events by status
            cursor.execute("SELECT status, COUNT(*) as count FROM events GROUP BY status")
            status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Total events by category
            cursor.execute("SELECT category, COUNT(*) as count FROM events GROUP BY category")
            category_counts = {row['category']: row['count'] for row in cursor.fetchall()}
            
            # Total scrapes
            cursor.execute("SELECT COUNT(*) as total FROM scrape_history")
            total_scrapes = cursor.fetchone()['total']
            
            # Success rate
            cursor.execute("SELECT COUNT(*) as successful FROM scrape_history WHERE success = 1")
            successful_scrapes = cursor.fetchone()['successful']
            success_rate = (successful_scrapes / total_scrapes * 100) if total_scrapes > 0 else 0
            
            # Total creators
            cursor.execute("SELECT COUNT(*) as total FROM creators")
            total_creators = cursor.fetchone()['total']
            
            # Total RSS feeds
            cursor.execute("SELECT COUNT(*) as total FROM rss_feeds WHERE enabled = 1")
            total_feeds = cursor.fetchone()['total']
            
            return {
                'events': {
                    'total': sum(status_counts.values()),
                    'by_status': status_counts,
                    'by_category': category_counts
                },
                'scrapes': {
                    'total': total_scrapes,
                    'successful': successful_scrapes,
                    'success_rate': round(success_rate, 2)
                },
                'creators': total_creators,
                'feeds': total_feeds
            }
    
    def export_events(self, output_file: str, status: Optional[str] = None):
        """Export events to JSON file.
        
        Args:
            output_file: Path to output JSON file
            status: Filter by status (optional)
        """
        events = self.list_events(status=status, limit=10000)
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(events, f, indent=2)
        
        logger.info(f"Exported {len(events)} events to {output_file}")


# Singleton instance
_db_instance: Optional[Database] = None

def get_db(db_path: str = "objectwire.db") -> Database:
    """Get or create database singleton instance.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        Database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_path)
    return _db_instance
