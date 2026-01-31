# ObjectWire World Cup Agent - Phase Implementation Plan

**Project**: World Cup 2026 Writing Agent  
**Start Date**: January 24, 2026  
**Current Phase**: Phase 2A  
**Branch**: world-cup  

---

## 🎯 Overview

This document breaks down the complete implementation into testable phases with clear milestones, context, and testing procedures.

---

## ✅ Phase 1: Core Infrastructure - COMPLETE

### Phase 1A: Local AI Setup ✅
**Goal**: Get Gemma 2 running locally for offline article generation

**Milestones**:
- [x] Install Ollama via Homebrew
- [x] Download Gemma 2 model (5.4GB)
- [x] Create `gemma_engine.py` wrapper
- [x] Test basic Gemma 2 connection

**Test Command**:
```bash
# Verify Gemma 2 is running
ollama list
curl http://localhost:11434/api/generate -d '{"model":"gemma2","prompt":"Hello"}'
```

**Success Criteria**: Gemma 2 responds to prompts in < 15 seconds

---

### Phase 1B: CLI Integration ✅
**Goal**: Add Gemma 2 to ObjectWire CLI

**Milestones**:
- [x] Add `chat` command for Gemma 2 interaction
- [x] Add `write` command for article generation
- [x] Update banner with soccer ball ASCII art
- [x] Add `gemma_is_available()` health check

**Test Command**:
```bash
cd /Users/thelegendofzjui/Documents/GitHub/url_scraper_agent.py
python3 -c "import sys; sys.path.insert(0, 'src'); from objectwire.cli import show_banner; show_banner()"
```

**Success Criteria**: Banner shows "🟢 Online" for Gemma 2

---

### Phase 1C: Article Writing Flow ✅
**Goal**: Auto-prompt for article writing after scraping

**Milestones**:
- [x] Add `generate_article_with_gemma()` function
- [x] Add `save_generated_article()` function
- [x] Add post-scrape "Write article?" prompt
- [x] Create `articles/` directory structure

**Test Command**:
```bash
# Test article generation
python3 -c "
import sys
sys.path.insert(0, 'src')
from objectwire.cli import generate_article_with_gemma

article = generate_article_with_gemma(
    'Mexico announces World Cup 2026 roster',
    {'title': 'Test', 'description': 'Test article'}
)
print(f'Generated {len(article.split())} words')
"
```

**Success Criteria**: Generates 500+ word articles, saves to `./articles/`

---

## 🔄 Phase 2: ObjectWire.org Integration - IN PROGRESS

### Phase 2A: Configuration & Templates ✅
**Goal**: Set up RSS feeds and article templates

**Milestones**:
- [x] Create `.env.example` with Phase 2 configs
- [x] Create `src/objectwire/worldcup/feeds.py` (10 RSS feeds)
- [x] Create 3 article templates (breaking_news, match_preview, team_analysis)
- [x] Document ObjectWire.org API payload structure

**Files Created**:
- `src/objectwire/worldcup/feeds.py`
- `src/objectwire/writers/templates/breaking_news.md`
- `src/objectwire/writers/templates/match_preview.md`
- `src/objectwire/writers/templates/team_analysis.md`

**Test Command**:
```bash
# Verify files exist
ls -la src/objectwire/worldcup/feeds.py
ls -la src/objectwire/writers/templates/
```

**Success Criteria**: All files created, RSS feeds listed

---

### Phase 2B: RSS Feed Monitor Command
**Goal**: Add `monitor` command to continuously check RSS feeds

**Milestones**:
- [ ] Add `monitor` command to `cli.py`
- [ ] Implement RSS feed parsing
- [ ] Add article deduplication (track processed URLs)
- [ ] Add filtering for World Cup keywords

