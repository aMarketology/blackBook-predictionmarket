# 🏗️ Implementation Blueprint: Offline LLM + Telegram Bot + Scheduler

## Overview
This blueprint outlines how to enhance your URL scraping agent with:
1. **Offline AI/LLM** using Ollama (runs locally, no API costs)
2. **Telegram Bot** for remote control and notifications
3. **Scheduler** for automated scraping at specific times
4. **Reminder System** for notifications

---

## 🧠 Part 1: Offline AI/LLM Integration (Ollama)

### What is Ollama?
- **Local LLM server** that runs models like Llama 3, Mistral, Phi-3 on your Mac
- No internet required after model download
- No API costs (unlike OpenAI)
- Privacy-focused (data never leaves your machine)

### How It Works:
```
┌─────────────────┐
│  Your Scraper   │
│                 │
│  serve_frontend │
└────────┬────────┘
         │
         ├──► Option 1: OpenAI API (internet, costs money)
         │    POST https://api.openai.com/v1/chat/completions
         │
         └──► Option 2: Ollama (local, free, offline)
              POST http://localhost:11434/api/generate
```

### Implementation Plan:

#### Step 1: Install Ollama
```bash
# Download Ollama for Mac
brew install ollama

# Pull a model (one-time, ~4GB download)
ollama pull llama3.2:3b  # Small, fast model
# OR
ollama pull mistral      # More powerful, slower
```

#### Step 2: Modify `serve_frontend.py`
Add a new function `analyze_with_ollama()`:

```python
def analyze_with_ollama(scraped: Dict, category: str, model: str = "llama3.2:3b") -> PredictionEvent:
    """
    Use local Ollama LLM instead of OpenAI
    """
    import requests
    
    prompt = f"""
    Analyze this article and create a prediction market event.
    
    Title: {scraped['title']}
    Content: {scraped['content'][:2000]}
    
    Generate:
    1. A clear prediction question (title)
    2. Description (2-3 sentences)
    3. 2-4 prediction options
    4. Confidence score (0-1)
    5. Resolution date
    
    Return as JSON.
    """
    
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False}
    )
    
    # Parse and return PredictionEvent
```

#### Step 3: Add Configuration
In `.env`:
```bash
# AI Configuration
AI_PROVIDER=ollama          # Options: openai, ollama, mock
OLLAMA_MODEL=llama3.2:3b    # Model to use
OLLAMA_URL=http://localhost:11434
```

### Pros/Cons:

**✅ Pros:**
- Free (no API costs)
- Works offline
- Private (data stays local)
- Fast response (no network latency)

**❌ Cons:**
- Requires ~8GB RAM
- Initial model download (~4GB)
- Quality depends on model chosen
- Only works on your machine

---

## 💬 Part 2: Telegram Bot Integration

### How It Works:
```
┌──────────────┐        ┌─────────────────┐        ┌──────────────┐
│   You on     │  msg   │  Telegram Bot   │  HTTP  │  Your Agent  │
│   Telegram   │ ─────► │  (telegram_bot  │ ─────► │  serve_      │
│              │        │   .py)          │        │  frontend.py │
└──────────────┘        └─────────────────┘        └──────────────┘
                               │
                               │ sends notifications
                               ▼
                        ┌──────────────┐
                        │  You on      │
                        │  Telegram    │
                        └──────────────┘
```

### Features:

#### Commands:
1. **`/scrape <URL>`** - Scrape a URL immediately
   ```
   You: /scrape https://techcrunch.com/article
   Bot: 🔄 Scraping URL...
   Bot: ✅ Event created: ai_market_xyz123
        Title: Will GPT-5 launch in 2025?
        Options: Yes, No
   ```

2. **`/schedule <URL> <time>`** - Schedule scraping for later
   ```
   You: /schedule https://example.com tomorrow 9am
   Bot: ⏰ Scheduled for Nov 5, 2025 at 9:00 AM
        Job ID: job_abc123
   ```

