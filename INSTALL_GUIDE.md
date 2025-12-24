# 📦 Installation Guide - BlackBook URL Scraping AI Agent

## ✅ What's Already Done

You already have:
- ✅ Python 3.9.6 installed
- ✅ All required packages installed (requests, beautifulsoup4, fastapi, openai, etc.)
- ✅ Project files in place
- ✅ Successfully scraped 2 URLs!

---

## 🚀 Quick Start (You Can Use It Right Now!)

### Option 1: Command Line Scraping (Simplest)

```bash
cd /Users/thelegendofzjui/Documents/GitHub/url_scraper_agent.py

# Scrape a URL with mock AI (no OpenAI key needed)
python3 serve_frontend.py --url "https://example.com" --ai-mock

# Scrape and create market on blockchain
python3 serve_frontend.py --url "https://example.com" --create-market --enable-blockchain
```

### Option 2: Run as API Server

```bash
# Start the server (not implemented yet, but can be added)
# This would let you use curl or Postman
```

---

## 🔧 Full Installation (If Starting Fresh)

If you were installing on a new machine, here's what you'd do:

### 1. Install Python 3.8+
```bash
# Check if Python is installed
python3 --version

# If not installed, get it from:
# https://www.python.org/downloads/
# OR use Homebrew:
brew install python3
```

### 2. Clone the Repository
```bash
cd ~/Documents/GitHub
git clone <your-repo-url> url_scraper_agent.py
cd url_scraper_agent.py
```

### 3. Install Dependencies
```bash
pip3 install -r requirements.txt
```

### 4. Set Up Environment (Optional)
```bash
# Copy the example environment file
cp .env.example .env

# Edit with your settings
nano .env
```

Add your API keys:
```bash
# OpenAI (optional, can use --ai-mock instead)
OPENAI_API_KEY=sk-your-key-here

# Blockchain URL
BLOCKCHAIN_API_URL=http://localhost:3000

# Agent port
AGENT_PORT=8082

# Enable blockchain posting
ALLOW_CREATE_MARKET=1
```

### 5. Test the Installation
```bash
# Test scraping with mock AI
python3 serve_frontend.py --url "https://techcrunch.com" --ai-mock

# Test blockchain connection
python3 serve_frontend.py --test-blockchain
```

---

## 📁 Project Structure

```
url_scraper_agent.py/
├── serve_frontend.py          # Main scraper (CLI version)
├── url_scraper.py            # API version (needs update)
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── IMPLEMENTATION_BLUEPRINT.md  # Feature blueprint
├── README.md                # Documentation
├── logs/                    # Scraped data and events
│   ├── run_*_scraped.json  # Raw scraped content
│   └── run_*_event.json    # Generated events
└── src/objectwire/          # ObjectWire integration
```

---

## 🎯 How to Use

### Basic Usage

```bash
# 1. Scrape a URL (mock AI, no blockchain)
python3 serve_frontend.py --url "https://example.com" --ai-mock

# 2. Scrape and create blockchain event
python3 serve_frontend.py --url "https://example.com" --create-market --enable-blockchain

# 3. Get JSON output
python3 serve_frontend.py --url "https://example.com" --ai-mock --json

# 4. Test blockchain connection
python3 serve_frontend.py --test-blockchain
```

### Examples You've Already Done

```bash
# Tesla article
python3 serve_frontend.py \
  --url "https://www.objectwire.org/tesla-can-now-test-its-autonomous-vehicle-technology-on-public-streets-in-nevada" \
  --create-market --enable-blockchain

# Zelle crypto article  
python3 serve_frontend.py \
  --url "https://www.objectwire.org/zelle-payment-processor-goes-global-to-allow-crypto-stablecoins-for-international-transactions" \
  --create-market --enable-blockchain
```

---

## 🔍 Check Your Results

```bash
# See all scraped data
ls -lh logs/

# View the latest event
cat logs/run_*_event.json | tail -20

# View raw scraped content
cat logs/run_*_scraped.json | head -50
```

---

## ⚙️ Configuration Options

### Command Line Flags

| Flag | Description |
|------|-------------|
| `--url <URL>` | URL to scrape (required) |
| `--ai-mock` | Use mock AI (no OpenAI key needed) |
| `--create-market` | Create a prediction market |
| `--enable-blockchain` | Post to blockchain (requires ALLOW_CREATE_MARKET=1) |
| `--json` | Output as JSON |
| `--test-blockchain` | Test blockchain connection |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | None | OpenAI API key |
| `BLOCKCHAIN_API_URL` | `http://localhost:3000` | Blockchain endpoint |
| `AGENT_PORT` | `8082` | API server port |
| `ALLOW_CREATE_MARKET` | `0` | Enable blockchain posting |

---

## 🚨 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'requests'"
```bash
pip3 install -r requirements.txt
```

### Error: "Connection refused" to blockchain
```bash
# Make sure your blockchain is running on port 3000
# Test with:
curl http://localhost:3000/health
```

### Error: "OpenAI API key not found"
```bash
# Use --ai-mock flag to bypass OpenAI
python3 serve_frontend.py --url "https://example.com" --ai-mock
```

### View Logs for Debugging
```bash
# Check the latest scraped content
ls -lt logs/ | head -5
cat logs/run_*_scraped.json | jq .
```

---

## 🆙 Upgrade pip (Optional)

You have pip 21.2.4, but 25.3 is available:

```bash
python3 -m pip install --upgrade pip
```

---

## 🎓 Next Steps

1. ✅ **You're already set up!** Everything works.

2. **Optional Enhancements** (see IMPLEMENTATION_BLUEPRINT.md):
   - Install Ollama for offline AI
   - Set up Telegram bot
   - Add scheduling system

3. **Your Blockchain**:
   - Make sure it's running on `http://localhost:3000`
   - Test with: `curl http://localhost:3000/health`

---

## 📚 Learn More

- **README.md** - Full project documentation
- **IMPLEMENTATION_BLUEPRINT.md** - Future features (Ollama, Telegram, Scheduler)
- **MANIFESTO.md** - ObjectWire prediction market philosophy
- **logs/** folder - All your scraped data

---

## 🎉 You're Ready to Go!

Try scraping another URL:

```bash
cd /Users/thelegendofzjui/Documents/GitHub/url_scraper_agent.py

python3 serve_frontend.py \
  --url "https://www.objectwire.org/your-article-here" \
  --create-market --enable-blockchain
```

Happy scraping! 🚀
