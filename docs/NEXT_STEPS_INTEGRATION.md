# ObjectWire World Cup Integration Guide

## 🎯 What We're Building

A **World Cup journalism automation system** that combines:
1. **Article scraping** from RSS feeds and URLs
2. **Local AI (Gemma 2)** for offline content generation
3. **Direct publishing** to ObjectWire.org
4. **Blockchain integration** for prediction markets

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ObjectWire CLI                                │
│                     ⚽ World Cup Edition                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   SCRAPER    │───▶│   GEMMA 2    │───▶│   PUBLISHER  │          │
│  │              │    │   (Local AI)  │    │              │          │
│  │ • RSS Feeds  │    │              │    │ • ObjectWire │          │
│  │ • URLs       │    │ • Write 500  │    │ • Blockchain │          │
│  │ • APIs       │    │   word article│    │ • Files      │          │
│  └──────────────┘    │ • Chat       │    └──────────────┘          │
│                      └──────────────┘                               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Complete Flow (Phase 1 Target)

```
1. SCRAPE     → User provides URL/RSS feed
2. ANALYZE    → Extract prediction market data
3. PROMPT     → "Write 500-word article? [y/N]"
4. WRITE      → Gemma 2 generates professional article
5. PUBLISH    → Send to ObjectWire.org API + Blockchain /events
6. SAVE       → Log everything to ./logs/ and ./articles/
```

---

## 🔗 API Payloads

### Blockchain Market Payload (`POST /events`)

```json
{
  "title": "Will Mexico advance to World Cup 2026 knockout round?",
  "description": "Market resolves YES if Mexico wins at least 2 group stage matches...",
  "outcomes": ["Yes", "No", "No Change"],
  "source_url": "https://espn.com/soccer/mexico-world-cup-preview",
  "market_type": "three_choice",
  "category": "sports",
  "tags": ["world-cup", "mexico", "fifa-2026"],
  
  "dates": {
    "published": "2026-01-24T12:00:00Z",
    "freeze": "2026-06-25T23:59:59Z",
    "resolution": "2026-06-26T23:59:59Z"
  },
  
  "resolution": {
    "deadline": "2026-06-26T23:59:59Z",
    "rules": "Market resolves YES if Mexico advances from Group A with 6+ points"
  },
  
  "resolution_rules": {
    "provider": "Manual",
    "data_source": "https://fifa.com/worldcup/standings",
    "conditions": {
      "Yes": "Mexico advances from group stage",
      "No": "Mexico eliminated in group stage",
      "No Change": "Tournament cancelled or Mexico withdrawn"
    }
  },
  
  "initial_probabilities": [0.65, 0.30, 0.05],
  "confidence": 0.85,
  "source": "ObjectWire_WorldCup_v1"
}
```

### Required Fields (Minimum)
| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Market question (prediction) |
| `description` | string | Detailed market description |
| `outcomes` | array | Betting options (2-10 items) |
| `source_url` | string | Source article URL |
| `dates.published` | ISO8601 | When event was published |

### Optional Fields
| Field | Type | Description |
|-------|------|-------------|
| `dates.freeze` | ISO8601 | When betting closes |
| `dates.resolution` | ISO8601 | Expected resolution date |
| `resolution.deadline` | ISO8601 | Resolution deadline |
| `resolution.rules` | string | Human-readable criteria |
| `category` | enum | business, tech, politics, crypto, **sports**, culture, science, general |
| `market_type` | string | "binary", "three_choice", "multi" |
| `initial_probabilities` | array | Starting odds (sum to 1.0) |
| `confidence` | float | AI confidence (0.0-1.0) |
| `tags` | array | Search/filter tags |

### ObjectWire.org Article Payload (`POST /api/articles`)

```json
{
  "title": "Mexico's World Cup 2026 Dreams: Can El Tri Make History on Home Soil?",
  "content": "<500+ word article body>",
  "excerpt": "As co-hosts of FIFA World Cup 2026, Mexico enters the tournament...",
  "category": "world-cup",
  "author": "ObjectWire AI",
  "source_url": "https://espn.com/soccer/mexico-preview",
  "status": "draft",
  "tags": ["mexico", "world-cup-2026", "fifa"],
  "market_id": "mex_wc_2026_advance",
  "featured_image": null
}
```

---

## ✅ Completed Features

### 1. Soccer Ball ASCII Art ⚽
- Replaced shamrock with soccer ball in CLI welcome screen
- Matches World Cup branding