3. **`/list`** - Show scheduled jobs
   ```
   Bot: 📋 Scheduled Jobs:
        1. https://example.com - Nov 5, 9:00 AM
        2. https://news.com - Nov 6, 2:00 PM
   ```

4. **`/cancel <job_id>`** - Cancel a scheduled job
   ```
   You: /cancel job_abc123
   Bot: ❌ Job cancelled
   ```

5. **`/status`** - Check agent health
   ```
   Bot: ✅ Agent Status:
        - AI: Ollama (llama3.2:3b)
        - Blockchain: Connected
        - Jobs: 3 scheduled
   ```

### Implementation Components:

#### File: `telegram_bot.py`
```python
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AGENT_URL = "http://localhost:8082"

async def scrape_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /scrape command"""
    url = context.args[0]
    
    # Send "processing" message
    await update.message.reply_text(f"🔄 Scraping {url}...")
    
    # Call your scraper
    response = requests.post(f"{AGENT_URL}/scrape", json={"url": url})
    
    # Send result
    if response.ok:
        data = response.json()
        await update.message.reply_text(
            f"✅ Event created!\n"
            f"Title: {data['title']}\n"
            f"ID: {data['market_id']}"
        )
```

### Setup Steps:

1. **Create Telegram Bot**
   - Talk to [@BotFather](https://t.me/botfather) on Telegram
   - Send `/newbot`
   - Get your `TELEGRAM_BOT_TOKEN`

2. **Add to `.env`**
   ```bash
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_CHAT_ID=your_chat_id  # Your personal chat ID
   ```

3. **Run the bot**
   ```bash
   python telegram_bot.py
   ```

---

## ⏰ Part 3: Scheduler System

### How It Works:
```
┌─────────────────────┐
│  APScheduler        │  ◄─── Stores jobs in SQLite DB
│  (Background)       │
│                     │
│  Jobs:              │
│  • Job 1: 9:00 AM   │ ──► Triggers scraping
│  • Job 2: 2:00 PM   │ ──► Sends to blockchain
│  • Job 3: Daily     │ ──► Sends Telegram notification
└─────────────────────┘
```

### Use Cases:

#### 1. **Recurring Scrapes**
Scrape a news site every day at 9 AM:
```python
scheduler.add_job(
    func=scrape_and_create_market,
    trigger='cron',
    hour=9,
    minute=0,
    args=['https://techcrunch.com']
)
```

#### 2. **One-Time Future Scrapes**
Scrape in 2 hours:
```python
scheduler.add_job(
    func=scrape_and_create_market,
    trigger='date',
    run_date=datetime.now() + timedelta(hours=2),
    args=['https://example.com']
)
```

#### 3. **Interval-Based**
Scrape every 6 hours:
```python
scheduler.add_job(
    func=scrape_and_create_market,
    trigger='interval',
    hours=6,
    args=['https://news.com']
)
```

### Implementation:

#### File: `scheduler_service.py`
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

# Persistent job storage (survives restarts)
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}

scheduler = BackgroundScheduler(jobstores=jobstores)
scheduler.start()

def add_scheduled_scrape(url: str, schedule_time: datetime, user_chat_id: str):
    """Add a new scheduled scraping job"""
    job = scheduler.add_job(
        func=scrape_and_notify,
        trigger='date',
        run_date=schedule_time,
        args=[url, user_chat_id],
        id=f"scrape_{url}_{int(time.time())}"
    )
    return job.id

def scrape_and_notify(url: str, chat_id: str):
    """Scrape URL and send Telegram notification"""
    result = run_pipeline(url, create_market_flag=True)
    
    # Send notification via Telegram
    send_telegram_message(
        chat_id,
        f"✅ Scheduled scrape complete!\n"
        f"URL: {url}\n"
        f"Event: {result['event']['title']}"
    )