**Implementation**:
```python
# In cli.py
@cli.command()
@click.option('--interval', default=300, help='Check interval in seconds')
@click.option('--auto-write', is_flag=True, help='Auto-generate articles')
@click.option('--feeds', multiple=True, help='Specific feeds to monitor')
def monitor(interval, auto_write, feeds):
    """Monitor FIFA RSS feeds for new World Cup articles."""
    pass  # To be implemented
```

**Test Command**:
```bash
# Run monitor in test mode (1 minute interval)
objectwire monitor --interval 60

# With auto-write enabled
objectwire monitor --auto-write --interval 300
```

**Success Criteria**: 
- Detects new articles from RSS feeds
- No duplicate processing
- Filters only World Cup content

---

### Phase 2C: Template-Based Article Generation
**Goal**: Use templates for structured article generation

**Milestones**:
- [ ] Add `--template` flag to `write` command
- [ ] Implement template variable extraction
- [ ] Create template rendering engine
- [ ] Add template validation

**Implementation**:
```python
def generate_article_with_template(template_name, scraped_content):
    """Generate article using a specific template."""
    template_path = f"src/objectwire/writers/templates/{template_name}.md"
    
    # Load template
    with open(template_path, 'r') as f:
        template = f.read()
    
    # Extract variables needed
    variables = extract_template_variables(template)
    
    # Use Gemma to fill in template
    prompt = f"""
    Fill in this article template with information from the content below.
    
    TEMPLATE:
    {template}
    
    CONTENT:
    {scraped_content}
    
    Generate a professional 500-word article following the template exactly.
    """
    
    return chat_with_gemma(prompt)
```

**Test Command**:
```bash
# Test breaking news template
objectwire scrape https://fifa.com/article --template breaking_news

# Test match preview template
objectwire scrape https://espn.com/soccer/match --template match_preview
```

**Success Criteria**: Articles follow template structure, 500+ words

---

### Phase 2D: ObjectWire.org API Testing
**Goal**: Test article publishing to live API

**Milestones**:
- [ ] Obtain ObjectWire.org API key
- [ ] Add API key to `.env` file
- [ ] Test `publish_to_objectwire()` function
- [ ] Verify articles appear on objectwire.org

**Setup**:
```bash
# Create .env file
cp .env.example .env

# Edit .env and add:
# OBJECTWIRE_API_KEY=your_actual_api_key_here
```

**Test Command**:
```bash
# Test publishing
objectwire scrape https://fifa.com/article
# When prompted: Write article? y
# When prompted: Publish to ObjectWire.org? y

# Verify it worked
curl https://objectwire.org/api/articles?category=world-cup
```

**Success Criteria**: 
- Article appears on ObjectWire.org
- Correct category and tags
- No API errors

---

## 🚀 Phase 3: Blockchain Integration

### Phase 3A: Market Payload Enhancement
**Goal**: Add full payload structure for blockchain markets

**Milestones**:
- [ ] Update `generate_market_payload()` with all fields
- [ ] Add resolution rules generation
- [ ] Add probability calculation
- [ ] Add market lifecycle states

**Implementation Details**:
```python
def generate_market_payload(event, article):
    """Generate complete blockchain market payload."""
    return {
        "title": event.title,
        "description": event.description,
        "outcomes": generate_outcomes(event),
        "source_url": event.source_url,
        "market_type": "three_choice",  # or binary/multi
        "category": "sports",
        "tags": ["world-cup-2026", "fifa"],
        
        # Enhanced fields
        "dates": {
            "published": datetime.utcnow().isoformat(),
            "freeze": calculate_freeze_date(event),
            "resolution": calculate_resolution_date(event)
        },
        
        "resolution": {
            "deadline": calculate_resolution_deadline(event),
            "rules": generate_resolution_rules(event)
        },
        
        "initial_probabilities": calculate_probabilities(event),
        "confidence": calculate_confidence(article),
        "source": "ObjectWire_WorldCup_v1"
    }
```