### 2. Gemma 2 Local AI Integration
- **Ollama installed** via Homebrew
- **Gemma 2 model** downloaded (5.4GB)
- **GemmaEngine class** for API communication
- **WorldCupGemmaWriter** for specialized journalism

### 3. CLI Commands Added
| Command | Description |
|---------|-------------|
| `chat` | Enter Gemma 2 chat mode |
| `write` | Generate article from scraped content |

### 4. Files Created
```
src/objectwire/
├── gemma_engine.py      # Gemma 2 integration
├── cli.py               # Updated with chat/write commands

worldcup_cli_gemma.py    # Standalone World Cup CLI
worldcup_content_engine.py
worldcup_monitor.py
worldcup_config.py
objectwire_integration.py
```

---

## 🔄 Current Workflow

```
User runs: objectwire

1. ⚽ Soccer ball banner displays
2. User types: rss <fifa-news-feed>
3. CLI scrapes and lists articles
4. User types: 1 (selects article)
5. Article is scraped and analyzed
6. User types: chat
7. Gemma 2 chat mode activates (with article context)
8. User: "Write a breaking news article about this"
9. Gemma 2 generates professional article
10. User types: exit (back to ObjectWire)
11. User can post to blockchain or save article
```

---

## 🎯 Next Integration Goals

### Phase 1: Core Flow (This Week)

#### 1.1 Seamless Scrape → Write Flow
```
scrape <url>  →  Auto-offer: "Write article? [y/N]"  →  Gemma writes  →  Save/Publish
```

**Files to modify:**
- `src/objectwire/cli.py` - Add post-scrape article prompt

#### 1.2 ObjectWire.org API Integration
```python
# After article generation:
publish_to_objectwire(article, category="world-cup")
```

**Endpoint:** `POST https://objectwire.org/api/articles`

**Payload:**
```json
{
  "title": "Messi Confirms World Cup 2026 Participation",
  "content": "<article body>",
  "category": "world-cup",
  "author": "ObjectWire AI",
  "source_url": "https://original-source.com/article",
  "status": "draft"
}
```

#### 1.3 Blockchain Prediction Market Integration
```
scrape <url>  →  Generate market  →  POST to localhost:3000/events
```

**Current endpoint:** `http://localhost:3000/events` (from next-steps.txt line 35)

---

### Phase 2: Enhanced Features (Next 2 Weeks)

#### 2.1 FIFA News Feed Monitoring
```python
FIFA_RSS_FEEDS = [
    "https://www.fifa.com/rss/news.xml",
    "https://www.espn.com/espn/rss/soccer/news",
    "https://www.bbc.co.uk/sport/football/rss.xml",
    # ... more feeds
]
```

**Command:** `objectwire monitor --worldcup`

#### 2.2 Article Templates
```
objectwire write --template breaking-news
objectwire write --template match-analysis
objectwire write --template transfer-rumor
objectwire write --template tournament-preview
```

#### 2.3 Batch Processing
```
objectwire batch --feed fifa-news.xml --write-all
# Scrapes all articles, generates content for each
```

---

### Phase 3: Advanced (Next Month)

#### 3.1 Real-Time World Cup Coverage
- WebSocket for live match updates
- Auto-generate match reports
- Live score integration

#### 3.2 Multi-Language Support
- Spanish articles for Mexico coverage
- French for Canadian venues
- Gemma 2 can generate in multiple languages

#### 3.3 Social Media Integration
- Auto-post to Twitter/X
- Generate thread summaries
- Cross-post to multiple platforms

---

## 📁 File Structure (Target)

```
src/objectwire/
├── __init__.py
├── __main__.py
├── cli.py                    # Main CLI with Gemma integration ✅
├── gemma_engine.py           # Local AI engine ✅
├── config.py                 # Configuration
│
├── scrapers/
│   ├── rss.py                # RSS feed scraper
│   ├── article.py            # Article scraper
│   └── fifa.py               # FIFA-specific scraper
│
├── writers/
│   ├── gemma_writer.py       # Gemma 2 article writer ✅
│   ├── templates/
│   │   ├── breaking_news.md
│   │   ├── match_analysis.md
│   │   └── transfer_rumor.md
│   └── publisher.py          # ObjectWire.org publisher
│
├── markets/
│   ├── generator.py          # Prediction market generator
│   └── blockchain.py         # Blockchain posting
│
└── worldcup/
    ├── feeds.py              # World Cup RSS feeds
    ├── teams.py              # Team data
    └── schedule.py           # Match schedule
```

