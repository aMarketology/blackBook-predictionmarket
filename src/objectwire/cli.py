#!/usr/bin/env python3
"""
ObjectWire CLI - AI-Powered RSS/URL Scraper Agent
==================================================
Scrape URLs & RSS feeds → Generate prediction events → Post to blockchain

Usage:
  objectwire                           # Launch interactive mode
  objectwire scrape <url>              # Scrape URL
  objectwire scrape <url> --post       # Scrape and post to blockchain
  objectwire scrape <url> --json       # Output as JSON
  objectwire scrape <url> --xml        # Output as XML
  objectwire rss <feed_url>            # Parse RSS feed
  objectwire post <url>                # Scrape and post in one step
  objectwire test                      # Test blockchain connectivity
  objectwire status                    # Check system status
"""

import os
import sys
import json
import time
import hashlib
import subprocess
import xml.etree.ElementTree as ET
from xml.dom import minidom
from urllib.parse import urlparse
from typing import Optional, Any, Dict, List
from pathlib import Path
from datetime import datetime, timezone

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.columns import Columns
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding import KeyBindings
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel
import feedparser
from dotenv import load_dotenv

load_dotenv()

console = Console()

# Configuration
BLOCKCHAIN_URL = os.getenv("BLOCKCHAIN_API_URL", "http://localhost:1234")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEBUG_MODE = os.getenv("OBJECTWIRE_DEBUG", "false").lower() == "true"


def debug_log(message: str, data: Any = None):
    """Print debug message if debug mode is enabled."""
    if DEBUG_MODE:
        console.print(f"[dim cyan]🔍 DEBUG:[/] [dim]{message}[/]")
        if data is not None:
            if isinstance(data, dict):
                console.print_json(data=data)
            else:
                console.print(f"[dim]{data}[/]")


import re

def generate_market_id(title: str, url: str) -> str:
    """Generate a short market ID from first 3-5 words of title with hash suffix."""
    # Clean the title and get words
    clean = re.sub(r'[^a-z0-9\s]', '', title.lower())
    words = clean.split()
    
    # Take first 3-5 meaningful words (skip very short words)
    meaningful = [w for w in words if len(w) > 2][:4]
    slug = '-'.join(meaningful) if meaningful else 'market'
    
    # Add short hash suffix for uniqueness
    url_hash = hashlib.md5(url.encode()).hexdigest()[:6]
    
    return f"{slug}-{url_hash}"


# Try importing OpenAI
try:
    import openai
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
    else:
        openai = None
except ImportError:
    openai = None


# ─────────────────────────────────────────────────────────────
# Dev Mode - File Watcher for Auto-Reload
# ─────────────────────────────────────────────────────────────

