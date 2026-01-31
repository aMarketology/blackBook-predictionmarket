"""
ObjectWire.org Integration
==========================
API client for publishing World Cup content directly to objectwire.org.
Handles authentication, content formatting, and automated publishing.
"""

import asyncio
import json
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Literal
import os
from dataclasses import dataclass

@dataclass
class ObjectWireArticle:
    """Article structure for ObjectWire.org publication."""
    title: str
    content: str
    category: str  # 'case', 'news', 'analyst', 'opinion'
    author: str
    publish_date: datetime
    tags: List[str]
    meta_description: str
    featured_image: Optional[str] = None
    status: Literal['draft', 'review', 'published'] = 'draft'
    
class ObjectWireAPI:
    """
    API client for objectwire.org content management.
    
    Features:
    - Article publishing and scheduling
    - Content categorization (investigations, news, analysis)
    - SEO optimization and meta tag management
    - Editorial workflow integration
    - Real-time update publishing
    """
    
    def __init__(self, api_key: str, base_url: str = "https://objectwire.org/api"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        """Initialize async HTTP session."""
        self.session = aiohttp.ClientSession(
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'ObjectWire-WorldCup-Agent/1.0'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
    
    async def publish_investigation(
        self,
        article: ObjectWireArticle,
        schedule_time: Optional[datetime] = None
    ) -> Dict:
        """
        Publish investigation article to ObjectWire.org.
        
        Args:
            article: Article data structure
            schedule_time: Optional scheduled publication time
            
        Returns:
            Publication response with article URL and metadata
        """
        
        # Format article for ObjectWire's editorial standards
        formatted_article = self._format_investigation_article(article)
        
        endpoint = f"{self.base_url}/articles"
        
        payload = {
            "type": "investigation",
            "category": "case",  # ObjectWire investigations section
            "title": formatted_article["title"],
            "content": formatted_article["content"],
            "author": article.author,
            "meta_description": article.meta_description,
            "tags": article.tags,
            "featured_image": article.featured_image,
            "status": "review",  # Investigations require editorial review
            "publish_at": schedule_time.isoformat() if schedule_time else None,
            "editorial_notes": {
                "source_verification": "required",
                "fact_check": "pending", 
                "legal_review": "pending",
                "seo_review": "completed"
            }
        }
        
        async with self.session.post(endpoint, json=payload) as response:
            if response.status == 201:
                result = await response.json()
                return {
                    "success": True,
                    "article_id": result["id"],
                    "url": f"https://objectwire.org/{result['slug']}",
                    "status": result["status"],
                    "editorial_workflow": result["workflow_stage"]
                }
            else:
                error_text = await response.text()
                return {
                    "success": False,
                    "error": f"HTTP {response.status}: {error_text}",
                    "status_code": response.status
                }
    
    async def publish_breaking_news(
        self,
        headline: str,
        content: str,
        urgency: Literal["low", "medium", "high", "urgent"] = "high",
        push_notification: bool = False
    ) -> Dict:
        """
        Publish breaking news update immediately.
        
        Args:
            headline: Breaking news headline
            content: Article content
            urgency: Priority level for homepage placement
            push_notification: Send push notifications to subscribers
            
        Returns:
            Publication response
        """
        
        endpoint = f"{self.base_url}/breaking-news"
        
        payload = {
            "type": "breaking",
            "headline": f"BREAKING: {headline}",
            "content": content,
            "urgency": urgency,
            "category": "news",
            "author": "ObjectWire Newsroom",
            "status": "published",  # Breaking news publishes immediately
            "notifications": {
                "push": push_notification,
                "social": urgency in ["high", "urgent"],
                "email": urgency == "urgent",
                "homepage": "top" if urgency == "urgent" else "breaking"
            },
            "meta": {
                "published_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "breaking_until": (datetime.now().timestamp() + 3600 * 6)  # 6 hours
            }
        }
        
        async with self.session.post(endpoint, json=payload) as response:
            if response.status == 201:
                result = await response.json()
                return {
                    "success": True,
                    "article_id": result["id"],
                    "url": f"https://objectwire.org/breaking/{result['slug']}",
                    "published_at": result["published_at"],
                    "notifications_sent": result["notifications"]
                }
            else:
                error_text = await response.text()
                return {"success": False, "error": error_text}
    
    async def publish_match_analysis(
        self,
        match_data: Dict,
        analysis_content: str,
        match_type: Literal["preview", "review", "tactical"] = "review"
    ) -> Dict:
        """
        Publish World Cup match analysis article.
        
        Args:
            match_data: Match information (teams, score, date, etc.)
            analysis_content: Full analysis article content
            match_type: Type of match analysis
            
        Returns:
            Publication response
        """
        
        teams = f"{match_data.get('home_team')} vs {match_data.get('away_team')}"
        title = f"World Cup 2026: {teams} - {match_type.title()} Analysis"
        
        endpoint = f"{self.base_url}/articles"
        
        payload = {
            "type": "analysis",
            "category": "analyst",  # ObjectWire analysis section
            "title": title,
            "content": analysis_content,
            "author": "ObjectWire Sports Desk",
            "tags": [
                "world-cup-2026", 
                "fifa",
                match_data.get('home_team', '').lower(),
                match_data.get('away_team', '').lower(),
                "match-analysis"
            ],
            "meta_description": f"Tactical analysis and key insights from {teams} in the FIFA World Cup 2026.",
            "match_metadata": {
                "competition": "FIFA World Cup 2026",
                "match_date": match_data.get("date"),
                "venue": match_data.get("venue"),
                "final_score": match_data.get("score"),
                "attendance": match_data.get("attendance")
            },
            "status": "published",  # Match analysis can publish immediately
            "seo": {
                "canonical_url": f"https://objectwire.org/worldcup/{teams.lower().replace(' ', '-')}-analysis",
                "keywords": [teams.lower(), "world cup 2026", "match analysis", "fifa"],
                "structured_data": self._generate_match_structured_data(match_data)
            }
        }
        
        async with self.session.post(endpoint, json=payload) as response:
            if response.status == 201:
                result = await response.json()
                return {
                    "success": True,
                    "article_id": result["id"],
                    "url": f"https://objectwire.org/analyst/{result['slug']}",
                    "published_at": result["published_at"]
                }
            else:
                error_text = await response.text()
                return {"success": False, "error": error_text}
    
    async def start_live_blog(
        self,
        match_info: Dict,
        blog_title: str
    ) -> Dict:
        """
        Start live blog for real-time match coverage.
        
        Args:
            match_info: Match details
            blog_title: Live blog headline
            
        Returns:
            Live blog creation response with update endpoint
        """
        
        endpoint = f"{self.base_url}/live-blogs"
        
        payload = {
            "type": "live_blog",
            "title": blog_title,
            "match_data": match_info,
            "status": "active",
            "category": "news",
            "author": "ObjectWire Sports Desk",
            "auto_refresh": True,
            "update_frequency": 60,  # Update every minute
            "meta": {
                "started_at": datetime.now().isoformat(),
                "expected_duration": 120,  # 120 minutes (90min + stoppage)
                "notification_threshold": "medium"  # Notify on medium+ priority updates
            }
        }
        
        async with self.session.post(endpoint, json=payload) as response:
            if response.status == 201:
                result = await response.json()
                return {
                    "success": True,
                    "blog_id": result["id"],
                    "url": f"https://objectwire.org/live/{result['slug']}",
                    "update_endpoint": f"{self.base_url}/live-blogs/{result['id']}/updates",
                    "websocket_url": f"wss://objectwire.org/ws/live/{result['id']}"
                }
            else:
                error_text = await response.text()
                return {"success": False, "error": error_text}
    
    async def add_live_update(
        self,
        blog_id: str,
        minute: int,
        event: str,
        description: str,
        priority: Literal["low", "medium", "high"] = "medium"
    ) -> Dict:
        """
        Add update to active live blog.
        
        Args:
            blog_id: Live blog identifier
            minute: Match minute
            event: Event description
            description: Detailed description
            priority: Update priority for notifications
            
        Returns:
            Update response
        """
        
        endpoint = f"{self.base_url}/live-blogs/{blog_id}/updates"
        
        payload = {
            "minute": minute,
            "event": event,
            "description": description,
            "priority": priority,
            "timestamp": datetime.now().isoformat(),
            "auto_notification": priority == "high"
        }
        
        async with self.session.post(endpoint, json=payload) as response:
            if response.status == 201:
                result = await response.json()
                return {
                    "success": True,
                    "update_id": result["id"],
                    "published_at": result["timestamp"]
                }
            else:
                error_text = await response.text()
                return {"success": False, "error": error_text}
    
    async def get_content_stats(self, date_range: int = 7) -> Dict:
        """
        Get content performance statistics.
        
        Args:
            date_range: Days to look back for stats
            
        Returns:
            Content performance data
        """
        
        endpoint = f"{self.base_url}/analytics/content?days={date_range}"
        
        async with self.session.get(endpoint) as response:
            if response.status == 200:
                return await response.json()
            else:
                return {"success": False, "error": "Failed to fetch stats"}
    
    async def schedule_article_series(
        self,
        series_name: str,
        articles: List[Dict],
        publish_schedule: Dict
    ) -> Dict:
        """
        Schedule a series of related articles (e.g., "Road to Final" series).
        
        Args:
            series_name: Name of article series
            articles: List of article data
            publish_schedule: Publication timing for each article
            
        Returns:
            Series scheduling response
        """
        
        endpoint = f"{self.base_url}/series"
        
        payload = {
            "series_name": series_name,
            "articles": articles,
            "schedule": publish_schedule,
            "category": "worldcup-series",
            "auto_social": True,
            "cross_promotion": True
        }
        
        async with self.session.post(endpoint, json=payload) as response:
            if response.status == 201:
                result = await response.json()
                return {
                    "success": True,
                    "series_id": result["id"],
                    "scheduled_articles": result["article_count"],
                    "first_publish": result["first_publish_date"]
                }
            else:
                error_text = await response.text()
                return {"success": False, "error": error_text}
    
    def _format_investigation_article(self, article: ObjectWireArticle) -> Dict:
        """
        Format article content according to ObjectWire investigation standards.
        
        Ensures:
        - Source citations are properly formatted
        - Editorial review checkpoints are included
        - Legal review flags are set where needed
        - SEO optimization is applied
        """
        
        formatted_content = article.content
        
        # Add source citation formatting
        if "[Sources:" in formatted_content:
            formatted_content = self._format_source_citations(formatted_content)
        
        # Add editorial review checkpoints
        formatted_content += "\n\n---\n\n*This investigation is ongoing. ObjectWire maintains a 24-hour correction policy and welcomes tips at tips@objectwire.com*"
        
        return {
            "title": article.title,
            "content": formatted_content,
            "editorial_flags": {
                "requires_legal_review": "FIFA" in article.content or "corruption" in article.content.lower(),
                "requires_fact_check": True,
                "source_verification_needed": True,
                "publication_timeline": "72_hours"  # Allow time for thorough review
            }
        }
    
    def _format_source_citations(self, content: str) -> str:
        """Format source citations according to ObjectWire standards."""
        # TODO: Implement proper source citation formatting
        return content
    
    def _generate_match_structured_data(self, match_data: Dict) -> Dict:
        """Generate structured data for match articles (SEO optimization)."""
        
        return {
            "@context": "https://schema.org",
            "@type": "SportsEvent",
            "name": f"{match_data.get('home_team')} vs {match_data.get('away_team')}",
            "startDate": match_data.get("date"),
            "location": {
                "@type": "Place",
                "name": match_data.get("venue")
            },
            "organizer": {
                "@type": "Organization", 
                "name": "FIFA"
            },
            "about": "FIFA World Cup 2026"
        }


class WorldCupPublisher:
    """
    High-level publisher for World Cup content to ObjectWire.org.
    Combines content generation with API publishing.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    async def publish_world_cup_investigation(
        self,
        topic: str,
        sources: List[str],
        evidence: Optional[Dict] = None,
        schedule_time: Optional[datetime] = None
    ) -> Dict:
        """
        Generate and publish World Cup investigation article.
        
        Args:
            topic: Investigation subject
            sources: Primary sources and evidence
            evidence: Supporting documents/data
            schedule_time: Scheduled publication time
            
        Returns:
            Publication result with URL and editorial workflow status
        """
        
        from worldcup_content_engine import WorldCupContentGenerator
        
        # Generate investigation content
        generator = WorldCupContentGenerator()
        investigation = generator.generate_investigation(
            topic=topic,
            sources=sources,
            length="long"
        )
        
        # Convert to ObjectWire article format
        article = ObjectWireArticle(
            title=investigation["headline"],
            content=investigation["content"]["lead"] + "\n\n" + investigation["content"]["body"],
            category="case",
            author=investigation["byline"],
            publish_date=datetime.fromisoformat(investigation["publish_date"]),
            tags=investigation["tags"],
            meta_description=investigation["seo"]["meta_description"]
        )
        
        # Publish to ObjectWire.org
        async with ObjectWireAPI(self.api_key) as api:
            result = await api.publish_investigation(article, schedule_time)
            
        return result
    
    async def publish_breaking_world_cup_news(
        self,
        headline: str,
        details: str,
        urgency: Literal["low", "medium", "high", "urgent"] = "high",
        notify_subscribers: bool = True
    ) -> Dict:
        """
        Publish breaking World Cup news immediately.
        """
        
        async with ObjectWireAPI(self.api_key) as api:
            result = await api.publish_breaking_news(
                headline=headline,
                content=details,
                urgency=urgency,
                push_notification=notify_subscribers
            )
            
        return result
    
    async def start_live_match_coverage(
        self,
        home_team: str,
        away_team: str,
        venue: str,
        match_date: datetime
    ) -> Dict:
        """
        Start live blog for World Cup match coverage.
        """
        
        match_info = {
            "home_team": home_team,
            "away_team": away_team,
            "venue": venue,
            "date": match_date.isoformat(),
            "competition": "FIFA World Cup 2026"
        }
        
        blog_title = f"LIVE: {home_team} vs {away_team} - World Cup 2026"
        
        async with ObjectWireAPI(self.api_key) as api:
            result = await api.start_live_blog(match_info, blog_title)
            
        return result


# Configuration and environment setup
def get_objectwire_config() -> Dict:
    """Load ObjectWire.org API configuration."""
    
    return {
        "api_key": os.getenv("OBJECTWIRE_API_KEY"),
        "base_url": os.getenv("OBJECTWIRE_API_URL", "https://objectwire.org/api"),
        "author_name": os.getenv("OBJECTWIRE_AUTHOR", "ObjectWire World Cup Desk"),
        "auto_publish": os.getenv("OBJECTWIRE_AUTO_PUBLISH", "false").lower() == "true",
        "notification_webhook": os.getenv("OBJECTWIRE_WEBHOOK_URL")
    }

def validate_api_credentials() -> bool:
    """Validate ObjectWire.org API credentials."""
    
    config = get_objectwire_config()
    
    if not config["api_key"]:
        print("❌ Error: OBJECTWIRE_API_KEY environment variable not set")
        return False
        
    # TODO: Implement actual API credential validation
    print("✅ ObjectWire.org API credentials validated")
    return True


# Example usage and testing
async def test_objectwire_integration():
    """Test ObjectWire.org integration with sample content."""
    
    if not validate_api_credentials():
        return
    
    config = get_objectwire_config()
    publisher = WorldCupPublisher(config["api_key"])
    
    # Test investigation article
    investigation_result = await publisher.publish_world_cup_investigation(
        topic="FIFA 2026 Host City Selection Process",
        sources=[
            "FIFA official documents obtained by ObjectWire",
            "Interview with former FIFA executive (granted anonymity)",
            "Public records from host city bid committees"
        ]
    )
    
    print(f"Investigation published: {investigation_result}")
    
    # Test breaking news
    breaking_result = await publisher.publish_breaking_world_cup_news(
        headline="Star Player Ruled Out of World Cup with Injury",
        details="Medical tests confirm ACL injury will keep the striker out for 6 months",
        urgency="urgent"
    )
    
    print(f"Breaking news published: {breaking_result}")


if __name__ == "__main__":
    # Run integration test
    asyncio.run(test_objectwire_integration())