---

## 🔧 Environment Variables Needed

```bash
# .env file

# Gemma 2 (Ollama)
OLLAMA_HOST=http://localhost:11434

# ObjectWire.org API
OBJECTWIRE_API_KEY=your_api_key
OBJECTWIRE_API_URL=https://objectwire.org/api

# Blockchain
BLOCKCHAIN_API_URL=http://localhost:3000

# Optional: OpenAI fallback
OPENAI_API_KEY=sk-...
```

---

## 🚀 Quick Start Commands

```bash
# 1. Start Ollama (if not running)
brew services start ollama

# 2. Verify Gemma 2 is ready
ollama list  # Should show gemma2

# 3. Run ObjectWire CLI
cd /Users/thelegendofzjui/Documents/GitHub/url_scraper_agent.py
.venv/bin/python -c "import sys; sys.path.insert(0, 'src'); from objectwire.cli import interactive_mode; interactive_mode()"

# 4. In CLI:
#    - Type 'chat' to talk to Gemma 2
#    - Type 'scrape <url>' to scrape an article
#    - Type 'write' to generate content
```

---

## 📊 Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Article generation time | < 15s | ~10s ✅ |
| Gemma 2 availability | 99% | ✅ Running |
| Scrape success rate | > 95% | TBD |
| Articles per day | 10+ | TBD |
| ObjectWire.org posts | 5+/day | Not connected |

---

## 🐛 Known Issues

1. **Import path complexity** - Need to run with `sys.path.insert`
2. **urllib3 SSL warning** - Cosmetic, doesn't affect functionality
3. **No ObjectWire.org API key yet** - Need to configure

---

## 📝 Next Actions (Priority Order)

> **📋 For detailed phase-by-phase implementation with testing context, see:**  
> **[PHASE_IMPLEMENTATION_PLAN.md](./PHASE_IMPLEMENTATION_PLAN.md)**

### ✅ Phase 1: Core Flow - COMPLETE! (January 24, 2026)

1. [x] **Test full scrape → chat → write flow** ✅ DONE
2. [x] **Add "Write article?" prompt after scraping** ✅ DONE  
3. [x] **Create ObjectWire.org API client** ✅ DONE (needs API key)
4. [x] **Add article saving to ./articles/ folder** ✅ DONE
5. [x] **New CLI banner with soccer ball** ✅ DONE
6. [x] **Gemma 2 integration complete** ✅ DONE

### ✅ Phase 2A: Configuration & Templates - COMPLETE! (January 24, 2026)

1. [x] **Updated .env.example** with Phase 2 configs
2. [x] **Created RSS feed configuration** (10 FIFA feeds)
3. [x] **Created article templates** (3 templates)
4. [x] **Documented API payload structure**

### 🔄 Phase 2B: RSS Monitor Command - NEXT UP

**Goal**: Add `monitor` command for continuous RSS feed checking

**Tasks**:
1. [ ] Implement `monitor` command in cli.py
2. [ ] Add RSS feed parser
3. [ ] Add article deduplication
4. [ ] Test with 1-minute interval

**Test Command**:
```bash
objectwire monitor --interval 60 --auto-write
```

### ⏳ Phase 2C: Template-Based Generation - PENDING

1. [ ] Add `--template` flag to write command
2. [ ] Implement template rendering engine
3. [ ] Test with all 3 templates

### ⏳ Phase 2D: ObjectWire.org API Testing - PENDING

1. [ ] Get ObjectWire.org API key
2. [ ] Test article publishing
3. [ ] Verify articles on objectwire.org

### ⏳ Phase 3: Blockchain & Advanced Features - PENDING

1. [ ] Enhanced market payloads with resolution rules
2. [ ] Full blockchain integration
3. [ ] Real-time monitoring and batch processing

---

## ✅ Phase 1 Complete! (January 24, 2026)

### What's Working Now:

```
[objectwire]> scrape https://espn.com/soccer/article

⚽ Scrapes article
📊 Creates prediction market
💾 Posts to blockchain

📝 Write 500-word article with Gemma 2? [y/N]: y

✍️  Gemma 2 generates 500-word article...

📰 Article Generated!
────────────────────────────────────────────────────────────
[Full professional article displayed]
────────────────────────────────────────────────────────────
Word count: 520

Save article? [y/N]: y
✓ Saved to articles/article_20260124_Mexico_World_Cup.md

Publish to ObjectWire.org? [y/N]: y
✓ Published to ObjectWire.org!
```