def run_dev_mode():
    """Run in development mode with auto-reload on file changes."""
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        console.print("[red]Error:[/] watchdog not installed. Run: pip install watchdog")
        sys.exit(1)
    
    src_path = Path(__file__).parent
    
    class ReloadHandler(FileSystemEventHandler):
        def __init__(self):
            self.process = None
            self.start_app()
        
        def start_app(self):
            """Start the objectwire interactive mode as a subprocess."""
            if self.process:
                self.process.terminate()
                self.process.wait()
            
            console.print("\n[dim]─" * 50 + "[/]")
            console.print("[green]✓[/] [bold]Starting ObjectWire...[/]")
            console.print("[dim]─" * 50 + "[/]\n")
            
            # Run python -m objectwire (without --dev to avoid recursion)
            self.process = subprocess.Popen(
                [sys.executable, "-m", "objectwire"],
                cwd=src_path.parent.parent,
            )
        
        def on_modified(self, event):
            if event.src_path.endswith('.py'):
                rel_path = Path(event.src_path).relative_to(src_path.parent.parent)
                console.print(f"\n[yellow]⟳[/] File changed: [cyan]{rel_path}[/]")
                console.print("[yellow]  Reloading...[/]")
                self.start_app()
    
    console.print(Panel(
        "[bold orange1]🔧 DEV MODE[/]\n\n"
        "Watching for file changes in [cyan]src/objectwire/[/]\n"
        "Press [bold]Ctrl+C[/] to stop",
        border_style="orange1",
        padding=(1, 2)
    ))
    
    handler = ReloadHandler()
    observer = Observer()
    observer.schedule(handler, str(src_path), recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping dev mode...[/]")
        if handler.process:
            handler.process.terminate()
        observer.stop()
    observer.join()


# ─────────────────────────────────────────────────────────────
# XML Utilities
# ─────────────────────────────────────────────────────────────

def dict_to_xml(data: Dict[str, Any], root_name: str = "data") -> str:
    """Convert a dictionary to pretty-printed XML string."""
    
    def build_element(parent: ET.Element, key: str, value: Any):
        """Recursively build XML elements."""
        # Clean key name for valid XML tag
        tag = str(key).replace(" ", "_").replace("-", "_")
        
        if isinstance(value, dict):
            child = ET.SubElement(parent, tag)
            for k, v in value.items():
                build_element(child, k, v)
        elif isinstance(value, list):
            container = ET.SubElement(parent, tag)
            for item in value:
                if isinstance(item, dict):
                    item_elem = ET.SubElement(container, "item")
                    for k, v in item.items():
                        build_element(item_elem, k, v)
                else:
                    item_elem = ET.SubElement(container, "item")
                    item_elem.text = str(item)
        else:
            child = ET.SubElement(parent, tag)
            child.text = str(value) if value is not None else ""
    
    root = ET.Element(root_name)
    for key, value in data.items():
        build_element(root, key, value)
    
    # Pretty print
    xml_str = ET.tostring(root, encoding='unicode')
    parsed = minidom.parseString(xml_str)
    return parsed.toprettyxml(indent="  ")


def print_xml(data: Dict[str, Any], root_name: str = "data"):
    """Print data as formatted XML to console."""
    xml_output = dict_to_xml(data, root_name)
    console.print(xml_output)


# ─────────────────────────────────────────────────────────────
# Clipboard Functions
# ─────────────────────────────────────────────────────────────

def copy_to_clipboard(text: str) -> bool:
    """Copy text to Windows clipboard."""
    try:
        process = subprocess.Popen(
            ['clip'],
            stdin=subprocess.PIPE,
            shell=True
        )
        process.communicate(input=text.encode('utf-8'))
        return process.returncode == 0
    except Exception:
        return False


def paste_from_clipboard() -> Optional[str]:
    """Paste text from Windows clipboard."""
    try:
        result = subprocess.run(
            ['powershell', '-command', 'Get-Clipboard'],
            capture_output=True,
            text=True,
            shell=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────────────────────

# Social Media Market Categories
SOCIAL_CATEGORIES = {
    "metric": "Metric Market",      # Views, subs, streams (verifiable)
    "event": "Event Market",        # Specific occurrences
    "platform": "Platform Wars",    # Twitch/Kick/YouTube moves
    "product": "Creator Product",   # Prime, Feastables, merch
    "music": "Music & Streaming",   # Spotify, charts
}

# Market types for social events
MARKET_TYPES = {
    "binary": ["Yes", "No"],
    "three_choice": ["Yes", "No Change", "No"],
    "over_under": ["Over", "Under"],
    "velocity": ["Hits Target", "Misses Target"],
    "multi_outcome": None,  # Custom outcomes
}

# Resolution oracle types
ORACLE_TYPES = {
    "youtube_api": "YouTube Data API (views, subs)",
    "twitch_api": "Twitch API (followers, streams)",
    "spotify_api": "Spotify API (streams, charts)",
    "social_blade": "SocialBlade (public stats)",
    "manual": "Manual verification",
}


class PredictionEvent(BaseModel):
    """Prediction market event model matching blockchain API format."""
    # Required fields
    title: str
    description: str
    outcomes: List[str]
    source_url: str
    
    # Dates (published is required)
    published_date: str
    freeze_date: Optional[str] = None
    resolution_date: Optional[str] = None
    
    # Optional fields
    source: Optional[str] = None  # ID from scraper/source
    category: Optional[str] = None  # "crypto", "sports", "social"
    tags: Optional[List[str]] = None
    market_type: str = "three_choice"
    initial_probabilities: Optional[List[float]] = None
    image_url: Optional[str] = None
    
    # Resolution rules (optional)
    resolution_rules: Optional[Dict[str, Any]] = None
    
    # Social media specific fields
    social_metric: Optional[Dict[str, Any]] = None  # For velocity/metric markets


# ─────────────────────────────────────────────────────────────
# Core Functions
# ─────────────────────────────────────────────────────────────

def scrape_url(url: str) -> Optional[dict]:
    """Scrape content from URL with retry logic."""
    console.print(f"[cyan]🔍 DEBUG: Starting scrape for URL: {url}[/cyan]")
    
    # Create a session for better connection handling
    session = requests.Session()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.109 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
    }
    
    console.print(f"[cyan]🔍 DEBUG: Sending request with {len(headers)} headers[/cyan]")
    
    for attempt in range(3):
        try:
            console.print(f"[cyan]🔍 DEBUG: Attempt {attempt + 1}/3[/cyan]")
            r = session.get(url, headers=headers, timeout=30, allow_redirects=True)
            console.print(f"[cyan]🔍 DEBUG: Response status: {r.status_code}[/cyan]")
            console.print(f"[cyan]🔍 DEBUG: Response headers: {dict(r.headers)}[/cyan]")
            console.print(f"[cyan]🔍 DEBUG: Content length: {len(r.content)} bytes[/cyan]")
            r.raise_for_status()
            console.print(f"[green]✓ DEBUG: Request successful![/green]")
            break
        except requests.exceptions.HTTPError as e:
            console.print(f"[red]❌ DEBUG: HTTP Error on attempt {attempt + 1}: {e}[/red]")
            console.print(f"[red]   Status code: {r.status_code}[/red]")
            console.print(f"[red]   Response text: {r.text[:500]}[/red]")
            if attempt == 2:
                debug_log(f"Failed to scrape after 3 attempts: {e}")
                return None
            time.sleep(2 ** attempt)
        except requests.exceptions.RequestException as e:
            console.print(f"[red]❌ DEBUG: Request error on attempt {attempt + 1}: {e}[/red]")
            if attempt == 2:
                debug_log(f"Failed to scrape after 3 attempts: {e}")
                return None
            time.sleep(2 ** attempt)
    
    console.print(f"[cyan]🔍 DEBUG: Parsing HTML with BeautifulSoup[/cyan]")
    soup = BeautifulSoup(r.content, "html.parser")
    
    # Remove noise
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        tag.decompose()
    
    title = soup.title.get_text(strip=True) if soup.title else "Untitled"
    console.print(f"[cyan]🔍 DEBUG: Title: {title}[/cyan]")
    
    # Get main content
    main = soup.find('article') or soup.find('main') or soup.body
    console.print(f"[cyan]🔍 DEBUG: Found main element: {type(main).__name__ if main else 'None'}[/cyan]")
    
    content = main.get_text("\n", strip=True)[:5000] if main else ""
    console.print(f"[cyan]🔍 DEBUG: Content length: {len(content)} chars[/cyan]")
    
    if len(content) < 100:
        console.print(f"[red]❌ DEBUG: Content too short ({len(content)} chars), returning None[/red]")
        debug_log(f"Content too short ({len(content)} chars), returning None")
        return None
    
    result = {"title": title, "content": content, "url": url, "domain": urlparse(url).netloc}
    console.print(f"[green]✓ DEBUG: Scrape complete! Domain: {result['domain']}[/green]")
    debug_log(f"Scraped URL successfully", {
        "title": title,
        "content_length": len(content),
        "domain": result["domain"]
    })
    return result


def analyze(scraped: dict) -> PredictionEvent:
    """Generate prediction market event from scraped content."""
    debug_log(f"Analyzing scraped content from {scraped['domain']}")
    
    # Generate market_id from title (will be updated after we get the final title)
    market_id = generate_market_id(scraped['title'], scraped['url'])
    debug_log(f"Generated market_id: {market_id}")
    
    # Current timestamp for published date
    published_date = datetime.now(timezone.utc).isoformat()
    
    # Extract domain for source (optional ID)
    source_domain = urlparse(scraped['url']).netloc
    
    # Detect if this is social media content
    social_keywords = ['youtube', 'twitch', 'tiktok', 'instagram', 'twitter', 'x.com', 
                       'mrbeast', 'sidemen', 'ksi', 'logan paul', 'speed', 'kai cenat',
                       'views', 'subscribers', 'followers', 'stream', 'viral']
    content_lower = (scraped['title'] + ' ' + scraped['content'][:500]).lower()
    is_social = any(kw in content_lower for kw in social_keywords)
    
    # Use OpenAI if available
    if openai and OPENAI_API_KEY:
        try:
            # Use specialized prompt for social media content
            if is_social:
                system_prompt = """You are a social media prediction market expert. Extract a BETTABLE market from this article.

CRITICAL RULES:
1. ONLY bet on PUBLIC, VERIFIABLE data (views, subscribers, followers, chart positions)
2. NEVER bet on private data (revenue, earnings, CPM - these are NOT public)
3. Prefer "velocity" markets (e.g., "Will X hit Y views in 24 hours?")

Return JSON with:
- title: Clear prediction question with specific metric and timeframe
- description: Context explaining the bet
- category: One of "metric", "event", "platform", "product", "music"
- market_type: "velocity" (speed bets), "over_under" (threshold), "binary" (yes/no), "event" (occurrence)
- outcomes: Array of outcomes (e.g., ["Hits Target", "Misses Target"] or ["Yes", "No"])
- tags: Relevant tags including creator names, platforms
- resolution_date: When bet resolves (ISO8601)
- freeze_date: When betting closes (ISO8601, usually before resolution)
- social_metric: Object with {"platform": "youtube/twitch/spotify", "metric": "views/subs/streams", "target": number, "timeframe_hours": number, "oracle": "youtube_api/twitch_api/spotify_api"}

EXAMPLES:
{"title": "Will MrBeast's next video hit 50M views in 24 hours?", "market_type": "velocity", "outcomes": ["Hits 50M", "Under 50M"], "social_metric": {"platform": "youtube", "metric": "views", "target": 50000000, "timeframe_hours": 24, "oracle": "youtube_api"}}
{"title": "Will KSI reach 25M subscribers before Jake Paul?", "market_type": "binary", "outcomes": ["KSI First", "Jake First"]}
{"title": "Will Kai Cenat break his own Twitch viewer record in 2025?", "market_type": "binary", "outcomes": ["Yes", "No"]}"""
            else:
                system_prompt = """Extract a prediction market question from this article. Return JSON with:
- title: A clear yes/no prediction question based on the article
- description: Brief description of the prediction context
- category: Category like "crypto", "politics", "sports", "technology", "social"
- tags: Array of relevant tags
- resolution_date: ISO8601 date when this prediction can be resolved (if determinable, otherwise null)
- freeze_date: ISO8601 date when betting should freeze (if determinable, otherwise null)

Example response:
{"title": "Will Bitcoin reach $100k by end of 2025?", "description": "Based on analyst predictions...", "category": "crypto", "tags": ["bitcoin", "price"], "resolution_date": "2025-12-31T23:59:59Z", "freeze_date": null}"""
            
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Title: {scraped['title']}\n\nContent: {scraped['content'][:2000]}"}
                ],
                temperature=0.3,
                max_tokens=600,
            )
            text = resp.choices[0].message.content
            # Parse JSON from response
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])
                debug_log("OpenAI response parsed", data)
                
                # Get outcomes from AI or use defaults based on market type
                market_type = data.get('market_type', 'binary')
                outcomes = data.get('outcomes')
                if not outcomes:
                    outcomes = MARKET_TYPES.get(market_type, ["Yes", "No"])
                
                # Calculate probabilities based on outcome count
                num_outcomes = len(outcomes)
                if num_outcomes == 2:
                    initial_probs = [0.5, 0.5]
                elif num_outcomes == 3:
                    initial_probs = [0.49, 0.02, 0.49]
                else:
                    initial_probs = [1.0 / num_outcomes] * num_outcomes
                
                # Build resolution rules for social metrics
                resolution_rules = None
                social_metric = data.get('social_metric')
                if social_metric:
                    resolution_rules = {
                        "oracle_type": social_metric.get('oracle', 'manual'),
                        "metric": social_metric,
                        "verification": "API-based automatic resolution" if social_metric.get('oracle') else "Manual verification"
                    }
                
                event = PredictionEvent(
                    source=market_id,
                    title=data.get('title', f"Will {scraped['title'][:60]} happen?"),
                    description=data.get('description', scraped['content'][:200]),
                    category=data.get('category', 'social' if is_social else None),
                    tags=data.get('tags'),
                    market_type=market_type,
                    outcomes=outcomes,
                    initial_probabilities=initial_probs,
                    source_url=scraped['url'],
                    image_url=None,
                    published_date=published_date,
                    freeze_date=data.get('freeze_date'),
                    resolution_date=data.get('resolution_date'),
                    resolution_rules=resolution_rules,
                    social_metric=social_metric
                )
                debug_log("Created PredictionEvent (OpenAI)", event.model_dump())
                return event
        except Exception as e:
            debug_log(f"OpenAI failed: {e}, falling back to simple extraction")
    
    # Fallback: Simple extraction with social detection
    debug_log("Using fallback extraction (no OpenAI)")
    
    # Detect social platform for fallback
    fallback_category = None
    if is_social:
        fallback_category = "social"
        if 'youtube' in content_lower:
            fallback_category = "metric"
        elif 'twitch' in content_lower or 'kick' in content_lower:
            fallback_category = "platform"
        elif 'spotify' in content_lower:
            fallback_category = "music"
    
    event = PredictionEvent(
        source=market_id,
        title=f"Will '{scraped['title'][:50]}' predictions come true?",
        description=f"Based on: {scraped['title']}",
        category=fallback_category,
        tags=None,
        market_type="binary",
        outcomes=["Yes", "No"],
        initial_probabilities=[0.5, 0.5],
        source_url=scraped['url'],
        image_url=None,
        published_date=published_date,
        freeze_date=None,
        resolution_date=None
    )
    debug_log("Created PredictionEvent (fallback)", event.model_dump())
    return event


