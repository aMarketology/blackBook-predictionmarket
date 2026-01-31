"""
World Cup 2026 Feed Monitor
===========================
Real-time monitoring system for FIFA World Cup news sources.
Automatically detects newsworthy events and triggers content generation.
"""

import asyncio
import feedparser
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import hashlib
import json
import re
from dataclasses import dataclass

@dataclass
class NewsAlert:
    """Structure for news alerts from monitored sources."""
    headline: str
    source: str
    url: str
    content_preview: str
    urgency: str  # 'low', 'medium', 'high', 'urgent'
    category: str  # 'transfer', 'injury', 'match', 'controversy', 'investigation'
    teams_mentioned: List[str]
    timestamp: datetime
    confidence_score: float  # AI confidence in newsworthiness (0-1)

class WorldCupFeedMonitor:
    """
    Comprehensive monitoring system for World Cup 2026 news sources.
    
    Features:
    - Real-time RSS feed monitoring
    - Social media trend detection
    - Breaking news identification
    - Source verification and fact-checking
    - Automated content generation triggers
    """
    
    def __init__(self):
        self.monitored_feeds = self._load_world_cup_feeds()
        self.seen_articles = set()  # Track processed articles
        self.alert_handlers = []  # Callback functions for news alerts
        self.running = False
        
    def _load_world_cup_feeds(self) -> Dict[str, Dict]:
        """Load comprehensive list of World Cup news sources."""
        
        return {
            # FIFA Official Sources
            "fifa_official": {
                "url": "https://www.fifa.com/rss-feeds/news",
                "name": "FIFA Official",
                "priority": "urgent",
                "check_interval": 300,  # 5 minutes
                "categories": ["official", "tournament", "matches"],
                "reliability": 1.0
            },
            
            "fifa_worldcup": {
                "url": "https://www.fifa.com/fifaplus/en/tournaments/mens/worldcup/canadamexicousa2026",
                "name": "FIFA World Cup 2026 Official",
                "priority": "urgent", 
                "check_interval": 300,
                "categories": ["official", "tournament"],
                "reliability": 1.0
            },
            
            # Major Sports News
            "espn_soccer": {
                "url": "https://www.espn.com/espn/rss/soccer/news",
                "name": "ESPN Soccer",
                "priority": "high",
                "check_interval": 600,  # 10 minutes
                "categories": ["news", "transfers", "matches"],
                "reliability": 0.9
            },
            
            "bbc_football": {
                "url": "http://feeds.bbci.co.uk/sport/football/rss.xml",
                "name": "BBC Football",
                "priority": "high",
                "check_interval": 600,
                "categories": ["news", "analysis"],
                "reliability": 0.95
            },
            
            "sky_sports_football": {
                "url": "http://www1.skysports.com/rss/0,20514,11661,00.xml",
                "name": "Sky Sports Football",
                "priority": "high",
                "check_interval": 900,  # 15 minutes
                "categories": ["news", "transfers"],
                "reliability": 0.85
            },
            
            # Specialized Football Media
            "goal_com": {
                "url": "https://www.goal.com/feeds/news?fmt=rss&id=2",
                "name": "Goal.com",
                "priority": "medium",
                "check_interval": 1200,  # 20 minutes
                "categories": ["transfers", "rumors"],
                "reliability": 0.7
            },
            
            "football_insider": {
                "url": "https://www.football-italia.net/rss.xml",
                "name": "Football Italia",
                "priority": "medium",
                "check_interval": 1800,  # 30 minutes
                "categories": ["transfers", "tactical"],
                "reliability": 0.75
            },
            
            # News Wires (High Reliability)
            "reuters_sports": {
                "url": "http://feeds.reuters.com/reuters/sportsNews",
                "name": "Reuters Sports",
                "priority": "urgent",
                "check_interval": 600,
                "categories": ["breaking", "investigation"],
                "reliability": 0.98
            },
            
            "ap_sports": {
                "url": "https://apnews.com/apf-sports",
                "name": "Associated Press Sports",
                "priority": "urgent", 
                "check_interval": 600,
                "categories": ["breaking", "official"],
                "reliability": 0.98
            },
            
            # World Cup Host Countries
            "usa_soccer": {
                "url": "https://www.ussoccer.com/rss",
                "name": "US Soccer Federation",
                "priority": "high",
                "check_interval": 900,
                "categories": ["team_usa", "host_country"],
                "reliability": 0.9
            },
            
            "canada_soccer": {
                "url": "https://www.canadasoccer.com/feeds/news/",
                "name": "Canada Soccer",
                "priority": "high",
                "check_interval": 900, 
                "categories": ["team_canada", "host_country"],
                "reliability": 0.9
            },
            
            "mexican_soccer": {
                "url": "https://www.fmf.com.mx/rss/noticias",
                "name": "FMF (Mexico Football)",
                "priority": "high",
                "check_interval": 900,
                "categories": ["team_mexico", "host_country"],
                "reliability": 0.9
            },
            
            # Major National Teams
            "england_fa": {
                "url": "http://www.thefa.com/TheFA/RSS",
                "name": "England FA",
                "priority": "medium",
                "check_interval": 1800,
                "categories": ["team_england"],
                "reliability": 0.85
            },
            
            "brazil_cbf": {
                "url": "https://www.cbf.com.br/rss/noticias",
                "name": "Brazil CBF",
                "priority": "high",
                "check_interval": 1200,
                "categories": ["team_brazil"],
                "reliability": 0.85
            },
            
            "argentina_afa": {
                "url": "https://www.afa.com.ar/rss",
                "name": "Argentina AFA",
                "priority": "high",
                "check_interval": 1200,
                "categories": ["team_argentina"],
                "reliability": 0.85
            },
            
            # Business & Economics
            "bloomberg_sports": {
                "url": "https://feeds.bloomberg.com/sports/news.rss",
                "name": "Bloomberg Sports Business",
                "priority": "medium",
                "check_interval": 1800,
                "categories": ["business", "economics"],
                "reliability": 0.9
            },
            
            "sportsbusiness": {
                "url": "https://www.sportsbusinessdaily.com/rss",
                "name": "Sports Business Daily",
                "priority": "medium",
                "check_interval": 3600,  # 1 hour
                "categories": ["business", "sponsorship"],
                "reliability": 0.8
            },
            
            # Investigation Sources
            "the_athletic": {
                "url": "https://theathletic.com/rss/",
                "name": "The Athletic",
                "priority": "high",
                "check_interval": 1200,
                "categories": ["investigation", "analysis"],
                "reliability": 0.9
            },
            
            "guardian_football": {
                "url": "https://www.theguardian.com/football/rss",
                "name": "The Guardian Football",
                "priority": "high", 
                "check_interval": 900,
                "categories": ["investigation", "analysis"],
                "reliability": 0.95
            }
        }
    
    async def start_monitoring(self):
        """Start the feed monitoring system."""
        
        print("🚀 Starting World Cup 2026 feed monitoring...")
        print(f"📡 Monitoring {len(self.monitored_feeds)} news sources")
        
        self.running = True
        
        # Create monitoring tasks for each feed
        tasks = []
        for feed_id, feed_config in self.monitored_feeds.items():
            task = asyncio.create_task(
                self._monitor_feed(feed_id, feed_config)
            )
            tasks.append(task)
        
        # Run all monitoring tasks concurrently
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("\n⏹️ Stopping feed monitoring...")
            self.running = False
    
    async def _monitor_feed(self, feed_id: str, config: Dict):
        """Monitor a single RSS feed for updates."""
        
        check_interval = config["check_interval"]
        feed_name = config["name"]
        
        print(f"📡 Started monitoring: {feed_name} (every {check_interval//60}min)")
        
        while self.running:
            try:
                # Fetch and parse RSS feed
                feed_data = await self._fetch_rss_feed(config["url"])
                
                if feed_data:
                    # Process new articles
                    new_articles = await self._process_feed_articles(
                        feed_data, feed_id, config
                    )
                    
                    # Generate alerts for newsworthy content
                    for article in new_articles:
                        alert = await self._analyze_article_newsworthiness(
                            article, config
                        )
                        
                        if alert and alert.urgency in ['medium', 'high', 'urgent']:
                            await self._trigger_alert(alert)
                
                # Wait before next check
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                print(f"❌ Error monitoring {feed_name}: {str(e)}")
                # Wait before retrying
                await asyncio.sleep(60)
    
    async def _fetch_rss_feed(self, url: str) -> Optional[Dict]:
        """Fetch and parse RSS feed."""
        
        try:
            # Use feedparser for RSS feeds
            feed = feedparser.parse(url)
            
            if feed.bozo:
                print(f"⚠️ RSS feed parsing warning for {url}")
            
            return {
                "title": feed.feed.get("title", "Unknown"),
                "link": feed.feed.get("link", ""),
                "description": feed.feed.get("description", ""),
                "entries": feed.entries[:10]  # Latest 10 articles
            }
            
        except Exception as e:
            print(f"❌ Failed to fetch RSS feed {url}: {str(e)}")
            return None
    
    async def _process_feed_articles(
        self, 
        feed_data: Dict, 
        feed_id: str, 
        config: Dict
    ) -> List[Dict]:
        """Process articles from RSS feed."""
        
        new_articles = []
        
        for entry in feed_data["entries"]:
            # Create unique identifier for article
            article_id = hashlib.md5(
                f"{entry.get('link', '')}{entry.get('title', '')}".encode()
            ).hexdigest()
            
            # Skip if already processed
            if article_id in self.seen_articles:
                continue
                
            # Mark as seen
            self.seen_articles.add(article_id)
            
            # Extract article data
            article = {
                "id": article_id,
                "feed_id": feed_id,
                "source": config["name"],
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "description": entry.get("description", ""),
                "published": entry.get("published_parsed"),
                "tags": [tag.get("term", "") for tag in entry.get("tags", [])],
                "content": entry.get("content", [{}])[0].get("value", ""),
                "reliability": config["reliability"]
            }
            
            new_articles.append(article)
        
        return new_articles
    
    async def _analyze_article_newsworthiness(
        self, 
        article: Dict, 
        feed_config: Dict
    ) -> Optional[NewsAlert]:
        """Analyze if article is newsworthy for World Cup coverage."""
        
        title = article["title"].lower()
        description = article["description"].lower()
        content = f"{title} {description}"
        
        # World Cup related keywords
        world_cup_keywords = [
            "world cup", "fifa", "2026", "canada", "mexico", "usa",
            "tournament", "qualification", "qualifier"
        ]
        
        # High-priority keywords
        urgent_keywords = [
            "breaking", "injured", "suspended", "banned", "corruption",
            "investigation", "scandal", "dies", "arrested", "fired"
        ]
        
        # Medium-priority keywords  
        important_keywords = [
            "transfer", "signing", "contract", "manager", "coach",
            "lineup", "squad", "injury", "return"
        ]
        
        # Check World Cup relevance
        world_cup_score = sum(1 for keyword in world_cup_keywords if keyword in content)
        if world_cup_score == 0:
            return None  # Not World Cup related
        
        # Calculate urgency
        urgent_score = sum(1 for keyword in urgent_keywords if keyword in content)
        important_score = sum(1 for keyword in important_keywords if keyword in content)
        
        if urgent_score > 0:
            urgency = "urgent"
            confidence = 0.9
        elif important_score > 0:
            urgency = "high" if feed_config["priority"] == "urgent" else "medium"
            confidence = 0.7
        elif world_cup_score >= 2:
            urgency = "medium"
            confidence = 0.5
        else:
            urgency = "low"
            confidence = 0.3
        
        # Extract mentioned teams
        teams = self._extract_team_mentions(content)
        
        # Categorize content
        category = self._categorize_content(content)
        
        return NewsAlert(
            headline=article["title"],
            source=article["source"],
            url=article["link"],
            content_preview=article["description"][:200],
            urgency=urgency,
            category=category,
            teams_mentioned=teams,
            timestamp=datetime.now(),
            confidence_score=confidence
        )
    
    def _extract_team_mentions(self, content: str) -> List[str]:
        """Extract team/country mentions from content."""
        
        # Major World Cup teams
        teams = [
            "argentina", "brazil", "germany", "spain", "france", "england",
            "portugal", "netherlands", "italy", "belgium", "croatia",
            "mexico", "usa", "canada", "japan", "south korea", "australia"
        ]
        
        mentioned_teams = []
        for team in teams:
            if team in content.lower():
                mentioned_teams.append(team.title())
                
        return mentioned_teams
    
    def _categorize_content(self, content: str) -> str:
        """Categorize news content."""
        
        if any(word in content for word in ["transfer", "signing", "contract"]):
            return "transfer"
        elif any(word in content for word in ["injured", "injury", "hurt"]):
            return "injury"  
        elif any(word in content for word in ["match", "game", "fixture"]):
            return "match"
        elif any(word in content for word in ["corruption", "investigation", "scandal"]):
            return "investigation"
        elif any(word in content for word in ["controversial", "controversy", "dispute"]):
            return "controversy"
        else:
            return "general"
    
    async def _trigger_alert(self, alert: NewsAlert):
        """Trigger alert for newsworthy content."""
        
        print(f"\n🚨 {alert.urgency.upper()} ALERT: {alert.headline}")
        print(f"   Source: {alert.source}")
        print(f"   Category: {alert.category}")
        print(f"   Teams: {', '.join(alert.teams_mentioned) if alert.teams_mentioned else 'None'}")
        print(f"   Confidence: {alert.confidence_score:.1%}")
        print(f"   URL: {alert.url}")
        
        # Call registered alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                print(f"❌ Error in alert handler: {str(e)}")
    
    def add_alert_handler(self, handler_func):
        """Add callback function for news alerts."""
        self.alert_handlers.append(handler_func)
    
    def get_monitoring_stats(self) -> Dict:
        """Get monitoring statistics."""
        
        return {
            "feeds_monitored": len(self.monitored_feeds),
            "articles_processed": len(self.seen_articles),
            "monitoring_active": self.running,
            "last_updated": datetime.now().isoformat()
        }