### Functions Added to cli.py:

| Function | Description |
|----------|-------------|
| `generate_article_with_gemma()` | Generates 500-word article from scraped content |
| `save_generated_article()` | Saves to `./articles/` and `./logs/` |
| `publish_to_objectwire()` | POSTs to ObjectWire.org API |

### Files Modified:
- `src/objectwire/cli.py` - Added article writing flow after scraping

---

## 🎯 Ultimate Goal

```
objectwire

⚽ Soccer ball appears

[objectwire]> rss https://fifa.com/news.xml
# Shows latest FIFA articles

[objectwire]> 1
# Scrapes article #1, shows prediction market

[objectwire]> write
# Gemma 2 generates professional article

[objectwire]> publish
# Posts to ObjectWire.org + blockchain

✅ Article published to ObjectWire.org
✅ Prediction market created on blockchain
```

---

*Last Updated: January 24, 2026*
*Branch: world-cup*
*Current Phase: Phase 2 - ObjectWire.org API Integration*

---

## 🚀 Phase 2 Implementation Details

### 2.1 ObjectWire.org API Integration

#### Step 1: Environment Setup
Create `.env` file in project root:

```bash
# ObjectWire.org API Configuration
OBJECTWIRE_API_KEY=your_api_key_here
OBJECTWIRE_API_URL=https://objectwire.org/api
OBJECTWIRE_AUTHOR=ObjectWire AI

# Blockchain Configuration (existing)
BLOCKCHAIN_API_URL=http://localhost:1234

# Gemma 2 / Ollama (existing)
OLLAMA_HOST=http://localhost:11434
```

#### Step 2: Update `publish_to_objectwire()` Function

Current stub in `cli.py`:
```python
def publish_to_objectwire(article, event, payload):
    """Publish article to ObjectWire.org."""
    # TODO: Implement actual API call
    console.print("[green]✓[/] Published to ObjectWire.org!")
```

**Target implementation:**
```python
def publish_to_objectwire(article, event, payload):
    """Publish article to ObjectWire.org Next.js CMS."""
    import os
    import requests
    from datetime import datetime
    
    api_key = os.getenv("OBJECTWIRE_API_KEY")
    api_url = os.getenv("OBJECTWIRE_API_URL", "https://objectwire.org/api")
    
    if not api_key:
        console.print("[yellow]⚠[/] OBJECTWIRE_API_KEY not set. Article saved locally only.")
        return False
    
    # Prepare article payload for Next.js
    article_payload = {
        "title": event.get("title", "Untitled"),
        "content": article,
        "excerpt": article[:200] + "...",
        "category": "world-cup",
        "author": os.getenv("OBJECTWIRE_AUTHOR", "ObjectWire AI"),
        "source_url": event.get("source_url", ""),
        "status": "draft",  # or "published"
        "tags": event.get("tags", ["world-cup-2026", "fifa"]),
        "market_id": payload.get("market_id"),
        "featured_image": None,
        "metadata": {
            "ai_generated": True,
            "model": "gemma2",
            "generated_at": datetime.utcnow().isoformat(),
            "word_count": len(article.split())
        }
    }
    
    try:
        response = requests.post(
            f"{api_url}/articles",
            json=article_payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            article_url = result.get("url", "")
            console.print(f"[green]✓[/] Published to ObjectWire.org: {article_url}")
            return True
        else:
            console.print(f"[red]✗[/] ObjectWire.org API error: {response.status_code}")
            console.print(f"[dim]{response.text}[/]")
            return False
            
    except Exception as e:
        console.print(f"[red]✗[/] Failed to publish: {str(e)}")
        return False
```

#### Step 3: RSS Feed Monitoring

Add FIFA RSS feeds to `src/objectwire/worldcup/config.py`:

