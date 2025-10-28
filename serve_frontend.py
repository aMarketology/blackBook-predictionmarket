#!/usr/bin/env python3
"""
BlackBook URL Scraping AI Agent
================================

Small, well-scoped agent that:
- scrapes a given URL
- uses (optional) OpenAI to craft a prediction-market-ready event
- optionally posts a market creation to the blockchain backend (simulated by default)

Run with --serve to start the API or --url <URL> to run a single pipeline.
"""

import os
import json
import time
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
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

app = FastAPI(title="BlackBook URL Scraper")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class URLRequest(BaseModel):
    url: HttpUrl
    category: Optional[str] = "tech"


class PredictionEvent(BaseModel):
    title: str
    description: str
    category: str
    options: List[str]
    confidence: float
    source_url: str


def scrape_content(url: str) -> Dict:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; BlackBookScraper/1.0)"}
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
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
        raise HTTPException(status_code=400, detail=f"Scrape failed: {e}")


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
        title = f"Will SNAP benefits mentioned in the article be exhausted by November 1, 2025?"
        description = f"Based on the article titled '{scraped.get('title')}', will SNAP benefits run out by Nov 1, 2025?"
        options = ["Yes, benefits exhausted by Nov 1, 2025", "No, benefits remain on Nov 1, 2025"]
        return PredictionEvent(title=title, description=description, category=category, options=options, confidence=0.6, source_url=scraped.get('url'))

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


def create_market(event: PredictionEvent, dry_run: bool = True) -> Optional[str]:
    payload = {
        "title": event.title,
        "description": event.description,
        "category": event.category,
        "options": event.options,
        "source_url": event.source_url,
    }

    if not ALLOW_CREATE_MARKET or dry_run:
        return f"SIM-{int(time.time())}"

    try:
        r = requests.post(f"{BLOCKCHAIN_URL}/api/markets/create", json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data.get('id') or data.get('market_id')
    except Exception as e:
        print(f"[create_market] error: {e}")
        return None


def run_pipeline(url: str, category: str = "tech", create_market_flag: bool = False, ai_mock: bool = False, save_dir: Optional[str] = "logs") -> Dict:
    os.makedirs(save_dir, exist_ok=True)
    stamp = int(time.time())
    run_id = f"run_{stamp}"
    out = {"run_id": run_id, "url": url, "steps": []}

    scraped = scrape_content(url)
    out['scraped'] = scraped
    out['steps'].append('scraped')
    with open(os.path.join(save_dir, f"{run_id}_scraped.json"), 'w', encoding='utf-8') as f:
        json.dump(scraped, f, ensure_ascii=False, indent=2)

    event = analyze_with_ai(scraped, category, ai_mock=ai_mock)
    out['event'] = json.loads(event.json())
    out['steps'].append('analyzed')
    with open(os.path.join(save_dir, f"{run_id}_event.json"), 'w', encoding='utf-8') as f:
        json.dump(out['event'], f, ensure_ascii=False, indent=2)

    if create_market_flag:
        market_id = create_market(event, dry_run=not ALLOW_CREATE_MARKET)
        out['market_id'] = market_id
        out['steps'].append('market_created' if market_id else 'market_failed')

    return out


@app.get("/")
async def info():
    return {"name": "BlackBook URL Scraper", "version": "2.0.0", "openai": bool(openai), "blockchain": BLOCKCHAIN_URL}


@app.get("/health")
async def health():
    return {"status": "ok", "openai": bool(openai)}


@app.post("/scrape")
async def api_scrape(req: URLRequest):
    res = run_pipeline(str(req.url), category=req.category, create_market_flag=False, ai_mock=False)
    return res


if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('--serve', action='store_true', help='Run API server')
    p.add_argument('--url', type=str, help='Run pipeline once for URL')
    p.add_argument('--ai-mock', action='store_true', help='Use deterministic AI mock')
    p.add_argument('--create-market', action='store_true', help='Attempt to create market (may be simulated)')
    args = p.parse_args()

    if args.serve:
        uvicorn.run(app, host='0.0.0.0', port=PORT)
    elif args.url:
        result = run_pipeline(args.url, ai_mock=args.ai_mock, create_market_flag=args.create_market)
        print(json.dumps(result, indent=2))
    else:
        print('No action specified. Use --serve or --url <URL>')