```

---

## 🔔 Part 4: Reminder/Notification System

### Notification Types:

#### 1. **Job Completion Notifications**
```
✅ Scraping Complete!
URL: https://techcrunch.com/article
Event Created: ai_market_xyz123
Title: Will GPT-5 launch in Q1 2025?
Options: Yes, No, Delayed
Confidence: 85%
```

#### 2. **Job Failure Notifications**
```
❌ Scraping Failed!
URL: https://broken-site.com
Error: Connection timeout after 3 retries
Time: Nov 4, 2025 10:30 AM
```

#### 3. **Scheduled Reminders**
```
⏰ Reminder: Scheduled job in 10 minutes
URL: https://example.com
Scheduled for: 3:00 PM
```

#### 4. **Daily Summary**
```
📊 Daily Report - Nov 4, 2025
Events Created: 5
Successful: 4
Failed: 1
Scheduled Jobs: 3 pending
```

### Implementation:

#### File: `notification_service.py`
```python
import requests

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def send_telegram_message(chat_id: str, message: str):
    """Send a message via Telegram"""
    requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
    )

def notify_job_complete(chat_id: str, result: Dict):
    """Send completion notification"""
    message = f"""
✅ *Scraping Complete!*

URL: {result['url']}
Event: `{result['event']['title']}`
Market ID: `{result['market_id']}`
Confidence: {result['event']['confidence']*100}%
"""
    send_telegram_message(chat_id, message)

