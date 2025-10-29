#!/usr/bin/env python3
"""
BlackBook URL Scraping AI Agent - CLI Version
==============================================

Simple CLI tool that:
- scrapes a given URL
- uses (optional) OpenAI to craft a prediction-market-ready event
- optionally posts a market creation to the blockchain backend (simulated by default)
- returns "No event found" if no meaningful event can be derived

Usage: python serve_frontend.py --url <URL> [--ai-mock] [--create-market]
"""

import os
import json
import time
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel
from dotenv import load_dotenv

try:
    import openai
except Exception:
    openai = None

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BLOCKCHAIN_URL = os.getenv("BLOCKCHAIN_API_URL", "http://localhost:3000")
PORT = int(os.getenv("AGENT_PORT", "8082"))
ALLOW_CREATE_MARKET = os.getenv("ALLOW_CREATE_MARKET", "0") == "1"

if openai and OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
else:
    openai = None


class PredictionEvent(BaseModel):
    title: str
    description: str
    category: str
    options: List[str]
    confidence: float
    source_url: str
    resolution_date: str  # ISO format with timezone


def scrape_content(url: str, max_retries: int = 3) -> Dict:
    """
    Scrape content from a URL with retry logic and better headers
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, "html.parser")
            break
        except (requests.exceptions.ConnectionError, ConnectionResetError) as e:
            if attempt < max_retries - 1:
                print(f"⚠️ Connection error (attempt {attempt + 1}/{max_retries}), retrying...")
                time.sleep(2)
                continue
            else:
                print(f"❌ Scrape failed after {max_retries} attempts: {e}")
                return None
        except Exception as e:
            print(f"❌ Scrape failed: {e}")
            return None
    
    try:
        soup = BeautifulSoup(r.content, "html.parser")

        for el in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
            el.decompose()

        title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else "Untitled"

        article = soup.find('article') or soup.find('main')
        if article:
            text = article.get_text("\n", strip=True)
        else:
            text = soup.get_text("\n", strip=True)

        lines = [ln.strip() for ln in text.split('\n') if ln.strip()]
        content = '\n'.join(lines)[:10000]

        return {"title": title, "content": content, "domain": urlparse(url).netloc, "url": url}
    except Exception as e:
        print(f"❌ Scrape failed: {e}")
        return None


def json_from_text(text: str) -> Dict:
    try:
        start = text.find('{')
        if start == -1:
            raise ValueError('no JSON object')
        for end in range(len(text), start, -1):
            try:
                cand = text[start:end]
                return json.loads(cand)
            except Exception:
                continue
        return json.loads(text)
    except Exception:
        return {"title": "Untitled", "description": "", "options": ["Yes", "No"], "confidence": 0.5}


def analyze_with_ai(scraped: Dict, category: str, ai_mock: bool = False) -> PredictionEvent:
    if ai_mock or not openai:
        # Parse the title and content to generate relevant prediction events
        article_title = scraped.get('title', '').lower()
        content = scraped.get('content', '').lower()
        
        # Try to generate context-aware predictions based on content
        if 'github universe' in article_title or 'github universe' in content:
            title = f"Will GitHub Universe 2025 exceed 4,000 attendees?"
            description = f"Based on the article about GitHub Universe October 28-29, 2025 in San Francisco, will the conference exceed its projected 3,700 attendees to reach 4,000+ participants?"
            options = ["Yes, over 4,000 attendees", "No, under 4,000 attendees", "Exactly 3,700 attendees"]
            resolution_date = "2025-10-29T23:59:00-07:00"  # End of GitHub Universe, Pacific Time
            
        elif 'snap' in article_title or 'snap benefits' in content or 'doordash' in content:
            title = f"Will SNAP benefits mentioned in the article be exhausted by November 1, 2025?"
            description = f"Based on the article titled '{scraped.get('title')}', will SNAP benefits run out by Nov 1, 2025?"
            options = ["Yes, benefits exhausted by Nov 1, 2025", "No, benefits remain on Nov 1, 2025"]
            resolution_date = "2025-11-01T23:59:00-05:00"  # November 1st, Eastern Time
            
        elif 'trump' in article_title or 'pardon' in content or 'binance' in content:
            title = f"Will Trump's crypto pardons impact Bitcoin price by December 2025?"
            description = f"Based on the article about Trump's crypto policy decisions, will Bitcoin exceed $100,000 by December 2025?"
            options = ["Yes, Bitcoin over $100k", "No, Bitcoin under $100k", "Bitcoin exactly $100k"]
            resolution_date = "2025-12-31T23:59:00-05:00"  # End of December, Eastern Time
            
        elif 'robot' in article_title or 'ai' in article_title or 'artificial intelligence' in content:
            title = f"Will AI robotics funding exceed $50B in 2025?"
            description = f"Based on the article about AI and robotics developments, will total AI robotics funding exceed $50 billion in 2025?"
            options = ["Yes, over $50B funding", "No, under $50B funding"]
            resolution_date = "2025-12-31T23:59:00-05:00"  # End of 2025, Eastern Time
            
        elif 'luxury' in article_title or 'theft' in content or 'grand prix' in content:
            title = f"Will luxury watch thefts at major events increase by 25% in 2025?"
            description = f"Based on the article about luxury watch thefts, will similar crimes at major sporting events increase by 25% or more in 2025?"
            options = ["Yes, 25%+ increase", "No, less than 25% increase"]
            resolution_date = "2025-12-31T23:59:00-05:00"  # End of 2025, Eastern Time
            
        else:
            # Generic fallback based on title keywords
            title_words = scraped.get('title', '').split()[:3]  # First 3 words
            if len(title_words) >= 2:
                title = f"Will the events described in '{' '.join(title_words)}...' occur as predicted?"
                description = f"Based on the article titled '{scraped.get('title')}', will the main predictions or events described come to fruition?"
                options = ["Yes, events will occur", "No, events will not occur", "Partially accurate"]
                resolution_date = "2025-12-31T23:59:00-05:00"  # End of 2025, Eastern Time
            else:
                title = f"Will this article's predictions prove accurate?"
                description = f"Based on the content analysis, will the main claims or predictions in this article prove to be accurate?"
                options = ["Yes, accurate", "No, inaccurate", "Partially accurate"]
                resolution_date = "2025-12-31T23:59:00-05:00"  # End of 2025, Eastern Time
        
        return PredictionEvent(title=title, description=description, category=category, options=options, confidence=0.7, source_url=scraped.get('url'), resolution_date=resolution_date)

    try:
        prompt = (
            f"Create a prediction-market-ready JSON from the article.\nTitle: {scraped.get('title')}\n\n"
            f"Content excerpt: {scraped.get('content','')[:2000]}\n\n"
            "Return only a JSON object with keys: title, description, category, options (list), confidence (0-1)."
        )

        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You extract clear, objective prediction-market questions from articles."}, {"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=400,
        )

        text = None
        if resp and hasattr(resp, 'choices') and len(resp.choices) > 0:
            ch = resp.choices[0]
            text = getattr(ch, 'message', None)
            if text:
                text = text.get('content') if isinstance(text, dict) else text.content
            else:
                text = getattr(ch, 'text', None)

        if not text:
            raise RuntimeError('OpenAI returned empty response')

        parsed = json_from_text(text)
        return PredictionEvent(
            title=parsed['title'],
            description=parsed['description'],
            category=parsed.get('category', category),
            options=parsed['options'],
            confidence=float(parsed.get('confidence', 0.8)),
            source_url=scraped.get('url')
        )
    except Exception as e:
        print(f"[analyze_with_ai] AI error: {e}")
        return PredictionEvent(
            title=f"Prediction: {scraped.get('title')[:80]}?",
            description=scraped.get('content','')[:200],
            category=category,
            options=["Yes", "No"],
            confidence=0.5,
            source_url=scraped.get('url')
        )


def test_blockchain_connection() -> Dict:
    """
    Test connection to the blockchain API
    """
    print(f"🔍 Testing blockchain connection at {BLOCKCHAIN_URL}")
    
    try:
        # Test health endpoint
        health_response = requests.get(f"{BLOCKCHAIN_URL}/health", timeout=5)
        
        if health_response.status_code == 200:
            print(f"✅ Blockchain health check passed")
            return {
                "success": True,
                "message": "Blockchain connection successful",
                "health_status": health_response.json() if health_response.text else {"status": "ok"}
            }
        else:
            print(f"❌ Blockchain health check failed: {health_response.status_code}")
            return {
                "success": False,
                "error": f"Health check failed with status {health_response.status_code}",
                "response": health_response.text
            }
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to blockchain at {BLOCKCHAIN_URL}")
        return {
            "success": False,
            "error": f"Connection failed - is your blockchain running on {BLOCKCHAIN_URL}?"
        }
    except Exception as e:
        print(f"❌ Blockchain test error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def create_market(event: PredictionEvent, dry_run: bool = True) -> Dict:
    """
    Enhanced blockchain market creation with detailed response and error handling
    """
    from urllib.parse import urlparse
    
    # Parse the URL to get the domain
    parsed_url = urlparse(event.source_url)
    domain = parsed_url.netloc
    
    # Format payload to match blockchain API expectations
    payload = {
        "source": {
            "domain": domain,
            "url": event.source_url
        },
        "event": {
            "title": event.title,
            "description": event.description,
            "category": event.category,
            "options": event.options,
            "confidence": event.confidence,
            "source_url": event.source_url,
            "resolution_date": event.resolution_date
        }
    }

    # Return simulation if dry run or blockchain posting is disabled
    if not ALLOW_CREATE_MARKET or dry_run:
        sim_id = f"SIM-{int(time.time())}"
        return {
            "success": True,
            "market_id": sim_id,
            "mode": "simulation",
            "message": f"Market simulated with ID: {sim_id}",
            "payload": payload
        }

    print(f"🔗 Posting to blockchain: {BLOCKCHAIN_URL}/ai/events")
    
    try:
        # Test blockchain connection first
        health_response = requests.get(f"{BLOCKCHAIN_URL}/health", timeout=5)
        if health_response.status_code != 200:
            return {
                "success": False,
                "error": f"Blockchain health check failed: {health_response.status_code}",
                "mode": "blockchain",
                "payload": payload
            }
        
        # Create the market using the correct endpoint
        response = requests.post(
            f"{BLOCKCHAIN_URL}/ai/events", 
            json=payload, 
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        
        market_id = data.get('id') or data.get('market_id') or data.get('marketId') or data.get('event_id')
        
        if market_id:
            return {
                "success": True,
                "market_id": market_id,
                "mode": "blockchain",
                "message": f"Event created successfully on blockchain: {market_id}",
                "blockchain_response": data,
                "payload": payload
            }
        else:
            return {
                "success": False,
                "error": "Blockchain returned success but no event ID found",
                "mode": "blockchain",
                "blockchain_response": data,
                "payload": payload
            }
            
    except requests.exceptions.ConnectionError as e:
        return {
            "success": False,
            "error": f"Cannot connect to blockchain at {BLOCKCHAIN_URL}: {str(e)}",
            "mode": "blockchain",
            "payload": payload
        }
    except requests.exceptions.Timeout as e:
        return {
            "success": False,
            "error": f"Blockchain request timed out: {str(e)}",
            "mode": "blockchain", 
            "payload": payload
        }
    except requests.exceptions.HTTPError as e:
        return {
            "success": False,
            "error": f"Blockchain HTTP error {response.status_code}: {response.text}",
            "mode": "blockchain",
            "status_code": response.status_code,
            "response_text": response.text,
            "payload": payload
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected blockchain error: {str(e)}",
            "mode": "blockchain",
            "payload": payload
        }


def run_pipeline(url: str, category: str = "tech", create_market_flag: bool = False, ai_mock: bool = False, save_dir: Optional[str] = "logs") -> Optional[Dict]:
    os.makedirs(save_dir, exist_ok=True)
    stamp = int(time.time())
    run_id = f"run_{stamp}"
    out = {"run_id": run_id, "url": url, "steps": []}

    # Step 1: Scrape content
    scraped = scrape_content(url)
    if not scraped:
        print("❌ Failed to scrape content")
        return None
    
    out['scraped'] = scraped
    out['steps'].append('scraped')
    with open(os.path.join(save_dir, f"{run_id}_scraped.json"), 'w', encoding='utf-8') as f:
        json.dump(scraped, f, ensure_ascii=False, indent=2)

    # Step 2: Check if content is substantial enough for event generation
    content_length = len(scraped.get('content', ''))
    if content_length < 100:  # Minimum content threshold
        print(f"❌ Content too short ({content_length} chars) - no meaningful event can be derived")
        return None

    # Step 3: Analyze with AI
    try:
        event = analyze_with_ai(scraped, category, ai_mock=ai_mock)
        out['event'] = json.loads(event.model_dump_json())
        out['steps'].append('analyzed')
        with open(os.path.join(save_dir, f"{run_id}_event.json"), 'w', encoding='utf-8') as f:
            json.dump(out['event'], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Failed to analyze content: {e}")
        return None

    # Step 4: Create market if requested
    if create_market_flag:
        market_result = create_market(event, dry_run=not ALLOW_CREATE_MARKET)
        out['market_result'] = market_result
        
        if market_result['success']:
            out['market_id'] = market_result['market_id']
            out['steps'].append('market_created')
            print(f"✅ {market_result['message']}")
        else:
            out['steps'].append('market_failed')
            print(f"❌ Market creation failed: {market_result['error']}")

    return out


def parse_url(url: str, ai_mock: bool = False, create_market_flag: bool = False) -> Dict:
    """
    Parse a single URL and return event data or 'No event found'
    """
    print(f"🔍 Parsing URL: {url}")
    
    try:
        result = run_pipeline(
            url=url, 
            ai_mock=ai_mock, 
            create_market_flag=create_market_flag,
            save_dir="logs"
        )
        
        if result and result.get('event'):
            event = result['event']
            print(f"✅ Event found: {event['title']}")
            
            response = {
                "status": "success",
                "event_found": True,
                "event": event,
                "source_url": url,
                "run_id": result.get('run_id')
            }
            
            # Include market creation results if attempted
            if create_market_flag and 'market_result' in result:
                response['market_result'] = result['market_result']
                response['market_id'] = result.get('market_id')
                
            return response
        else:
            print("❌ No event found")
            return {
                "status": "success", 
                "event_found": False,
                "message": "No event found",
                "source_url": url
            }
            
    except Exception as e:
        print(f"❌ Error processing URL: {e}")
        return {
            "status": "error",
            "event_found": False,
            "error": str(e),
            "source_url": url
        }


def main():
    import argparse
    global ALLOW_CREATE_MARKET

    p = argparse.ArgumentParser(description='BlackBook URL Scraping AI Agent - CLI Version')
    p.add_argument('--url', type=str, help='URL to parse for events')
    p.add_argument('--ai-mock', action='store_true', help='Use deterministic AI mock (default: True if no OpenAI key)')
    p.add_argument('--create-market', action='store_true', help='Attempt to create market (simulated by default)')
    p.add_argument('--json', action='store_true', help='Output only JSON result')
    p.add_argument('--test-blockchain', action='store_true', help='Test blockchain connection')
    p.add_argument('--enable-blockchain', action='store_true', help='Enable real blockchain posting (sets ALLOW_CREATE_MARKET=1)')
    args = p.parse_args()

    # Enable blockchain posting if requested
    if args.enable_blockchain:
        import os
        os.environ['ALLOW_CREATE_MARKET'] = '1'
        # Re-read the environment variable to update the global
        ALLOW_CREATE_MARKET = os.getenv("ALLOW_CREATE_MARKET", "0") == "1"
        print("🔗 Blockchain posting enabled for this session")

    # Test blockchain connection if requested
    if args.test_blockchain:
        test_result = test_blockchain_connection()
        if args.json:
            print(json.dumps(test_result, indent=2))
        else:
            if test_result['success']:
                print(f"✅ Blockchain test successful: {test_result['message']}")
            else:
                print(f"❌ Blockchain test failed: {test_result['error']}")
        exit(0)

    # URL is required for parsing
    if not args.url:
        print("❌ Error: --url is required (or use --test-blockchain)")
        p.print_help()
        exit(1)

    # Auto-enable ai_mock if no OpenAI key is available
    use_ai_mock = args.ai_mock or not openai
    
    result = parse_url(args.url, ai_mock=use_ai_mock, create_market_flag=args.create_market)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result['event_found']:
            event = result['event']
            print(f"\n🎯 Prediction Event Generated:")
            print(f"   Title: {event['title']}")
            print(f"   Category: {event['category']}")
            print(f"   Confidence: {event['confidence']}")
            print(f"   Options: {', '.join(event['options'])}")
            print(f"   Resolution Date: {event['resolution_date']}")
            
            # Show blockchain result if market creation was attempted
            if args.create_market and 'market_result' in result:
                market_result = result['market_result']
                if market_result['success']:
                    print(f"   🔗 Event ID: {market_result['market_id']} ({market_result['mode']})")
                else:
                    print(f"   ❌ Blockchain Creation Failed: {market_result['error']}")
        else:
            print(f"\n❌ {result.get('message', 'No event could be derived from this URL')}")


if __name__ == '__main__':
    main()