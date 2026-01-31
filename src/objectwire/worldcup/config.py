"""
World Cup 2026 Configuration
============================
Central configuration management for ObjectWire World Cup Writing Agent.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class WorldCupConfig:
    """Main configuration for World Cup writing agent."""
    
    # Tournament Information
    tournament_start: datetime = datetime(2026, 6, 11)
    tournament_end: datetime = datetime(2026, 7, 19)
    host_countries: List[str] = None
    
    # API Configurations
    objectwire_api_key: Optional[str] = None
    objectwire_api_url: str = "https://objectwire.org/api"
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # Content Generation Settings
    default_article_length: str = "medium"  # short, medium, long
    auto_publish: bool = False
    editorial_review_required: bool = True
    source_verification_required: bool = True
    
    # Monitoring Settings
    feed_check_interval: int = 600  # seconds
    breaking_news_threshold: str = "high"  # low, medium, high, urgent
    max_articles_per_hour: int = 10
    
    # Publishing Settings
    publish_to_social: bool = False
    send_notifications: bool = True
    seo_optimization: bool = True
    
    def __post_init__(self):
        if self.host_countries is None:
            self.host_countries = ["USA", "Canada", "Mexico"]
        
        # Load from environment variables
        self.objectwire_api_key = os.getenv("OBJECTWIRE_API_KEY", self.objectwire_api_key)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", self.gemini_api_key)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        
        # Override with environment settings
        self.auto_publish = os.getenv("AUTO_PUBLISH", "false").lower() == "true"
        self.editorial_review_required = os.getenv("EDITORIAL_REVIEW", "true").lower() == "true"


# World Cup 2026 Tournament Data
WORLD_CUP_2026 = {
    "host_cities": [
        {
            "city": "Atlanta",
            "country": "USA",
            "venue": "Mercedes-Benz Stadium",
            "capacity": 71000
        },
        {
            "city": "Boston",
            "country": "USA", 
            "venue": "Gillette Stadium",
            "capacity": 65878
        },
        {
            "city": "Dallas",
            "country": "USA",
            "venue": "AT&T Stadium", 
            "capacity": 80000
        },
        {
            "city": "Guadalajara",
            "country": "Mexico",
            "venue": "Estadio Akron",
            "capacity": 46355
        },
        {
            "city": "Houston", 
            "country": "USA",
            "venue": "NRG Stadium",
            "capacity": 72220
        },
        {
            "city": "Kansas City",
            "country": "USA",
            "venue": "Arrowhead Stadium",
            "capacity": 76416
        },
        {
            "city": "Los Angeles",
            "country": "USA",
            "venue": "SoFi Stadium",
            "capacity": 70240
        },
        {
            "city": "Mexico City",
            "country": "Mexico",
            "venue": "Estadio Azteca",
            "capacity": 87523
        },
        {
            "city": "Miami",
            "country": "USA",
            "venue": "Hard Rock Stadium",
            "capacity": 64767
        },
        {
            "city": "Monterrey",
            "country": "Mexico", 
            "venue": "Estadio BBVA",
            "capacity": 53500
        },
        {
            "city": "New York/New Jersey",
            "country": "USA",
            "venue": "MetLife Stadium",
            "capacity": 82500
        },
        {
            "city": "Philadelphia",
            "country": "USA",
            "venue": "Lincoln Financial Field",
            "capacity": 69176
        },
        {
            "city": "San Francisco Bay Area",
            "country": "USA",
            "venue": "Levi's Stadium",
            "capacity": 68500
        },
        {
            "city": "Seattle",
            "country": "USA",
            "venue": "Lumen Field",
            "capacity": 69000
        },
        {
            "city": "Toronto",
            "country": "Canada",
            "venue": "BMO Field",
            "capacity": 45500
        },
        {
            "city": "Vancouver",
            "country": "Canada",
            "venue": "BC Place",
            "capacity": 54500
        }
    ],
    
    "tournament_format": {
        "teams": 48,
        "groups": 16,
        "teams_per_group": 3,
        "matches_total": 104,
        "duration_days": 39
    },
    
    "key_dates": {
        "opening_ceremony": "2026-06-11",
        "first_match": "2026-06-11", 
        "group_stage_end": "2026-06-27",
        "round_of_32": "2026-06-30",
        "round_of_16": "2026-07-01",
        "quarter_finals": "2026-07-05",
        "semi_finals": "2026-07-09",
        "third_place": "2026-07-17",
        "final": "2026-07-19"
    }
}

# Content Templates and Standards
OBJECTWIRE_EDITORIAL_STANDARDS = {
    "investigation": {
        "minimum_sources": 3,
        "verification_required": True,
        "legal_review": True,
        "fact_check_stages": 3,
        "minimum_word_count": 800,
        "publication_delay": 72  # hours for thorough review
    },
    
    "breaking_news": {
        "maximum_delay": 15,  # minutes
        "source_verification": True,
        "fact_check_stages": 1,
        "minimum_word_count": 100,
        "editorial_approval": False  # Can publish immediately
    },
    
    "analysis": {
        "minimum_sources": 2,
        "expert_quotes_required": True,
        "fact_check_stages": 2,
        "minimum_word_count": 500,
        "publication_delay": 24  # hours
    },
    
    "live_updates": {
        "maximum_delay": 2,  # minutes
        "source_verification": False,  # Live updates from verified feeds
        "fact_check_stages": 0,
        "minimum_word_count": 50,
        "editorial_approval": False
    }
}

# SEO and Content Optimization
SEO_KEYWORDS = {
    "primary": [
        "world cup 2026",
        "fifa world cup",
        "soccer world cup",
        "football world cup",
        "usa canada mexico world cup"
    ],
    
    "secondary": [
        "fifa 2026",
        "world cup usa",
        "world cup canada", 
        "world cup mexico",
        "world cup investigation",
        "fifa corruption",
        "world cup news"
    ],
    
    "long_tail": [
        "world cup 2026 host cities",
        "fifa world cup 2026 schedule",
        "world cup 2026 teams",
        "world cup 2026 tickets",
        "fifa corruption investigation 2026",
        "world cup economic impact",
        "world cup player transfers"
    ]
}

# Social Media Configuration
SOCIAL_MEDIA_CONFIG = {
    "twitter": {
        "handle": "@objectwire",
        "hashtags": ["#WorldCup2026", "#FIFA", "#ObjectWire"],
        "auto_post": False,
        "character_limit": 280
    },
    
    "linkedin": {
        "page": "objectwire",
        "auto_post": False,
        "professional_tone": True
    },
    
    "facebook": {
        "page": "objectwire",
        "auto_post": False,
        "include_images": True
    }
}

# Monitoring and Alerting
ALERT_LEVELS = {
    "urgent": {
        "keywords": ["breaking", "dies", "arrested", "banned", "suspended", "corruption"],
        "response_time": 15,  # minutes
        "notification_channels": ["email", "slack", "sms"],
        "auto_publish": True
    },
    
    "high": {
        "keywords": ["injured", "transfer", "fired", "signs", "investigation"],
        "response_time": 60,  # minutes  
        "notification_channels": ["email", "slack"],
        "auto_publish": False
    },
    
    "medium": {
        "keywords": ["rumor", "report", "claim", "suggest"],
        "response_time": 240,  # minutes
        "notification_channels": ["slack"],
        "auto_publish": False
    },
    
    "low": {
        "keywords": ["update", "news", "announce"],
        "response_time": 720,  # minutes
        "notification_channels": [],
        "auto_publish": False
    }
}

def load_config() -> WorldCupConfig:
    """Load configuration from environment and defaults."""
    
    return WorldCupConfig()

def get_tournament_phase() -> str:
    """Determine current tournament phase."""
    
    now = datetime.now()
    config = load_config()
    
    if now < config.tournament_start:
        days_until = (config.tournament_start - now).days
        if days_until <= 30:
            return "pre_tournament_final_month"
        elif days_until <= 90:
            return "pre_tournament_preparation"
        else:
            return "pre_tournament_early"
    elif now > config.tournament_end:
        return "post_tournament"
    else:
        # During tournament - determine specific phase
        tournament_day = (now - config.tournament_start).days
        
        if tournament_day <= 16:  # June 11-27
            return "group_stage"
        elif tournament_day <= 19:  # June 30 - July 3
            return "round_of_32"
        elif tournament_day <= 23:  # July 5-6  
            return "quarter_finals"
        elif tournament_day <= 27:  # July 9-10
            return "semi_finals"
        elif tournament_day <= 35:  # July 17
            return "third_place_final"
        else:  # July 19
            return "final"

def get_host_city_info(city_name: str) -> Optional[Dict]:
    """Get information about a World Cup host city."""
    
    for city in WORLD_CUP_2026["host_cities"]:
        if city["city"].lower() == city_name.lower():
            return city
    
    return None

def get_editorial_standards(content_type: str) -> Dict:
    """Get editorial standards for content type."""
    
    return OBJECTWIRE_EDITORIAL_STANDARDS.get(content_type, {})

def validate_environment() -> Dict[str, bool]:
    """Validate required environment variables and configuration."""
    
    validation = {
        "objectwire_api_key": bool(os.getenv("OBJECTWIRE_API_KEY")),
        "gemini_api_key": bool(os.getenv("GEMINI_API_KEY")),
        "content_directory": os.path.exists("content/"),
        "logs_directory": os.path.exists("logs/"),
        "templates_directory": os.path.exists("templates/")
    }
    
    return validation


if __name__ == "__main__":
    # Test configuration loading
    config = load_config()
    print("🏆 World Cup 2026 Configuration")
    print(f"Tournament starts: {config.tournament_start}")
    print(f"Host countries: {', '.join(config.host_countries)}")
    print(f"Current phase: {get_tournament_phase()}")
    
    # Validate environment
    validation = validate_environment()
    print("\n🔧 Environment Validation:")
    for key, status in validation.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {key}")