**Test Command**:
```bash
# Test payload generation
python3 -c "
import sys
sys.path.insert(0, 'src')
from objectwire.cli import generate_market_payload
import json

payload = generate_market_payload({...})
print(json.dumps(payload, indent=2))
"
```

**Success Criteria**: Valid payload with all required fields

---

### Phase 3B: Blockchain Posting
**Goal**: Post markets to blockchain endpoint

**Milestones**:
- [ ] Update `post_to_blockchain()` function
- [ ] Add retry logic for failed posts
- [ ] Add transaction verification
- [ ] Log all blockchain interactions

**Test Command**:
```bash
# Test blockchain posting
objectwire scrape https://fifa.com/article
# Should auto-post to http://localhost:1234/events

# Verify on blockchain
curl http://localhost:1234/events | jq
```

**Success Criteria**: Markets appear on blockchain, valid transaction hashes

---

### Phase 3C: Market Resolution
**Goal**: Handle market resolution and outcomes

**Milestones**:
- [ ] Add resolution tracking
- [ ] Implement resolution rules parser
- [ ] Add manual resolution UI
- [ ] Create resolution history log

**Test Command**:
```bash
# Mark market as resolved
objectwire resolve --market-id mex_wc_2026_advance --outcome "Yes"

# View resolution history
objectwire resolutions --date 2026-01-24
```

**Success Criteria**: Markets resolve correctly, payouts calculated

---

## 🎨 Phase 4: Enhanced Features

### Phase 4A: Batch Processing
**Goal**: Process multiple articles at once

**Milestones**:
- [ ] Add `batch` command
- [ ] Implement parallel processing
- [ ] Add progress tracking
- [ ] Generate summary reports

**Test Command**:
```bash
# Process all articles from feed
objectwire batch --feed https://fifa.com/rss/news.xml --limit 10

# Process multiple feeds
objectwire batch --all-feeds --auto-write --auto-publish
```

**Success Criteria**: Processes 10+ articles in < 5 minutes

---

### Phase 4B: Real-Time Match Coverage
**Goal**: Generate live match reports

**Milestones**:
- [ ] Integrate with live score APIs
- [ ] Create match report templates
- [ ] Add auto-update on goal events
- [ ] Generate post-match analysis

**Test Command**:
```bash
# Start live match coverage
objectwire live-match --match-id usa_vs_mexico --interval 60

# Generate match report
objectwire match-report --match-id usa_vs_mexico
```

**Success Criteria**: Updates every minute, generates final report

---

### Phase 4C: Multi-Language Support
**Goal**: Generate articles in Spanish, French, English

**Milestones**:
- [ ] Add language detection
- [ ] Implement translation with Gemma 2
- [ ] Create language-specific templates
- [ ] Add language routing for publishing

**Test Command**:
```bash
# Generate in Spanish
objectwire scrape https://fifa.com/article --lang es

# Generate in all languages
objectwire scrape https://fifa.com/article --lang all
```

**Success Criteria**: Articles in 3 languages, proper grammar

---

## 🛠️ Phase 5: Deployment & Automation

### Phase 5A: Helper Scripts
**Goal**: Create easy deployment and management scripts

**Milestones**:
- [ ] Create `setup.sh` installer
- [ ] Create `start.sh` launcher
- [ ] Create `monitor.sh` daemon
- [ ] Create `deploy.sh` for production

**Files to Create**:
```bash
scripts/
├── setup.sh          # Full installation
├── start.sh          # Start ObjectWire
├── monitor.sh        # Start RSS monitoring daemon
├── deploy.sh         # Deploy to production
└── test-all.sh       # Run all tests
```

**Test Command**:
```bash
# Run setup
./scripts/setup.sh

# Start monitoring
./scripts/monitor.sh --daemon

# Run tests
./scripts/test-all.sh
```

**Success Criteria**: One-command setup and deployment

---

### Phase 5B: Docker Containerization
**Goal**: Package as Docker container