def post_to_blockchain(event: PredictionEvent) -> Optional[dict]:
    """Post event to blockchain API."""
    debug_log(f"Posting to blockchain: {BLOCKCHAIN_URL}/markets")
    
    # Build payload in new market format with nested dates
    payload = {
        "title": event.title,
        "description": event.description,
        "market_type": event.market_type,
        "outcomes": event.outcomes,
        "source_url": event.source_url,
        "dates": {
            "published": event.published_date,
        }
    }
    
    # Add optional fields if present
    if event.source:
        payload["source"] = event.source
    if event.category:
        payload["category"] = event.category
    if event.tags:
        payload["tags"] = event.tags
    if event.initial_probabilities:
        payload["initial_probabilities"] = event.initial_probabilities
    if event.image_url:
        payload["image_url"] = event.image_url
    if event.freeze_date:
        payload["dates"]["freeze"] = event.freeze_date
    if event.resolution_date:
        payload["dates"]["resolution"] = event.resolution_date
    if event.resolution_rules:
        payload["resolution_rules"] = event.resolution_rules
    if event.social_metric:
        payload["social_metric"] = event.social_metric
    
    debug_log("Payload being sent", payload)
    
    try:
        # Post event directly (no health check needed)
        resp = requests.post(
            f"{BLOCKCHAIN_URL}/markets",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        debug_log(f"Response status: {resp.status_code}")
        resp.raise_for_status()
        result = resp.json()
        debug_log("Blockchain response", result)
        return result
    
    except requests.exceptions.RequestException as e:
        debug_log(f"Blockchain error: {e}")
        return None


def post_to_blockchain_dict(event_dict: dict) -> Optional[dict]:
    """Post event dictionary directly to blockchain API (for AI-extracted events)."""
    debug_log(f"Posting to blockchain: {BLOCKCHAIN_URL}/markets")
    debug_log("Payload being sent", event_dict)
    
    try:
        resp = requests.post(
            f"{BLOCKCHAIN_URL}/markets",
            json=event_dict,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        debug_log(f"Response status: {resp.status_code}")
        resp.raise_for_status()
        result = resp.json()
        debug_log("Blockchain response", result)
        return result
    
    except requests.exceptions.RequestException as e:
        debug_log(f"Request failed: {e}")
        console.print(f"[red]❌ Failed to post to blockchain:[/] {e}")
        return None


def build_market_payload(event: PredictionEvent) -> dict:
    """Build the market payload for display/preview."""
    payload = {
        "title": event.title,
        "description": event.description,
        "market_type": event.market_type,
        "outcomes": event.outcomes,
        "source_url": event.source_url,
        "dates": {
            "published": event.published_date,
        }
    }
    
    # Add optional fields if present
    if event.source:
        payload["source"] = event.source
    if event.category:
        payload["category"] = event.category
    if event.tags:
        payload["tags"] = event.tags
    if event.initial_probabilities:
        payload["initial_probabilities"] = event.initial_probabilities
    if event.image_url:
        payload["image_url"] = event.image_url
    if event.freeze_date:
        payload["dates"]["freeze"] = event.freeze_date
    if event.resolution_date:
        payload["dates"]["resolution"] = event.resolution_date
    if event.resolution_rules:
        payload["resolution_rules"] = event.resolution_rules
    if event.social_metric:
        payload["social_metric"] = event.social_metric
    
    return payload


def display_market_panel(event: PredictionEvent, title: str = "🎯 Market Event"):
    """Display a market event in a formatted panel."""
    resolution = event.resolution_date or "Not set"
    freeze = event.freeze_date or "Not set"
    category = event.category or "Uncategorized"
    tags = ", ".join(event.tags) if event.tags else "None"
    probs = event.initial_probabilities or []
    
    # Format category with emoji for social types
    category_display = category
    if category in SOCIAL_CATEGORIES:
        category_icons = {"metric": "📊", "event": "🎬", "platform": "⚔️", "product": "🛍️", "music": "🎵"}
        category_display = f"{category_icons.get(category, '')} {SOCIAL_CATEGORIES[category]}"
    
    # Build base content
    content = (
        f"[bold cyan]{event.title}[/]\n\n"
        f"{event.description}\n\n"
        f"[dim]Source ID:[/] {event.source or 'Auto-generated'}\n"
        f"[dim]Category:[/] {category_display}\n"
        f"[dim]Tags:[/] {tags}\n"
        f"[dim]Market Type:[/] {event.market_type}\n"
        f"[dim]Outcomes:[/] {' | '.join(event.outcomes)}\n"
        f"[dim]Probabilities:[/] {probs}\n"
        f"[dim]Published:[/] {event.published_date}\n"
        f"[dim]Freeze:[/] {freeze}\n"
        f"[dim]Resolution:[/] {resolution}"
    )
    
    # Add social metric details if present
    if event.social_metric:
        sm = event.social_metric
        content += f"\n\n[bold yellow]📈 Social Metric[/]\n"
        content += f"[dim]Platform:[/] {sm.get('platform', 'N/A').upper()}\n"
        content += f"[dim]Metric:[/] {sm.get('metric', 'N/A')}\n"
        if sm.get('target'):
            content += f"[dim]Target:[/] {sm.get('target'):,}\n"
        if sm.get('timeframe_hours'):
            content += f"[dim]Timeframe:[/] {sm.get('timeframe_hours')} hours\n"
        content += f"[dim]Oracle:[/] {ORACLE_TYPES.get(sm.get('oracle'), sm.get('oracle', 'manual'))}"
    
    console.print(Panel(
        content,
        title=title,
        border_style="green"
    ))


def parse_rss(url: str) -> Optional[dict]:
    """Parse RSS/Atom feed from URL."""
    try:
        feed = feedparser.parse(url)
        if feed.bozo and not feed.entries:
            return None
        
        return {
            "title": feed.feed.get("title", "Unknown Feed"),
            "link": feed.feed.get("link", url),
            "items": [
                {
                    "title": entry.get("title", "Untitled"),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", entry.get("description", ""))[:200],
                    "published": entry.get("published", "")
                }
                for entry in feed.entries
            ]
        }
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# Interactive Mode
# ─────────────────────────────────────────────────────────────

def show_banner():
    """Display welcome banner with Claude-style layout."""
    import os
    from datetime import datetime
    
    # Get current directory
    cwd = os.getcwd()
    if len(cwd) > 35:
        cwd = "..." + cwd[-32:]
    
    # Build the welcome panel content with ASCII shamrock
    left_side = f"""
[bold orange3]ObjectWire[/] v0.1.0
─────────────────────────────

[bold orange1]      Welcome![/]

[orange3]           ,@@@,[/]
[orange3]          @@@@@@@[/]
[orange3]   ,@@@, '@@@@@@@' ,@@@,[/]
[orange3]  @@@@@@@ '@@@@@@' @@@@@@@[/]
[orange3]  '@@@@@@'  @@@@  '@@@@@@'[/]
[orange3]    '@@@' ,@@@@@@, '@@@'[/]
[orange3]         @@@@@@@@@@[/]
[orange3]          '@@@@@@'[/]
[orange3]            @@@@[/]
[orange3]            @@[/]
[orange3]            @@[/]
[orange3]            @@[/]

[dim]Prediction Markets[/]
[dim]{cwd}[/]
"""

    right_side = f"""[bold]Tips for getting started[/]
[dim]─────────────────────────────────────────────────────[/]
[orange3]scrape <url>[/]     Scrape a URL and generate prediction
[orange3]rss <feed>[/]       Parse an RSS feed for articles
[orange3]post[/]             Post last event to blockchain
[orange3]test[/]             Test blockchain connectivity
[orange3]status[/]           Check system status
[orange3]help[/]             Show all available commands
[orange3]exit[/]             Quit ObjectWire

[bold]Recent Commands[/]
[dim]─────────────────────────────────────────────────────[/]
[dim]Type a command to get started...[/]
"""

    # Create a two-column layout
    console.print()
    console.print(Panel(
        Columns([left_side, right_side], expand=True, equal=False),
        border_style="orange3",
        title="[bold orange3]ObjectWire CLI v0.1.0[/]",
        subtitle="[dim]AI-Powered Prediction Market Agent[/]"
    ))
    console.print()


def show_help():
    """Display help information."""
    help_md = """
## Commands

| Command | Description |
|---------|-------------|
| `<rss_feed_url>` | Just paste an RSS feed to see 3 latest posts |
| `<url>` | Just paste any URL to scrape and analyze it |
| `1`, `2`, `3`... | Select article from RSS feed |
| `1 json` | Get article 1 as JSON |
| `2 xml` | Get article 2 as XML |
| `3 json xml` | Get article 3 as both JSON and XML |
| `scrape <url>` | Scrape URL and generate prediction event |
| `rss <feed_url>` | Parse and display RSS feed items (15 max) |
| `post` | Post last event to blockchain |
| `copy` or `c` | Copy last event to clipboard (JSON) |
| `copy xml` | Copy last event to clipboard (XML) |
| `paste` or `v` | Paste URL from clipboard and process it |
| `test` | Test blockchain connectivity |
| `status` | Check system status |
| `debug` | Toggle debug mode (verbose logging) |
| `help` | Show this help |
| `exit` or `q` | Quit ObjectWire |

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+V` | Paste from clipboard into prompt |
| `Ctrl+C` | Cancel current operation |
| `↑` / `↓` | Browse command history |

## Examples

```
v                                    # Paste & process URL from clipboard
https://feeds.bbci.co.uk/news/rss.xml
copy
post
debug                                # Enable debug mode
```
"""
    console.print(Markdown(help_md))


def show_status():
    """Display system status."""
    table = Table(title="System Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status")
    
    # OpenAI
    if OPENAI_API_KEY:
        table.add_row("OpenAI API", "[green]✓ Configured[/]")
    else:
        table.add_row("OpenAI API", "[yellow]✗ Not set (using fallback)[/]")
    
    # Blockchain
    table.add_row("Blockchain URL", BLOCKCHAIN_URL)
    try:
        r = requests.get(f"{BLOCKCHAIN_URL}/health", timeout=3)
        if r.status_code == 200:
            table.add_row("Blockchain Status", "[green]✓ Online[/]")
        else:
            table.add_row("Blockchain Status", f"[red]✗ Error ({r.status_code})[/]")
    except:
        table.add_row("Blockchain Status", "[red]✗ Offline[/]")
    
    console.print(table)


def interactive_mode():
    """Launch interactive REPL mode."""
    show_banner()
    
    # Set up key bindings for Ctrl+V paste
    bindings = KeyBindings()
    
    @bindings.add(Keys.ControlV)
    def _(event):
        """Handle Ctrl+V to paste from clipboard."""
        clipboard_text = paste_from_clipboard()
        if clipboard_text:
            event.current_buffer.insert_text(clipboard_text)
    
    session = PromptSession(
        history=FileHistory(os.path.expanduser("~/.objectwire_history")),
        key_bindings=bindings,
        mouse_support=False  # Disable to allow normal terminal mouse behavior (select, scroll)
    )
    last_event: Optional[PredictionEvent] = None
    last_rss_items: list = []  # Store last RSS feed items for number selection
    
    while True:
        try:
            cmd = session.prompt("\n[objectwire]> ").strip()
            if not cmd:
                continue
            
            parts = cmd.split()
            action = parts[0].lower()
            args = " ".join(parts[1:]) if len(parts) > 1 else ""
            
            # Check if first part is a number (article selection from RSS)
            if action.isdigit() and last_rss_items:
                article_num = int(action)
                if 1 <= article_num <= len(last_rss_items):
                    item = last_rss_items[article_num - 1]
                    article_url = item["link"]
                    
                    console.print(f"\n[dim]Scraping article {article_num}: {item['title'][:50]}...[/]")
                    
                    with console.status("[green]Scraping article..."):
                        data = scrape_url(article_url)
                    
                    if not data:
                        console.print("[red]❌ Failed to scrape article[/]")
                        continue
                    
                    last_event = analyze(data)
                    
                    # Show the market event panel
                    display_market_panel(last_event)
                    
                    # Build and show the payload being sent
                    payload = build_market_payload(last_event)
                    console.print("\n[bold cyan]═══ Payload ═══[/]")
                    console.print_json(data=payload)
                    
                    # Auto-post to blockchain
                    with console.status("[green]Posting to blockchain..."):
                        result = post_to_blockchain(last_event)
                    
                    if result:
                        console.print(f"\n[green]✓ Posted to blockchain![/]")
                        if isinstance(result, dict):
                            event_id = result.get('id') or result.get('market_id') or result.get('event_id')
                            if event_id:
                                console.print(f"[dim]Market ID: {event_id}[/]")
                    else:
                        console.print("[yellow]⚠ Could not post to blockchain (service may be offline)[/]")
                    
                    continue
                else:
                    console.print(f"[red]Invalid article number. Choose 1-{len(last_rss_items)}[/]")
                    continue
            
            # Exit
            if action in ("exit", "quit", "q"):
                console.print("[yellow]👋 Goodbye![/]")
                break
            
            # Debug toggle
            elif action == "debug":
                global DEBUG_MODE
                DEBUG_MODE = not DEBUG_MODE
                status = "[green]enabled[/]" if DEBUG_MODE else "[yellow]disabled[/]"
                console.print(f"[dim cyan]🔍 Debug mode {status}[/]")
            
            # Help
            elif action == "help":
                show_help()
            
            # Status
            elif action == "status":
                show_status()
            
            # Scrape
            elif action == "scrape":
                if not args:
                    console.print("[red]Usage: scrape <url>[/]")
                    continue
                
                with console.status("[green]Scraping URL..."):
                    data = scrape_url(args)
                
                if not data:
                    console.print("[red]❌ Failed to scrape URL[/]")
                    continue
                
                last_event = analyze(data)
                display_market_panel(last_event)
                
                # Auto-post to blockchain
                with console.status("[green]Posting to blockchain..."):
                    result = post_to_blockchain(last_event)
                
                if result:
                    console.print(f"[green]✓ Posted to blockchain![/]")
                    if isinstance(result, dict):
                        event_id = result.get('id') or result.get('market_id') or result.get('event_id')
                        if event_id:
                            console.print(f"[dim]Event ID: {event_id}[/]")
                else:
                    console.print("[yellow]⚠ Could not post to blockchain (service may be offline)[/]")
            
            # RSS
            elif action == "rss":
                if not args:
                    console.print("[red]Usage: rss <feed_url>[/]")
                    continue
                
                with console.status("[green]Fetching RSS feed..."):
                    feed = parse_rss(args)
                
                if not feed:
                    console.print("[red]❌ Failed to parse RSS feed[/]")
                    continue
                
                # Store items for number selection
                last_rss_items = feed["items"][:15]
                
                table = Table(title=feed["title"])
                table.add_column("#", style="dim", width=3)
                table.add_column("Title", style="cyan")
                table.add_column("Published", style="dim", width=20)
                
                for i, item in enumerate(feed["items"][:15], 1):
                    table.add_row(str(i), item["title"][:60], item["published"][:20] if item["published"] else "")
                
                console.print(table)
                console.print(f"\n[dim]Type a number (1-{len(last_rss_items)}) to scrape that article. Add 'json' or 'xml' for formatted output.[/]")
                console.print(f"[dim]Example: '1 json' or '2 xml' or '3 json xml'[/]")
            
            # Post
            elif action == "post":
                if not last_event:
                    console.print("[red]No event to post. Scrape a URL first.[/]")
                    continue
                
                # Show preview data
                payload = build_market_payload(last_event)
                
                console.print("\n[bold cyan]═══ JSON Preview ═══[/]")
                console.print_json(data=payload)
                
                console.print("\n[bold cyan]═══ XML Preview ═══[/]")
                print_xml(payload, root_name="market_event")
                
                # Confirm before posting
                confirm = session.prompt("\n[yellow]Post to blockchain? (y/n):[/] ").strip().lower()
                if confirm not in ("y", "yes"):
                    console.print("[dim]Cancelled.[/]")
                    continue
                
                with console.status("[green]Posting to blockchain..."):
                    result = post_to_blockchain(last_event)
                
                if result:
                    event_id = result.get('id') or result.get('market_id') or result.get('event_id') if isinstance(result, dict) else result
                    console.print(f"[green]✓ Posted! Market ID:[/] [bold]{event_id}[/]")
                else:
                    console.print("[red]❌ Failed to post to blockchain[/]")
            
            # Copy - copy last event to clipboard
            elif action in ("copy", "c"):
                if not last_event:
                    console.print("[red]No event to copy. Scrape a URL first.[/]")
                    continue
                
                # Determine format (default JSON, or xml if specified)
                fmt = args.lower() if args else "json"
                output = last_event.model_dump()
                
                if fmt == "xml":
                    text = dict_to_xml(output, root_name="prediction_event")
                else:
                    text = json.dumps(output, indent=2)
                
                if copy_to_clipboard(text):
                    console.print(f"[green]✓ Copied to clipboard as {fmt.upper()}![/]")
                else:
                    console.print("[red]❌ Failed to copy to clipboard[/]")
            
            # Paste - paste URL from clipboard and process it
            elif action in ("paste", "v", "pv"):
                clipboard_text = paste_from_clipboard()
                if not clipboard_text:
                    console.print("[red]❌ Clipboard is empty or couldn't read[/]")
                    continue
                
                # Check if it's a URL
                if clipboard_text.startswith(("http://", "https://")):
                    console.print(f"[dim]Pasted: {clipboard_text[:60]}...[/]" if len(clipboard_text) > 60 else f"[dim]Pasted: {clipboard_text}[/]")
                    
                    # Try RSS first
                    with console.status("[green]Detecting content type..."):
                        feed = parse_rss(clipboard_text)
                    
                    if feed and feed.get("items"):
                        # It's an RSS feed
                        console.print(f"\n[bold orange3]📡 RSS Feed Detected:[/] {feed['title']}")
                        console.print("[dim]Showing 3 most recent posts:[/]\n")
                        
                        table = Table(title=feed["title"], border_style="orange3")
                        table.add_column("#", style="dim", width=3)
                        table.add_column("Title", style="orange3")
                        table.add_column("Link", style="dim")
                        
                        for i, item in enumerate(feed["items"][:3], 1):
                            link = item["link"][:45] + "..." if len(item["link"]) > 45 else item["link"]
                            table.add_row(str(i), item["title"][:55], link)
                        
                        console.print(table)
                    else:
                        # Scrape as webpage
                        with console.status("[green]Scraping URL..."):
                            data = scrape_url(clipboard_text)
                        
                        if data:
                            last_event = analyze(data)
                            display_market_panel(last_event)
                            
                            # Auto-post to blockchain
                            with console.status("[green]Posting to blockchain..."):
                                result = post_to_blockchain(last_event)
                            
                            if result:
                                console.print(f"[green]✓ Posted to blockchain![/]")
                                if isinstance(result, dict):
                                    event_id = result.get('id') or result.get('market_id') or result.get('event_id')
                                    if event_id:
                                        console.print(f"[dim]Market ID: {event_id}[/]")
                            else:
                                console.print("[yellow]⚠ Could not post to blockchain (service may be offline)[/]")
                        else:
                            console.print("[red]❌ Failed to parse URL[/]")
                else:
                    console.print(f"[yellow]Clipboard content is not a URL:[/] {clipboard_text[:50]}...")
            
            # Unknown
            else:
                # Auto-detect: Check if it's a URL (RSS feed or webpage)
                if cmd.startswith(("http://", "https://")):
                    url = cmd
                    
                    # Try RSS first
                    with console.status("[green]Detecting content type..."):
                        feed = parse_rss(url)
                    
                    if feed and feed.get("items"):
                        # It's an RSS feed - show top 3 items and store for selection
                        last_rss_items = feed["items"][:3]
                        
                        console.print(f"\n[bold orange3]📡 RSS Feed Detected:[/] {feed['title']}")
                        console.print("[dim]Showing 3 most recent posts:[/]\n")
                        
                        table = Table(title=feed["title"], border_style="orange3")
                        table.add_column("#", style="dim", width=3)
                        table.add_column("Title", style="orange3")
                        table.add_column("Link", style="dim")
                        
                        for i, item in enumerate(last_rss_items, 1):
                            link = item["link"][:45] + "..." if len(item["link"]) > 45 else item["link"]
                            table.add_row(str(i), item["title"][:55], link)
                        
                        console.print(table)
                        console.print(f"\n[dim]Type 1, 2, or 3 to scrape and post to blockchain.[/]")
                    else:
                        # Not RSS, try scraping as webpage
                        with console.status("[green]Scraping URL..."):
                            data = scrape_url(url)
                        
                        if data:
                            last_event = analyze(data)
                            display_market_panel(last_event)
                            
                            # Auto-post to blockchain
                            with console.status("[green]Posting to blockchain..."):
                                result = post_to_blockchain(last_event)
                            
                            if result:
                                console.print(f"[green]✓ Posted to blockchain![/]")
                                if isinstance(result, dict):
                                    event_id = result.get('id') or result.get('market_id') or result.get('event_id')
                                    if event_id:
                                        console.print(f"[dim]Market ID: {event_id}[/]")
                            else:
                                console.print("[yellow]⚠ Could not post to blockchain (service may be offline)[/]")
                        else:
                            console.print("[red]❌ Failed to parse URL (not RSS or scrapeable webpage)[/]")
                else:
                    console.print(f"[red]Unknown command:[/] {action}")
                    console.print("[dim]Type 'help' for available commands, or paste a URL/RSS feed[/]")
        
        except KeyboardInterrupt:
            continue
        except EOFError:
            console.print("\n[yellow]👋 Goodbye![/]")
            break


# ─────────────────────────────────────────────────────────────
# CLI Commands (Click)
# ─────────────────────────────────────────────────────────────

@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0", prog_name="objectwire")
@click.option("--dev", is_flag=True, help="Run in dev mode with auto-reload on file changes")
@click.option("--debug", is_flag=True, help="Enable debug mode with verbose logging")
@click.pass_context
def main(ctx, dev: bool, debug: bool):
    """🔌 ObjectWire - AI-Powered RSS/URL Scraper Agent for Prediction Markets"""
    global DEBUG_MODE
    if debug:
        DEBUG_MODE = True
        console.print("[dim cyan]🔍 Debug mode enabled[/]")
    
    if dev:
        run_dev_mode()
    elif ctx.invoked_subcommand is None:
        interactive_mode()


@main.command()
@click.argument("url")
@click.option("--post", is_flag=True, help="Post event to blockchain immediately")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--xml", "as_xml", is_flag=True, help="Output as XML")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt when posting")
@click.option("--no-ai", is_flag=True, help="Disable AI extraction (use fallback)")
def scrape(url: str, post: bool, as_json: bool, as_xml: bool, yes: bool, no_ai: bool):
    """Scrape a URL and generate blockchain-ready prediction event with AI.
    
    Examples:
        objectwire scrape https://techcrunch.com/article
        objectwire scrape https://coindesk.com/bitcoin --post
        objectwire scrape https://example.com --json
    """
    
    # Step 1: Scrape the URL
    with console.status("[cyan]🌐 Scraping URL..."):
        data = scrape_url(url)
    
    if not data:
        console.print("[red]❌ Failed to scrape URL[/]")
        sys.exit(1)
    
    console.print(f"[green]✓[/] Scraped: [bold]{data['title'][:60]}...[/]")
    
    # Step 2: Extract event with AI (unless --no-ai flag)
    if not no_ai:
        try:
            console.print("[cyan]🤖 Loading AI engine...[/]")
            from .llama_engine import create_nuextract_engine, BlockchainEvent
            
            engine = create_nuextract_engine()
            console.print("[green]✓[/] AI engine ready")
            
            with console.status("[cyan]🔮 Analyzing with AI (10-15 seconds)..."):
                blockchain_event = engine.analyze_article_blockchain(
                    title=data['title'],
                    content=data['content'],
                    url=url
                )
            
            console.print("[green]✓[/] AI extraction complete!")
            
            # Convert to dict for display
            event_dict = blockchain_event.model_dump()
            
        except Exception as e:
            console.print(f"[yellow]⚠ AI extraction failed: {e}[/]")
            console.print("[yellow]Falling back to basic extraction...[/]")
            event = analyze(data)
            event_dict = build_market_payload(event)
    else:
        # Use legacy extraction without AI
        event = analyze(data)
        event_dict = build_market_payload(event)
    
    # Step 3: Display results
    console.print("\n[bold cyan]═══ BLOCKCHAIN EVENT ═══[/]")
    
    # Display in chosen format
    if as_json:
        console.print_json(data=event_dict)
    elif as_xml:
        print_xml(event_dict, root_name="blockchain_event")
    else:
        # Pretty display
        console.print(f"\n[bold]📌 Title:[/] {event_dict.get('title', 'N/A')}")
        console.print(f"[bold]📝 Description:[/] {event_dict.get('description', 'N/A')[:150]}...")
        console.print(f"[bold]🏷️  Category:[/] {event_dict.get('category', 'N/A')}")
        
        tags = event_dict.get('tags', [])
        if tags:
            console.print(f"[bold]🔖 Tags:[/] {', '.join(tags)}")
        
        probs = event_dict.get('initial_probabilities')
        if probs:
            console.print(f"[bold]🎲 Odds:[/] Yes={probs[0]:.1%}, No Change={probs[1]:.1%}, No={probs[2]:.1%}")
        
        dates = event_dict.get('dates', {})
        if dates:
            console.print(f"[bold]📅 Resolution:[/] {dates.get('resolution', 'Not set')}")
        
        rules = event_dict.get('resolution_rules', {})
        if rules:
            console.print(f"[bold]🔮 Oracle:[/] {rules.get('data_source', 'N/A')}")
        
        console.print()
    
    # Step 4: Post to blockchain (if requested)
    if post:
        if not yes:
            if not click.confirm("\n[bold]Post to blockchain?[/]", default=True):
                console.print("[dim]Cancelled.[/]")
                return
        
        with console.status("[green]📤 Posting to blockchain..."):
            result = post_to_blockchain_dict(event_dict)
        
        if result:
            event_id = result.get('id') or result.get('market_id') or result.get('event_id')
            console.print(f"\n[green]✅ Posted to blockchain![/]")
            if event_id:
                console.print(f"[bold]Market ID:[/] {event_id}")
        else:
            console.print("\n[red]❌ Failed to post to blockchain[/]")
    else:
        console.print("[dim]💡 Tip: Add --post to publish to blockchain[/]")


@main.command()
@click.argument("feed_url")
@click.option("--limit", default=15, help="Max items to display")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--xml", "as_xml", is_flag=True, help="Output as XML")
def rss(feed_url: str, limit: int, as_json: bool, as_xml: bool):
    """Parse and display RSS feed items."""
    with console.status("[green]Fetching RSS feed..."):
        feed = parse_rss(feed_url)
    
    if not feed:
        console.print("[red]❌ Failed to parse RSS feed[/]")
        sys.exit(1)
    
    # Limit items
    limited_feed = {**feed, "items": feed["items"][:limit]}
    
    if as_xml:
        print_xml(limited_feed, root_name="rss_feed")
    elif as_json:
        console.print_json(data=limited_feed)
    else:
        table = Table(title=feed["title"])
        table.add_column("#", style="dim", width=3)
        table.add_column("Title", style="cyan")
        table.add_column("Link", style="dim")
        
        for i, item in enumerate(feed["items"][:limit], 1):
            table.add_row(str(i), item["title"][:55], item["link"][:40] + "..." if len(item["link"]) > 40 else item["link"])
        
        console.print(table)
        console.print(f"\n[dim]Showing {min(limit, len(feed['items']))} of {len(feed['items'])} items[/]")


@main.command()
def status():
    """Check system and API status."""
    show_status()


@main.command(name="post")
@click.argument("url")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--xml", "as_xml", is_flag=True, help="Output as XML")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def post_command(url: str, as_json: bool, as_xml: bool, yes: bool):
    """Scrape a URL and immediately post to blockchain."""
    with console.status("[green]Scraping URL..."):
        data = scrape_url(url)
    
    if not data:
        console.print("[red]❌ Failed to scrape URL[/]")
        sys.exit(1)
    
    event = analyze(data)
    payload = build_market_payload(event)
    
    # Show preview
    console.print("\n[bold cyan]═══ JSON Preview ═══[/]")
    console.print_json(data=payload)
    
    console.print("\n[bold cyan]═══ XML Preview ═══[/]")
    print_xml(payload, root_name="market_event")
    
    # Confirm before posting (unless --yes flag)
    if not yes:
        if not click.confirm("\nPost to blockchain?", default=False):
            console.print("[dim]Cancelled.[/]")
            sys.exit(0)
    
    with console.status("[green]Posting to blockchain..."):
        result = post_to_blockchain(event)
    
    output = event.model_dump()
    if result:
        event_id = result.get('id') or result.get('market_id') or result.get('event_id') if isinstance(result, dict) else result
        output['event_id'] = event_id
        output['status'] = 'posted'
    else:
        output['status'] = 'failed'
    
    if as_xml:
        print_xml(output, root_name="market_result")
    elif as_json:
        console.print_json(data=output)
    else:
        if result:
            event_id = result.get('id') or result.get('market_id') or result.get('event_id') if isinstance(result, dict) else result
            console.print(Panel(
                f"[bold cyan]{event.meta_title}[/]\n\n"
                f"[green]✓ Successfully posted to blockchain![/]\n"
                f"[dim]Market ID:[/] [bold]{event_id}[/]\n\n"
                f"[dim]Outcomes:[/] {' | '.join(event.outcomes)}",
                title="🎯 Posted Market",
                border_style="green"
            ))
        else:
            console.print(Panel(
                f"[bold cyan]{event.meta_title}[/]\n\n"
                f"[red]❌ Failed to post to blockchain[/]\n\n"
                f"[dim]Check 'objectwire test' for connectivity issues[/]",
                title="⚠️ Post Failed",
                border_style="red"
            ))
            sys.exit(1)


@main.command()
def test():
    """Test blockchain connectivity and API health."""
    console.print(Panel.fit(
        "[bold cyan]ObjectWire Connectivity Test[/]",
        border_style="cyan"
    ))
    
    table = Table(show_header=True)
    table.add_column("Test", style="cyan")
    table.add_column("Result")
    table.add_column("Details", style="dim")
    
    # Test 1: Blockchain health endpoint
    try:
        with console.status("[green]Testing blockchain health..."):
            r = requests.get(f"{BLOCKCHAIN_URL}/health", timeout=5)
        if r.status_code == 200:
            table.add_row("Blockchain Health", "[green]✓ PASS[/]", f"Status: {r.status_code}")
        else:
            table.add_row("Blockchain Health", "[red]✗ FAIL[/]", f"Status: {r.status_code}")
    except requests.exceptions.ConnectionError:
        table.add_row("Blockchain Health", "[red]✗ FAIL[/]", "Connection refused")
    except requests.exceptions.Timeout:
        table.add_row("Blockchain Health", "[red]✗ FAIL[/]", "Timeout")
    except Exception as e:
        table.add_row("Blockchain Health", "[red]✗ FAIL[/]", str(e)[:40])
    
    # Test 2: Markets endpoint
    try:
        with console.status("[green]Testing markets endpoint..."):
            r = requests.options(f"{BLOCKCHAIN_URL}/markets", timeout=5)
        if r.status_code in (200, 204, 405):  # 405 = method not allowed is OK (means endpoint exists)
            table.add_row("Markets Endpoint", "[green]✓ PASS[/]", f"Endpoint reachable")
        else:
            table.add_row("Markets Endpoint", "[yellow]? UNKNOWN[/]", f"Status: {r.status_code}")
    except requests.exceptions.ConnectionError:
        table.add_row("Markets Endpoint", "[red]✗ FAIL[/]", "Connection refused")
    except Exception as e:
        table.add_row("Markets Endpoint", "[red]✗ FAIL[/]", str(e)[:40])
    
    # Test 3: OpenAI API
    if OPENAI_API_KEY:
        table.add_row("OpenAI API Key", "[green]✓ CONFIGURED[/]", "Key present in environment")
    else:
        table.add_row("OpenAI API Key", "[yellow]⚠ NOT SET[/]", "Using fallback analysis")
    
    # Test 4: External URL scraping
    try:
        with console.status("[green]Testing URL scraping..."):
            r = requests.get("https://httpbin.org/get", timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
            })
        if r.status_code == 200:
            table.add_row("External HTTP", "[green]✓ PASS[/]", "Internet connectivity OK")
        else:
            table.add_row("External HTTP", "[red]✗ FAIL[/]", f"Status: {r.status_code}")
    except Exception as e:
        table.add_row("External HTTP", "[red]✗ FAIL[/]", str(e)[:40])
    
    console.print(table)
    console.print(f"\n[dim]Blockchain URL: {BLOCKCHAIN_URL}[/]")