def notify_job_failed(chat_id: str, url: str, error: str):
    """Send failure notification"""
    message = f"""
❌ *Scraping Failed!*

URL: {url}
Error: {error}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    send_telegram_message(chat_id, message)
```

---

## 🏗️ Overall Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Your Mac/Computer                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Ollama (Local LLM)                                   │  │
│  │  - Runs on http://localhost:11434                     │  │
│  │  - Models: llama3.2, mistral, etc.                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ▲                                   │
│                          │                                   │
│  ┌──────────────────────┼───────────────────────────────┐  │
│  │  serve_frontend.py   │                               │  │
│  │  (Main Scraper)      │                               │  │
│  │  - Scrapes URLs      │                               │  │
│  │  - Calls Ollama ─────┘                               │  │
│  │  - Posts to blockchain                               │  │
│  │  - Saves logs                                        │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                          ▲                                   │
│                          │ HTTP                              │
│  ┌──────────────────────┼───────────────────────────────┐  │
│  │  telegram_bot.py     │                               │  │
│  │  - Receives commands │                               │  │
│  │  - Triggers scraping ┘                               │  │
│  │  - Sends notifications                               │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                          ▲                                   │
│                          │                                   │
│  ┌──────────────────────┼───────────────────────────────┐  │
│  │  scheduler_service.py│                               │  │
│  │  - APScheduler       │                               │  │
│  │  - Runs jobs at set times                           │  │
│  │  - Stores jobs in SQLite (jobs.sqlite)              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Internet
                          ▼
           ┌─────────────────────────────┐
           │  Telegram Servers            │
           │  (sends/receives messages)   │
           └─────────────────────────────┘
                          │
                          ▼
           ┌─────────────────────────────┐
           │  Your Phone (Telegram App)   │
           │  - Send commands             │
           │  - Receive notifications     │
           └─────────────────────────────┘
```

---

## 📋 Example Workflows

### Workflow 1: Manual Scraping via Telegram
```
1. You send to Telegram bot:
   /scrape https://techcrunch.com/article

2. Telegram bot receives command
   ↓
3. telegram_bot.py calls serve_frontend.py
   ↓
4. serve_frontend.py scrapes the URL
   ↓
5. serve_frontend.py calls Ollama for AI analysis
   ↓
6. serve_frontend.py posts to blockchain
   ↓
7. telegram_bot.py sends you notification:
   "✅ Event created: ai_market_xyz123"
```

### Workflow 2: Scheduled Scraping
```
1. You send to Telegram bot:
   /schedule https://news.com tomorrow 9am

2. scheduler_service.py creates job in SQLite DB
   ↓
3. [Wait until tomorrow 9am]
   ↓
4. APScheduler triggers the job
   ↓
5. Scraping happens automatically
   ↓
6. telegram_bot.py sends notification:
   "✅ Scheduled scrape complete!"
```

### Workflow 3: Recurring Daily Scrapes
```
1. You configure in config file:
   DAILY_SCRAPES = [
     "https://techcrunch.com",
     "https://coindesk.com"
   ]

2. scheduler_service.py sets up cron jobs:
   - Every day at 9:00 AM
   ↓
3. Automatic scraping happens daily
   ↓
4. You get a notification each time
   ↓
5. End of day: Summary report sent
   "📊 Today: 2 events created"
```

---

## 📦 New Dependencies

Add to `requirements.txt`:
```txt
# Existing dependencies...

# Local LLM
requests>=2.31.0  # Already have this

# Telegram Bot
python-telegram-bot==20.7

# Scheduler
APScheduler==3.10.4

# Database for persistent jobs
sqlalchemy==2.0.23
```

---

## 🚀 Startup Sequence

### Option 1: All-in-One Script
Create `start_all.sh`:
```bash
#!/bin/bash
# Start all services

# 1. Start Ollama (if not running)
ollama serve &

# 2. Start the scheduler
python scheduler_service.py &

# 3. Start the Telegram bot
python telegram_bot.py &

# 4. Keep running
wait
```

### Option 2: Individual Services
```bash
# Terminal 1: Ollama
ollama serve

# Terminal 2: Telegram Bot
python telegram_bot.py

# Terminal 3: Manual scraping
python serve_frontend.py --url "https://example.com"
```

---

## 🎯 Configuration File

Create `config.yaml`:
```yaml
# AI Configuration
ai:
  provider: ollama  # Options: openai, ollama, mock
  ollama:
    url: http://localhost:11434
    model: llama3.2:3b
  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4

# Telegram Configuration
telegram:
  bot_token: ${TELEGRAM_BOT_TOKEN}
  chat_id: ${TELEGRAM_CHAT_ID}
  notifications:
    on_success: true
    on_failure: true
    daily_summary: true
    summary_time: "18:00"  # 6 PM

# Scheduler Configuration
scheduler:
  timezone: America/New_York
  persist_jobs: true
  database: sqlite:///jobs.sqlite

# Blockchain Configuration
blockchain:
  url: http://localhost:3000
  enabled: true

# Recurring Scrapes
recurring_scrapes:
  - url: https://techcrunch.com
    schedule: "0 9 * * *"  # Every day at 9 AM
    category: tech
  
  - url: https://coindesk.com
    schedule: "0 14 * * *"  # Every day at 2 PM
    category: crypto
```

---

## 🔒 Security Considerations

1. **Telegram Bot Token**: Keep secret, don't commit to Git
2. **Chat ID Whitelist**: Only allow specific Telegram users
3. **Rate Limiting**: Prevent spam scraping
4. **Input Validation**: Sanitize URLs before scraping

---

## 📈 Future Enhancements

1. **Web Dashboard**: View all events and jobs in a browser
2. **Multiple Users**: Support team collaboration
3. **Analytics**: Track scraping success rates
4. **Auto-Resolution**: Automatically resolve prediction markets
5. **Price Monitoring**: Alert on prediction market price changes

---

## ❓ Questions to Consider

Before implementation:

1. **Which LLM model?**
   - Small/Fast: `llama3.2:3b` (4GB, fast responses)
   - Powerful: `mistral:7b` (4GB, better quality)
   - Best: `llama3:8b` (7GB, highest quality)

2. **Notification frequency?**
   - Immediate on every scrape?
   - Daily summary only?
   - Both?

3. **Who can use the bot?**
   - Just you?
   - Your team?
   - Need authentication?

4. **Scheduling needs?**
   - One-time future scrapes?
   - Recurring daily/hourly?
   - Interval-based (every X hours)?

---

## 🎓 Summary

This blueprint gives you:
- **Offline AI**: No API costs, works without internet
- **Telegram Control**: Scrape from anywhere via your phone
- **Automation**: Set it and forget it with scheduled jobs
- **Notifications**: Know immediately when events are created

**Next Steps**: Review this blueprint and let me know:
1. Which features you want first
2. Any modifications to the design
3. Ready to start implementation?
