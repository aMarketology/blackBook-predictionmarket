#!/usr/bin/env python3
"""
🤖 BlackBook URL Scraping AI Agent
==================================
Scrapes URLs → Extracts events → Creates prediction markets

Usage:
    POST /scrape {"url": "https://example.com"}
    GET /health
"""

import os
import json
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import uvicorn
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BLOCKCHAIN_URL = os.getenv("BLOCKCHAIN_API_URL", "http://localhost:3000")
PORT = int(os.getenv("AGENT_PORT", "8082"))

# Initialize
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
app = FastAPI(title="🤖 BlackBook URL Scraper", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ============================================
# DATA MODELS
# ============================================

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

class ScrapeResponse(BaseModel):
    success: bool
    market_id: Optional[str] = None
    event: Optional[PredictionEvent] = None
    message: str

# ============================================
# CORE FUNCTIONS
# ============================================

def scrape_content(url: str) -> Dict:
    """Scrape webpage content"""
    try:
        print(f"🔍 Scraping: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # Extract title
        title = soup.find('title')
        title = title.text.strip() if title else "Untitled"
        
        # Extract main content
        content = soup.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        content = '\n'.join(lines)[:5000]  # Limit to 5000 chars
        
        return {
            "title": title,
            "content": content,
            "domain": urlparse(url).netloc,
            "url": url
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Scraping failed: {str(e)}")

def analyze_with_ai(scraped: Dict, category: str) -> PredictionEvent:
    """Use AI to create prediction event from scraped content"""
    
    if not openai_client:
        # Fallback without AI
        return PredictionEvent(
            title=f"Prediction: {scraped['title'][:80]}?",
            description=scraped['content'][:200] + "...",
            category=category,
            options=["Yes", "No"],
            confidence=0.5,
            source_url=scraped['url']
        )
    
    try:
        print("🤖 Analyzing with AI...")
        
        prompt = f"""Create a prediction market from this article:

Title: {scraped['title']}
Content: {scraped['content'][:2000]}

Create a clear, specific prediction question that can be resolved objectively.

Return JSON:
{{
    "title": "Will X happen by Y date?",
    "description": "Brief context in 1-2 sentences",
    "category": "{category}",
    "options": ["Yes", "No"] or ["Option A", "Option B", "Option C"],
    "confidence": 0.8
}}"""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You create prediction market events from news. Be specific and time-bound."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return PredictionEvent(
            title=result['title'],
            description=result['description'],
            category=result.get('category', category),
            options=result['options'],
            confidence=result.get('confidence', 0.8),
            source_url=scraped['url']
        )
        
    except Exception as e:
        print(f"⚠️ AI failed: {e}")
        # Fallback
        return PredictionEvent(
            title=f"Prediction about: {scraped['title'][:60]}",
            description=scraped['content'][:200],
            category=category,
            options=["Likely", "Unlikely"],
            confidence=0.6,
            source_url=scraped['url']
        )

def create_market(event: PredictionEvent) -> Optional[str]:
    """Create market on blockchain"""
    try:
        print(f"🔗 Creating market: {event.title}")
        
        payload = {
            "title": event.title,
            "description": event.description,
            "category": event.category,
            "options": event.options,
            "source_url": event.source_url
        }
        
        response = requests.post(
            f"{BLOCKCHAIN_URL}/api/markets/create",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            market_id = result.get('id')
            print(f"✅ Market created: {market_id}")
            return market_id
        else:
            print(f"❌ Market creation failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Blockchain error: {e}")
        return None

# ============================================
# API ENDPOINTS
# ============================================

@app.get("/")
async def root():
    return {
        "name": "🤖 BlackBook URL Scraper",
        "version": "2.0.0",
        "status": "running",
        "openai": "enabled" if openai_client else "disabled",
        "blockchain": BLOCKCHAIN_URL,
        "endpoints": {
            "POST /scrape": "Scrape URL and create market",
            "GET /health": "Health check"
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "openai": "enabled" if openai_client else "disabled",
        "blockchain": BLOCKCHAIN_URL
    }

@app.post("/scrape")
async def scrape_url(request: URLRequest) -> ScrapeResponse:
    """Main endpoint: Scrape URL and create prediction market"""
    
    try:
        # Step 1: Scrape content
        scraped = scrape_content(str(request.url))
        
        # Step 2: AI analysis
        event = analyze_with_ai(scraped, request.category or "tech")
        
        # Step 3: Create market
        market_id = create_market(event)
        
        if market_id:
            return ScrapeResponse(
                success=True,
                market_id=market_id,
                event=event,
                message=f"✅ Market created from {urlparse(str(request.url)).netloc}"
            )
        else:
            return ScrapeResponse(
                success=False,
                event=event,
                message="⚠️ Event analyzed but market creation failed"
            )
            
    except Exception as e:
        return ScrapeResponse(
            success=False,
            message=f"❌ Error: {str(e)}"
        )

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 BlackBook URL Scraping AI Agent")
    print("=" * 60)
    print(f"🌐 Server: http://localhost:{PORT}")
    print(f"📚 Docs: http://localhost:{PORT}/docs")
    print(f"🔗 Blockchain: {BLOCKCHAIN_URL}")
    print(f"🤖 OpenAI: {'✅ Enabled' if openai_client else '❌ Disabled'}")
    print("=" * 60)
    print("\n🚀 Send POST to /scrape with URL to create prediction markets!")
    print("\n💡 Example:")
    print(f'curl -X POST http://localhost:{PORT}/scrape \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"url": "https://techcrunch.com/article"}\'')
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")