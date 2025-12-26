# Quick Start: Using the AI Greeter

## See the Greeting in Action

### Run CLI in Interactive Mode
```bash
cd /Users/thelegendofzjui/Documents/GitHub/url_scraper_agent.py
python3 -m src.objectwire
```

**Expected Output**:
```
╔══════════════════════════════════════════════════════════════╗
║                     🤖 OBJECTWIRE CLI                        ║
║              AI-Powered Prediction Market Assistant          ║
╚══════════════════════════════════════════════════════════════╝

Good [morning/afternoon/evening]! [Dynamic greeting]

📊 Capabilities:
  • Scrape & analyze events with offline AI
  • Generate articles & threads with Gemini 2.0
  • Monitor RSS feeds in real-time
  • Deploy markets to blockchain

Type 'help' for commands or press Ctrl+C to exit.
```

## Test the Greeter

### Run Test Script
```bash
python3 test_ai_greeter.py
```

**Shows**:
- Dynamic greeting generation
- Welcome banner
- Status line (AI Ready / AI Offline)
- Sample fallback greetings

## When Greeting Appears

✅ **Shows greeting**:
- `objectwire` (no subcommand)
- `objectwire --debug`
- `objectwire --dev`

❌ **No greeting**:
- `objectwire scrape https://...`
- `objectwire rss add ...`
- `objectwire --help`
- Any command with subcommand

## Customize Greetings

### Edit Templates
**File**: `src/objectwire/ai_greeter.py`

**Find**: `_fallback_greeting()` function

**Add your templates**:
```python
"morning": [
    "Your custom morning greeting! ☀️",
    # ... more templates
]
```

### Change Model
**Line 37**: `model_path = Path("models/your-model.gguf")`

### Adjust Timeout
**Line 51**: `timeout=3  # Change to your preferred seconds`

### Change Token Limit
**Line 47**: `"-n", "50",  # Change token count`

## Files Overview

```
src/objectwire/
  ├── ai_greeter.py          # 🎯 Main greeting logic
  └── cli.py                 # Integration point

test_ai_greeter.py           # 🧪 Test script
AI_GREETER_GUIDE.md          # 📚 Full documentation
GREETER_IMPLEMENTATION.md    # 📋 Implementation summary
```

## Next Steps

1. **Try it**: Run `python3 -m src.objectwire`
2. **Test it**: Run `python3 test_ai_greeter.py`
3. **Customize it**: Edit greeting templates
4. **Enhance it**: Add RSS monitor status to greeting

## Need Help?

- **Full docs**: See `AI_GREETER_GUIDE.md`
- **Implementation details**: See `GREETER_IMPLEMENTATION.md`
- **System status**: See `START_HERE.md`
