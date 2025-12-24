# 📋 Quick Reference Cheat Sheet

## 🚀 One-Line Commands (Copy & Paste)

### Scrape with Mock AI (No API Key Needed)
```bash
python3 serve_frontend.py --url "https://techcrunch.com/article" --ai-mock
```

### Scrape and Post to Blockchain
```bash
python3 serve_frontend.py --url "https://news.com/article" --create-market --enable-blockchain
```

### Get JSON Output
```bash
python3 serve_frontend.py --url "https://example.com" --ai-mock --json
```

### Test Blockchain Connection
```bash
python3 serve_frontend.py --test-blockchain
```

---

## 📁 File Locations

| What | Where |
|------|-------|
| Main scraper | `serve_frontend.py` |
| Config | `.env` |
| Logs | `logs/` folder |
| Latest event | `logs/run_*_event.json` (newest) |
| Raw scraped data | `logs/run_*_scraped.json` |

---

## 🔧 Quick Checks

### View Latest Scraped Events
```bash
ls -lt logs/*.json | head -4
cat logs/run_*_event.json | tail -20
```

### Check Python & Packages
```bash
python3 --version
pip3 list | grep -E "requests|beautifulsoup|openai"
```

### Check Blockchain is Running
```bash
curl http://localhost:3000/health
```

---

## ⚡ Command Flags

| Flag | What It Does |
|------|--------------|
| `--url <URL>` | Website to scrape |
| `--ai-mock` | Use mock AI (no OpenAI key) |
| `--create-market` | Create prediction market |
| `--enable-blockchain` | Post to blockchain |
| `--json` | Output as JSON |
| `--test-blockchain` | Test connection |

---

## 🆘 Quick Fixes

### "Module not found" error
```bash
pip3 install -r requirements.txt
```

### Can't connect to blockchain
```bash
# Make sure blockchain is running on port 3000
curl http://localhost:3000/health
```

### Reinstall everything
```bash
./setup.sh
```

---

## 📊 Example Workflows

### Workflow 1: Quick Test
```bash
cd /Users/thelegendofzjui/Documents/GitHub/url_scraper_agent.py
python3 serve_frontend.py --url "https://techcrunch.com" --ai-mock
```

### Workflow 2: Production Scrape
```bash
cd /Users/thelegendofzjui/Documents/GitHub/url_scraper_agent.py
python3 serve_frontend.py \
  --url "https://www.objectwire.org/article" \
  --create-market \
  --enable-blockchain
```

### Workflow 3: Check Results
```bash
# See newest events
ls -lt logs/ | head -5

# Read last event
cat $(ls -t logs/*_event.json | head -1)
```

---

## 🎯 Your Successful Commands

You've already run these successfully:

```bash
# Tesla article
python3 serve_frontend.py \
  --url "https://www.objectwire.org/tesla-can-now-test-its-autonomous-vehicle-technology-on-public-streets-in-nevada" \
  --create-market --enable-blockchain

# Zelle article
python3 serve_frontend.py \
  --url "https://www.objectwire.org/zelle-payment-processor-goes-global-to-allow-crypto-stablecoins-for-international-transactions" \
  --create-market --enable-blockchain
```

Both created events successfully! ✅

---

## 📚 Documentation

- **INSTALL_GUIDE.md** - Complete installation guide
- **README.md** - Full documentation
- **IMPLEMENTATION_BLUEPRINT.md** - Future features
- **This file (QUICKSTART.md)** - Quick reference

---

## 🎉 TL;DR

**You're already set up!** Just run:

```bash
cd /Users/thelegendofzjui/Documents/GitHub/url_scraper_agent.py
python3 serve_frontend.py --url "YOUR_URL_HERE" --create-market --enable-blockchain
```

Done! 🚀