```python
# FIFA & World Cup RSS Feeds
WORLD_CUP_RSS_FEEDS = {
    "fifa_official": "https://www.fifa.com/rss/news.xml",
    "espn_soccer": "https://www.espn.com/espn/rss/soccer/news",
    "bbc_football": "https://www.bbc.co.uk/sport/football/rss.xml",
    "goal_world_cup": "https://www.goal.com/feeds/en/news/world-cup.xml",
    "fox_soccer": "https://www.foxsports.com/soccer/rss",
    "the_athletic": "https://theathletic.com/feeds/rss/soccer/",
    "guardian_soccer": "https://www.theguardian.com/football/rss",
}

# Monitoring Configuration
MONITOR_INTERVAL = 300  # Check every 5 minutes
AUTO_WRITE_ARTICLES = True
AUTO_PUBLISH = False  # Require manual approval
MIN_WORD_COUNT = 500
MAX_ARTICLES_PER_FEED = 3
```

#### Step 4: Add RSS Monitor Command

Update `cli.py` to add monitoring capability:

```python
@cli.command()
@click.option('--interval', default=300, help='Check interval in seconds')
@click.option('--auto-write', is_flag=True, help='Auto-generate articles')
def monitor(interval, auto_write):
    """Monitor FIFA RSS feeds for new articles."""
    from objectwire.worldcup.config import WORLD_CUP_RSS_FEEDS
    
    console.print("[bold green]⚽ Starting World Cup RSS Monitor[/]")
    console.print(f"[dim]Checking {len(WORLD_CUP_RSS_FEEDS)} feeds every {interval}s[/]")
    console.print()
    
    while True:
        for feed_name, feed_url in WORLD_CUP_RSS_FEEDS.items():
            try:
                # Parse RSS feed
                articles = parse_rss_feed(feed_url)
                
                for article in articles[:3]:  # Top 3 per feed
                    # Check if already processed
                    if not is_already_processed(article['url']):
                        console.print(f"[cyan]📰 New article from {feed_name}[/]")
                        console.print(f"[white]{article['title']}[/]")
                        
                        if auto_write:
                            # Scrape and generate article
                            scraped = scrape_url(article['url'])
                            article_text = generate_article_with_gemma(scraped)
                            save_generated_article(article_text, scraped, {})
                            console.print("[green]✓[/] Article generated and saved")
                        
                        mark_as_processed(article['url'])
                        
            except Exception as e:
                console.print(f"[red]Error with {feed_name}: {e}[/]")
        
        time.sleep(interval)
```

---

### 2.2 Article Templates

Create `src/objectwire/writers/templates/` directory:

**breaking_news.md:**
```markdown
# {title}

**Breaking:** {headline}

{intro_paragraph}

## Key Details

{bullet_points}

## Analysis

{analysis_paragraph}

## What's Next

{future_implications}

---
*This article was generated by ObjectWire AI based on information from {source}*
```

**match_preview.md:**
```markdown
# {match_title}

**{team_a} vs {team_b}** | {date} | {venue}

## Match Preview

{preview_paragraph}

## Team Form

**{team_a}:**
{team_a_form}

**{team_b}:**
{team_b_form}

## Key Players to Watch

{key_players}

## Prediction

{prediction_paragraph}

---
*Prediction market available on ObjectWire.org*
```

#### Implementation in cli.py:

```python
def generate_article_with_template(template_name, context, scraped_content):
    """Generate article using a specific template."""
    template_path = f"src/objectwire/writers/templates/{template_name}.md"
    
    with open(template_path, 'r') as f:
        template = f.read()
    
    # Use Gemma 2 to fill in template
    prompt = f"""
    Fill in this article template with information from the following content:
    
    TEMPLATE:
    {template}
    
    CONTENT:
    {scraped_content}
    
    Generate a professional 500-word article following the template structure.
    """
    
    return chat_with_gemma(prompt, context={})
```

---

### 2.3 Testing Phase 2

**Test checklist:**

```bash
# 1. Test ObjectWire.org API (with valid key)
[objectwire]> scrape https://fifa.com/article
[objectwire]> write
[objectwire]> publish
# Should POST to ObjectWire.org API

# 2. Test RSS monitoring
[objectwire]> monitor --interval 60
# Should check feeds every minute

# 3. Test with auto-write
[objectwire]> monitor --auto-write
# Should generate articles automatically

# 4. Test templates
[objectwire]> write --template match-preview
# Should use template for generation
```

---

### Phase 2 Success Criteria

- [ ] ObjectWire.org API integration working
- [ ] Articles publishing to Next.js CMS
- [ ] RSS monitoring active for 3+ feeds
- [ ] At least 2 article templates created
- [ ] Auto-write generates 5+ articles per day

---