**Milestones**:
- [ ] Create `Dockerfile`
- [ ] Create `docker-compose.yml`
- [ ] Add environment configuration
- [ ] Test container deployment

**Test Command**:
```bash
# Build container
docker build -t objectwire:latest .

# Run container
docker-compose up -d

# Test in container
docker exec objectwire objectwire status
```

**Success Criteria**: Runs in Docker, persistent storage works

---

### Phase 5C: Production Deployment
**Goal**: Deploy to production server

**Milestones**:
- [ ] Set up production server
- [ ] Configure domain and SSL
- [ ] Set up monitoring/logging
- [ ] Configure auto-restart

**Test Command**:
```bash
# Deploy to production
./scripts/deploy.sh production

# Check health
curl https://objectwire.org/health
```

**Success Criteria**: 24/7 uptime, auto-recovery

---

## 📊 Testing Strategy

### Unit Tests
```bash
# Run all unit tests
pytest tests/

# Test specific component
pytest tests/test_gemma_engine.py
pytest tests/test_rss_monitor.py
```

### Integration Tests
```bash
# Test full scrape → write → publish flow
./scripts/test-integration.sh

# Test RSS monitoring for 5 minutes
./scripts/test-monitor.sh --duration 300
```

### End-to-End Tests
```bash
# Test complete workflow
./scripts/test-e2e.sh

# Expected output:
# ✓ Scraped article
# ✓ Generated 523-word article
# ✓ Saved to articles/
# ✓ Published to ObjectWire.org
# ✓ Posted to blockchain
```

---

## 🎯 Current Status

| Phase | Status | Completion |
|-------|--------|-----------|
| Phase 1A: Local AI Setup | ✅ Complete | 100% |
| Phase 1B: CLI Integration | ✅ Complete | 100% |
| Phase 1C: Article Writing | ✅ Complete | 100% |
| **Phase 2A: Configuration** | **✅ Complete** | **100%** |
| **Phase 2B: RSS Monitor** | **🔄 In Progress** | **0%** |
| Phase 2C: Templates | ⏳ Pending | 0% |
| Phase 2D: API Testing | ⏳ Pending | 0% |
| Phase 3A: Market Payload | ⏳ Pending | 0% |
| Phase 3B: Blockchain | ⏳ Pending | 0% |
| Phase 3C: Resolution | ⏳ Pending | 0% |
| Phase 4A: Batch Processing | ⏳ Pending | 0% |
| Phase 4B: Live Coverage | ⏳ Pending | 0% |
| Phase 4C: Multi-Language | ⏳ Pending | 0% |
| Phase 5A: Helper Scripts | ⏳ Pending | 0% |
| Phase 5B: Docker | ⏳ Pending | 0% |
| Phase 5C: Production | ⏳ Pending | 0% |

---

## 🚦 Next Actions

### Immediate (This Week)
1. ✅ Complete Phase 2A (Configuration)
2. 🔄 Start Phase 2B (RSS Monitor Command)
3. ⏳ Test Phase 2C (Template Generation)

### Short-Term (Next 2 Weeks)
1. Complete Phase 2D (ObjectWire.org API)
2. Start Phase 3A (Enhanced Market Payloads)
3. Begin Phase 3B (Blockchain Integration)

### Medium-Term (Next Month)
1. Complete Phase 3 (Full Blockchain)
2. Start Phase 4 (Enhanced Features)
3. Create helper scripts (Phase 5A)

### Long-Term (Next 2-3 Months)
1. Multi-language support
2. Docker deployment
3. Production launch

---

## 📝 Notes

- Each phase should be fully tested before moving to next
- Document any issues in GitHub Issues
- Update this document as phases complete
- Tag releases at major milestones

---

*Last Updated: January 24, 2026*  
*Next Milestone: Phase 2B - RSS Monitor Command*  
*Expected Completion: January 25, 2026*