# World Cup specific monitoring configurations
class WorldCupAlertManager:
    """Manages World Cup specific alerts and content generation triggers."""
    
    def __init__(self, content_generator=None, publisher=None):
        self.content_generator = content_generator
        self.publisher = publisher
        self.alert_history = []
        
    async def handle_urgent_alert(self, alert: NewsAlert):
        """Handle urgent World Cup alerts."""
        
        self.alert_history.append(alert)
        
        print(f"🔥 URGENT: Processing {alert.headline}")
        
        if alert.category == "investigation" and self.content_generator:
            # Generate investigation article
            await self._generate_investigation_article(alert)
            
        elif alert.urgency == "urgent" and self.publisher:
            # Publish breaking news immediately
            await self._publish_breaking_news(alert)
            
        elif alert.category == "transfer" and len(alert.teams_mentioned) > 0:
            # Generate transfer analysis
            await self._generate_transfer_analysis(alert)
    
    async def _generate_investigation_article(self, alert: NewsAlert):
        """Generate investigation article based on alert."""
        
        print(f"📝 Generating investigation article: {alert.headline}")
        
        # TODO: Implement investigation article generation
        # This would use the content generator to create a full investigation
        # piece based on the alert information
        
    async def _publish_breaking_news(self, alert: NewsAlert):
        """Publish breaking news based on alert."""
        
        print(f"📰 Publishing breaking news: {alert.headline}")
        
        # TODO: Implement breaking news publishing
        # This would immediately publish to objectwire.org
        
    async def _generate_transfer_analysis(self, alert: NewsAlert):
        """Generate transfer analysis article."""
        
        print(f"⚽ Generating transfer analysis: {alert.headline}")
        
        # TODO: Implement transfer analysis generation


# Example usage and testing
async def test_world_cup_monitoring():
    """Test the World Cup monitoring system."""
    
    monitor = WorldCupFeedMonitor()
    alert_manager = WorldCupAlertManager()
    
    # Add alert handler
    monitor.add_alert_handler(alert_manager.handle_urgent_alert)
    
    print("🏆 Starting World Cup 2026 monitoring test...")
    print("Press Ctrl+C to stop\n")
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n✅ Monitoring test completed")
        
        # Show stats
        stats = monitor.get_monitoring_stats()
        print(f"📊 Articles processed: {stats['articles_processed']}")
        print(f"📡 Feeds monitored: {stats['feeds_monitored']}")


if __name__ == "__main__":
    # Run monitoring test
    asyncio.run(test_world_cup_monitoring())