@main.command()
def chat():
    """Interactive AI assistant - chat with ObjectWire CLI."""
    from .llama_engine import create_nuextract_engine, LlamaConfig
    from pathlib import Path
    
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🤖 ObjectWire AI Assistant[/]\n\n"
        "[dim]Ask me about commands, scrape URLs, or get help![/]\n"
        "[dim]Type 'exit' or 'quit' to leave[/]",
        border_style="cyan",
        title="AI Chat Mode"
    ))
    console.print()
    
    # Initialize NuExtract engine
    try:
        console.print("[dim]Loading offline AI model...[/]")
        engine = create_nuextract_engine()
        console.print("[green]✓ AI ready![/]\n")
    except Exception as e:
        console.print(f"[red]❌ Failed to load AI: {e}[/]")
        console.print("[yellow]Continuing with limited functionality...[/]\n")
        engine = None
    
    # Create session with history
    session = PromptSession(
        history=FileHistory(os.path.expanduser("~/.objectwire_chat_history"))
    )
    
    # System context about ObjectWire
    cli_context = """ObjectWire CLI is a tool for scraping URLs and creating prediction markets. 

Available commands:
- objectwire scrape <url> : Scrape a URL and generate a prediction event
- objectwire rss <feed> : Parse an RSS feed
- objectwire post <url> : Scrape and immediately post to blockchain
- objectwire test : Test blockchain connectivity
- objectwire status : Check system status
- objectwire chat : Start this AI assistant (current mode)

The tool can scrape news articles, analyze content with AI, and automatically create prediction market events that are posted to a blockchain API."""
    
    while True:
        try:
            user_input = session.prompt("\n[you]> ", completer=None).strip()
            
            if not user_input:
                continue
            
            # Check for exit commands
            if user_input.lower() in ("exit", "quit", "q", "bye"):
                console.print("\n[cyan]👋 Goodbye![/]")
                break
            
            # Check for help request
            if user_input.lower() in ("help", "commands", "?"):
                console.print("\n[bold cyan]ObjectWire Commands:[/]")
                console.print("  [orange3]scrape <url>[/]  - Scrape a URL and analyze")
                console.print("  [orange3]rss <feed>[/]    - Parse RSS feed")
                console.print("  [orange3]post <url>[/]    - Scrape and post to blockchain")
                console.print("  [orange3]test[/]          - Test blockchain connectivity")
                console.print("  [orange3]status[/]        - Check system status")
                console.print("  [orange3]chat[/]          - This AI assistant mode")
                console.print("\n[dim]In chat mode, you can:[/]")
                console.print("  • Ask questions about commands")
                console.print("  • Paste URLs to analyze")
                console.print("  • Get help with the tool")
                continue
            
            # Check if it's a URL - process it
            if user_input.startswith(("http://", "https://")):
                url = user_input
                console.print(f"\n[dim]🔍 Analyzing: {url}[/]")
                
                with console.status("[green]Scraping..."):
                    scraped = scrape_url(url)
                
                if not scraped:
                    console.print("[red]❌ Failed to scrape URL[/]")
                    continue
                
                if engine:
                    with console.status("[green]Analyzing with AI..."):
                        try:
                            event = engine.analyze_article(
                                scraped['title'],
                                scraped['content'],
                                url
                            )
                            
                            console.print("\n[bold green]✓ Analysis Complete![/]\n")
                            console.print(f"[bold]Title:[/] {event.title}")
                            console.print(f"[bold]Category:[/] {event.category}")
                            console.print(f"[bold]Tags:[/] {', '.join(event.tags)}")
                            console.print(f"[bold]Confidence:[/] {event.confidence:.1%}")
                            console.print(f"[bold]Options:[/] {', '.join(event.options)}")
                            console.print(f"\n[dim]Description:[/] {event.description[:150]}...")
                            
                            # Ask if user wants to post
                            post_confirm = session.prompt("\n[yellow]Post to blockchain? (y/n):[/] ").strip().lower()
                            if post_confirm in ("y", "yes"):
                                with console.status("[green]Posting..."):
                                    # Convert to PredictionEvent format
                                    pred_event = PredictionEvent(
                                        title=event.title,
                                        description=event.description,
                                        outcomes=event.options,
                                        source_url=event.source_url,
                                        category=event.category,
                                        tags=event.tags,
                                        published_date=datetime.now(timezone.utc).isoformat(),
                                        resolution_date=event.resolution_date
                                    )
                                    result = post_to_blockchain(pred_event)
                                
                                if result:
                                    console.print("[green]✓ Posted to blockchain![/]")
                                else:
                                    console.print("[red]❌ Failed to post[/]")
                            else:
                                console.print("[dim]Skipped posting[/]")
                        
                        except Exception as e:
                            console.print(f"[red]❌ AI analysis failed: {e}[/]")
                else:
                    console.print("[yellow]⚠ No AI engine loaded - showing basic analysis[/]")
                    console.print(f"Title: {scraped['title']}")
                    console.print(f"Domain: {scraped['domain']}")
                    console.print(f"Content length: {len(scraped['content'])} chars")
                
                continue
            
            # General conversational response
            console.print("\n[dim cyan]🤖 AI:[/] ", end="")
            
            if engine:
                # Use AI to respond
                console.print("[dim](Thinking...)[/]", end="\r")
                
                # Build a simple Q&A prompt
                prompt = f"""<|input|>
### Template:
{{
  "response": "Helpful response to user question",
  "suggested_command": "objectwire command if applicable, or null",
  "helpful": true
}}

### Text:
Context: {cli_context}

User Question: {user_input}

Provide a helpful response about ObjectWire CLI. If the user is asking how to do something, suggest the appropriate command.

<|output|>
"""
                
                try:
                    response = engine.extract(prompt)
                    
                    # Try to parse JSON from response
                    import re
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group())
                        console.print(f"\r{data.get('response', response[:200])}")
                        
                        if data.get('suggested_command'):
                            console.print(f"\n[dim]💡 Try:[/] [orange3]{data['suggested_command']}[/]")
                    else:
                        # Fallback to raw response
                        console.print(f"\r{response[:300]}")
                
                except Exception as e:
                    # Fallback to simple response
                    console.print(f"\r[dim]I'm having trouble understanding. Type 'help' to see available commands.[/]")
            else:
                # No AI - provide basic help
                if "scrape" in user_input.lower():
                    console.print("To scrape a URL, use: [orange3]objectwire scrape <url>[/]")
                elif "rss" in user_input.lower() or "feed" in user_input.lower():
                    console.print("To parse an RSS feed, use: [orange3]objectwire rss <feed_url>[/]")
                elif "post" in user_input.lower() or "blockchain" in user_input.lower():
                    console.print("To post to blockchain, use: [orange3]objectwire post <url>[/]")
                elif "test" in user_input.lower():
                    console.print("To test connectivity, use: [orange3]objectwire test[/]")
                else:
                    console.print("Type 'help' to see available commands, or paste a URL to analyze it.")
        
        except KeyboardInterrupt:
            console.print("\n[dim](Type 'exit' to quit)[/]")
            continue
        except EOFError:
            console.print("\n[cyan]👋 Goodbye![/]")
            break


if __name__ == "__main__":
    main()
