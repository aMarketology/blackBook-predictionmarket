"""
FIFA World Cup 2026 RSS Feed Configuration
"""

# FIFA & World Cup RSS Feeds
WORLD_CUP_RSS_FEEDS = {
    "fifa_official": "https://www.fifa.com/rss/news.xml",
    "espn_soccer": "https://www.espn.com/espn/rss/soccer/news",
    "bbc_football": "https://www.bbc.co.uk/sport/football/rss.xml",
    "goal_world_cup": "https://www.goal.com/feeds/en/news/world-cup.xml",
    "fox_soccer": "https://www.foxsports.com/soccer/rss",
    "the_athletic": "https://theathletic.com/feeds/rss/soccer/",
    "guardian_soccer": "https://www.theguardian.com/football/rss",
    "marca_es": "https://www.marca.com/rss/futbol.xml",  # Spanish coverage
    "univision": "https://www.univision.com/feeds/deportes/futbol",  # Spanish
    "cbc_soccer": "https://www.cbc.ca/cmlink/rss-sports-soccer",  # Canadian
}

# World Cup Teams (for filtering)
WORLD_CUP_TEAMS = [
    # CONCACAF (North/Central America)
    "USA", "Mexico", "Canada", "Costa Rica", "Panama", "Honduras",
    
    # CONMEBOL (South America)
    "Brazil", "Argentina", "Uruguay", "Colombia", "Chile", "Peru", "Ecuador",
    
    # UEFA (Europe)
    "Germany", "France", "Spain", "England", "Italy", "Portugal", "Netherlands",
    "Belgium", "Croatia", "Denmark", "Switzerland", "Poland", "Sweden",
    
    # AFC (Asia)
    "Japan", "South Korea", "Iran", "Saudi Arabia", "Australia", "Qatar",
    
    # CAF (Africa)
    "Morocco", "Senegal", "Tunisia", "Nigeria", "Ghana", "Cameroon", "Egypt",
]

# Keywords to filter World Cup relevant articles
WORLD_CUP_KEYWORDS = [
    "world cup",
    "world cup 2026",
    "fifa 2026",
    "wc2026",
    "mundial",
    "copa del mundo",
    "qualifying",
    "qualifiers",
    "usmnt",
    "concacaf",
    "group stage",
    "knockout",
    "round of 16",
    "quarter-final",
    "semi-final",
    "final",
]

# Venues for World Cup 2026
WORLD_CUP_VENUES = {
    "usa": [
        "MetLife Stadium (New York/New Jersey)",
        "AT&T Stadium (Dallas)",
        "Arrowhead Stadium (Kansas City)",
        "NRG Stadium (Houston)",
        "Mercedes-Benz Stadium (Atlanta)",
        "Lincoln Financial Field (Philadelphia)",
        "Levi's Stadium (San Francisco)",
        "SoFi Stadium (Los Angeles)",
        "Gillette Stadium (Boston)",
        "Hard Rock Stadium (Miami)",
        "Lumen Field (Seattle)",
    ],
    "mexico": [
        "Estadio Azteca (Mexico City)",
        "Estadio BBVA (Monterrey)",
        "Estadio Akron (Guadalajara)",
    ],
    "canada": [
        "BC Place (Vancouver)",
        "BMO Field (Toronto)",
    ]
}

# High-priority sources (check more frequently)
HIGH_PRIORITY_FEEDS = [
    "fifa_official",
    "espn_soccer",
    "bbc_football",
]

# Monitoring configuration
FEED_CONFIG = {
    "check_interval": 300,  # 5 minutes
    "max_articles_per_feed": 3,
    "min_word_count": 500,
    "auto_write": True,
    "auto_publish": False,  # Require manual approval
    "save_to_disk": True,
    "notification_enabled": False,
}
