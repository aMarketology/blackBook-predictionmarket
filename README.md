# 🤖 BlackBook URL Scraping AI Agent

An intelligent AI agent that scrapes URLs, extracts event data, and automatically creates prediction markets on your BlackBook blockchain.

## 🎯 What It Does

1. **Scrapes URLs** - Extracts content from any website
2. **AI Analysis** - Uses OpenAI to identify prediction-worthy events
3. **Market Creation** - Automatically creates markets on your blockchain
4. **REST API** - Provides endpoints for integration

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- BlackBook blockchain running on port 3000

### Installation

1. **Clone and navigate to directory**
```bash
cd "c:\Users\Allied Gaming\Documents\GitHub\templates\ai agent"
```

2. **Set up environment**
```bash
# Copy environment template
copy .env.example .env

# Edit .env and add your OpenAI API key
notepad .env
```

3. **Run the agent**
```bash
# Windows
start_agent.bat

# Linux/Mac
chmod +x start_agent.sh
./start_agent.sh
```

The agent will be available at: **http://localhost:8082**

## 📚 API Endpoints

### POST /scrape
Scrape a URL and create a prediction market

**Request:**
```json
{
  "url": "https://techcrunch.com/2024/01/15/openai-announces-gpt5",
  "category": "tech",
  "auto_create_market": true
}
```

**Response:**
```json
{
  "success": true,
  "market_id": "market_123",
  "event_data": {
    "title": "Will GPT-5 be released before June 2025?",
    "description": "OpenAI announced GPT-5 development...",
    "category": "tech",
    "options": ["Yes, before June 2025", "No, after June 2025", "Cancelled/Delayed"],
    "confidence": 0.85,
    "source_url": "https://techcrunch.com/..."
  },
  "message": "Market created successfully"
}
```

### POST /analyze
Analyze a URL without creating a market

**Request:**
```json
{
  "url": "https://example.com/article",
  "category": "crypto"
}
```

### GET /markets
List all active prediction markets

### GET /health
Check agent health status

## 💡 Usage Examples

### Using cURL

```bash
# Scrape and create market
curl -X POST http://localhost:8082/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://techcrunch.com/article"}'

# Analyze without creating market
curl -X POST http://localhost:8082/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article", "auto_create_market": false}'

# Get all markets
curl http://localhost:8082/markets
```

### Using Python

```python
import requests

# Scrape URL and create market
response = requests.post('http://localhost:8082/scrape', json={
    'url': 'https://techcrunch.com/article',
    'category': 'tech',
    'auto_create_market': True
})

result = response.json()
print(f"Market created: {result['market_id']}")
```

### Using JavaScript

```javascript
// Scrape URL and create market
fetch('http://localhost:8082/scrape', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    url: 'https://techcrunch.com/article',
    category: 'tech',
    auto_create_market: true
  })
})
.then(res => res.json())
.then(data => console.log('Market created:', data.market_id));
```

## 🔧 Configuration

Edit `.env` file:

```bash
# Required: OpenAI API Key
OPENAI_API_KEY=sk-your-key-here

# Optional: Blockchain API URL (default: http://localhost:3000)
BLOCKCHAIN_API_URL=http://localhost:3000

# Optional: Agent port (default: 8082)
AGENT_PORT=8082
```

## 🏗️ Architecture

```
┌─────────────────┐
│   Web Browser   │
│   or API Call   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  URL Scraping AI Agent      │
│  (serve_frontend.py)        │
│                             │
│  ┌────────────────────┐    │
│  │  URLScraper        │    │
│  │  - BeautifulSoup   │    │
│  │  - Extract content │    │
│  └──────┬─────────────┘    │
│         │                   │
│         ▼                   │
│  ┌────────────────────┐    │
│  │  EventAnalyzer     │    │
│  │  - OpenAI GPT-4    │    │
│  │  - Extract events  │    │
│  └──────┬─────────────┘    │
│         │                   │
│         ▼                   │
│  ┌────────────────────┐    │
│  │ BlockchainConnector│    │
│  │ - Create markets   │    │
│  └──────┬─────────────┘    │
└─────────┼───────────────────┘
          │
          ▼
┌─────────────────────────────┐
│  BlackBook Blockchain       │
│  (Rust - port 3000)         │
│  - Prediction markets       │
│  - Escrow & settlements     │
└─────────────────────────────┘
```

## 🎭 Features

### Intelligent Content Extraction
- Removes ads, navigation, and clutter
- Extracts main article content
- Captures metadata (author, date, images)

### AI-Powered Event Detection
- Identifies prediction-worthy events
- Creates clear, time-bound questions
- Generates multiple outcome options
- Assigns confidence scores

### Blockchain Integration
- Direct API integration
- Automatic market creation
- Real-time status updates

### Fallback Mode
- Works without OpenAI (basic mode)
- Graceful degradation
- Manual event creation option

## 📊 Categories

The agent supports these categories:
- `tech` - Technology and software
- `crypto` - Cryptocurrency and blockchain
- `business` - Business and finance
- `politics` - Political events
- `sports` - Sports outcomes
- `general` - General events

## 🛠️ Development

### Project Structure

```
ai agent/
├── serve_frontend.py       # Main agent code
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── start_agent.bat        # Windows startup script
├── start_agent.sh         # Linux/Mac startup script
├── README_AGENT.md        # This file
└── src/                   # Rust blockchain (separate)
```

### Running in Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn serve_frontend:app --reload --port 8082
```

### API Documentation

Interactive API docs available at:
- Swagger UI: http://localhost:8082/docs
- ReDoc: http://localhost:8082/redoc

## 🔍 Troubleshooting

### OpenAI API Not Working
- Check your API key in `.env`
- Verify you have credits: https://platform.openai.com/usage
- Agent will work in fallback mode without OpenAI

### Blockchain Connection Failed
- Make sure Rust backend is running: `cargo run`
- Check it's on port 3000: http://localhost:3000
- Verify BLOCKCHAIN_API_URL in `.env`

### URL Scraping Failed
- Some sites block scrapers (use different URLs)
- Check internet connection
- Try simpler websites first

### Port Already in Use
- Change AGENT_PORT in `.env`
- Or kill the process using port 8082

## 🚦 Status Indicators

- ✅ **Enabled** - Feature is working
- ❌ **Disabled** - Feature not configured
- ⚠️ **Warning** - Issue detected
- 🔍 **Scraping** - Extracting content
- 🤖 **Analyzing** - AI processing
- 🔗 **Creating** - Building market

## 📝 Example Workflow

1. **Find interesting article**
   ```
   https://techcrunch.com/2024/01/15/startup-x-raises-100m
   ```

2. **Send to agent**
   ```bash
   curl -X POST http://localhost:8082/scrape \
     -H "Content-Type: application/json" \
     -d '{"url": "https://techcrunch.com/..."}'
   ```

3. **Agent processes**
   - Scrapes article content
   - AI extracts prediction event
   - Creates market on blockchain

4. **Market is live**
   - Users can place bets
   - Track on your frontend
   - Resolve when outcome known

## 🎯 Best Practices

1. **Use quality sources** - News sites work best
2. **Clear events** - Look for time-bound claims
3. **Verify markets** - Review before going live
4. **Monitor usage** - Watch OpenAI costs
5. **Rate limiting** - Don't spam requests

## 📜 License

Part of the BlackBook Prediction Market platform.

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Check blockchain backend logs

---

**Ready to scrape the web and create prediction markets!** 🚀
