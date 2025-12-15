#!/usr/bin/env python3
"""
BlackBook URL Scraper CLI
==========================
Scrape URLs → Generate prediction events → Post to blockchain

Usage:
  python scraper.py <url>                    # Parse URL, show event
  python scraper.py <url> --post             # Parse and post to blockchain
  python scraper.py <url> --json             # Output as JSON
  python scraper.py <url> --post --json      # Post and output JSON
"""

import os
import sys
import json
import re
import hashlib
import argparse
import time
from urllib.parse import urlparse
from typing import Optional

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Configuration
BLOCKCHAIN_URL = os.getenv("BLOCKCHAIN_API_URL", "http://localhost:1234")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


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


class PredictionEvent(BaseModel):
    title: str
    description: str
    category: str
    options: list[str]
    confidence: float
    source_url: str
    resolution_date: str


def scrape(url: str) -> Optional[dict]:
    """Scrape content from URL with retry logic."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    for attempt in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=20)
            r.raise_for_status()
            break
        except requests.exceptions.RequestException as e:
            if attempt == 2:
                print(f"❌ Scrape failed: {e}", file=sys.stderr)
                return None
            time.sleep(1)
    
    soup = BeautifulSoup(r.content, "html.parser")
    
    # Remove noise
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        tag.decompose()
    
    title = soup.title.get_text(strip=True) if soup.title else "Untitled"
    
    # Get main content
    main = soup.find('article') or soup.find('main') or soup.body
    content = main.get_text("\n", strip=True)[:5000] if main else ""
    
    if len(content) < 100:
        print("❌ Content too short", file=sys.stderr)
        return None
    
    return {"title": title, "content": content, "url": url, "domain": urlparse(url).netloc}


def analyze(scraped: dict) -> PredictionEvent:
    """Generate prediction event from scraped content."""
    
    # Use OpenAI if available
    if openai and OPENAI_API_KEY:
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract a prediction market question from this article. Return JSON with: title (question), description, category, options (list of 2-3 choices), confidence (0-1), resolution_date (ISO format)."},
                    {"role": "user", "content": f"Title: {scraped['title']}\n\nContent: {scraped['content'][:2000]}"}
                ],
                temperature=0.3,
                max_tokens=400,
            )
            text = resp.choices[0].message.content
            # Parse JSON from response
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])
                return PredictionEvent(
                    title=data.get('title', f"Prediction: {scraped['title'][:60]}?"),
                    description=data.get('description', scraped['content'][:200]),
                    category=data.get('category', 'general'),
                    options=data.get('options', ['Yes', 'No']),
                    confidence=float(data.get('confidence', 0.7)),
                    source_url=scraped['url'],
                    resolution_date=data.get('resolution_date', '2025-12-31T23:59:00-05:00')
                )
        except Exception as e:
            print(f"⚠️ OpenAI error, using fallback: {e}", file=sys.stderr)
    
    # Fallback: Simple extraction
    return PredictionEvent(
        title=f"Will '{scraped['title'][:50]}' predictions come true?",
        description=f"Based on: {scraped['title']}",
        category="Uncategorized",
        options=["Yes", "No Change", "No"],
        confidence=0.5,
        source_url=scraped['url'],
        resolution_date="2025-12-31T23:59:00-05:00"
    )


def post_to_blockchain(event: PredictionEvent) -> Optional[str]:
    """Post event to markets API."""
    from datetime import datetime, timezone
    
    # Generate a human-readable source_id from the title
    source_id = generate_market_id(event.title, event.source_url)
    
    # Build payload for /markets endpoint
    payload = {
        "title": event.title,
        "description": event.description,
        "source_id": source_id,
        "category": event.category.capitalize() if event.category != "general" else "Uncategorized",
        "outcomes": event.options if len(event.options) >= 2 else ["Yes", "No Change", "No"],
        "probabilities": _calculate_probabilities(len(event.options), event.confidence),
        "published": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        # Post to /markets endpoint
        resp = requests.post(
            f"{BLOCKCHAIN_URL}/markets",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get('id') or data.get('market_id') or data.get('source_id')
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Markets API error: {e}", file=sys.stderr)
        return None


def _calculate_probabilities(num_options: int, confidence: float) -> list[float]:
    """Calculate probabilities for outcomes based on confidence."""
    if num_options == 2:
        return [round(confidence, 2), round(1 - confidence, 2)]
    elif num_options == 3:
        # For 3 options: Yes, No Change/Partial, No
        yes_prob = confidence * 0.49 / 0.5 if confidence <= 0.5 else 0.49
        no_prob = (1 - confidence) * 0.49 / 0.5 if confidence >= 0.5 else 0.49
        middle_prob = round(1 - yes_prob - no_prob, 2)
        return [round(yes_prob, 2), middle_prob, round(no_prob, 2)]
    else:
        # Distribute evenly
        base = round(1 / num_options, 2)
        probs = [base] * num_options
        # Adjust last to ensure sum = 1
        probs[-1] = round(1 - sum(probs[:-1]), 2)
        return probs


def main():
    parser = argparse.ArgumentParser(
        description="Scrape URL → Generate prediction event → Post to blockchain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scraper.py https://example.com/article
  python scraper.py https://example.com/article --post
  python scraper.py https://example.com/article --json
        """
    )
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("--post", action="store_true", help="Post event to blockchain")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    # Scrape
    scraped = scrape(args.url)
    if not scraped:
        sys.exit(1)
    
    # Analyze
    event = analyze(scraped)
    
    # Post if requested
    market_id = None
    if args.post:
        market_id = post_to_blockchain(event)
        if not market_id:
            print("⚠️ Failed to post to blockchain", file=sys.stderr)
    
    # Output
    if args.json:
        output = event.model_dump()
        if market_id:
            output['market_id'] = market_id
        print(json.dumps(output, indent=2))
    else:
        print(f"\n🎯 {event.title}")
        print(f"   📝 {event.description[:100]}...")
        print(f"   🏷️  {event.category} | Confidence: {event.confidence:.0%}")
        print(f"   🎲 Options: {', '.join(event.options)}")
        print(f"   ⏰ Resolves: {event.resolution_date}")
        if market_id:
            print(f"   🔗 Market ID: {market_id}")


if __name__ == "__main__":
    main()
