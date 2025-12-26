# AI Greeter System 🤖

## Overview
The AI Greeter provides dynamic, contextual greetings when users start the ObjectWire CLI. It creates a personalized experience using the offline NuExtract model or falls back to template-based greetings.

## Features

### Dynamic Greetings
- **Time-aware**: Different greetings for morning, afternoon, and evening
- **Day-aware**: Incorporates the current day of week
- **AI-powered**: Uses llama.cpp with NuExtract model when available
- **Fast fallback**: Template-based greetings when AI is unavailable (3s timeout)

### Welcome Banner
Full ASCII art banner displayed on CLI startup:
```
╔══════════════════════════════════════════════════════════════╗
║                     🤖 OBJECTWIRE CLI                        ║
║              AI-Powered Prediction Market Assistant          ║
╚══════════════════════════════════════════════════════════════╝

Good morning! ☀️ Ready to discover profitable prediction markets?

📊 Capabilities:
  • Scrape & analyze events with offline AI
  • Generate articles & threads with Gemini 2.0
  • Monitor RSS feeds in real-time
  • Deploy markets to blockchain

Type 'help' for commands or press Ctrl+C to exit.
```

### Status Line
Shows AI model availability: `[✓ AI Ready]` or `[⚠ AI Offline]`

## Implementation

### File Structure
```
src/objectwire/
  ├── ai_greeter.py          # Greeting generation logic
  └── cli.py                 # Integration point (main function)
```

### Key Functions

#### `get_dynamic_greeting() -> str`
Generates dynamic greeting using AI or templates.
- Tries llama.cpp with 3s timeout
- Falls back to templates if unavailable
- Returns greeting string (under 150 chars)

#### `get_welcome_banner() -> str`
Returns full ASCII banner with greeting and capabilities.
- Used in interactive mode only
- Shows when CLI starts without subcommand

#### `get_status_line() -> str`
Returns system status indicator.
- `[✓ AI Ready]` if model exists
- `[⚠ AI Offline]` if model missing

#### `_fallback_greeting(time_of_day: str, day_name: str) -> str`
Template-based greeting fallback.
- 4 templates per time period (morning/afternoon/evening)
- Randomized selection for variety
- Always available (no dependencies)

## How It Works

### Startup Flow
1. User runs `objectwire` (no subcommand)
2. CLI main function checks if subcommand is None
3. Imports `get_welcome_banner()` from `ai_greeter`
4. Displays banner with greeting
5. Enters interactive mode

### AI Greeting Generation
```python
# Simple prompt for quick greeting
prompt = f"""Generate a friendly, professional greeting for a user starting ObjectWire CLI.
Context: It's {time_of_day} on {day_name}. Keep it under 20 words and enthusiastic about prediction markets.
Greeting:"""

# Run llama-completion
subprocess.run([
    "llama-completion",
    "-m", "models/nuextract-smol-1.5-q4_k_m.gguf",
    "-p", prompt,
    "-n", "50",  # Max 50 tokens
    "--temp", "0.8",
    "--single-turn"
], timeout=3)
```

### Template Fallback
If AI times out or model is unavailable:
```python
greetings = {
    "morning": [
        "Good morning! ☀️ Ready to discover profitable prediction markets?",
        "Happy {day_name} morning! Let's find some winning markets today.",
        # ... more templates
    ],
    "afternoon": [...],
    "evening": [...]
}
```

## Configuration

### Model Path
Default: `models/nuextract-smol-1.5-q4_k_m.gguf`

To use a different model:
1. Edit `ai_greeter.py`
2. Change `model_path` variable
3. Ensure model is compatible with llama.cpp

### Timeout
Default: 3 seconds

To adjust:
```python
timeout=3  # Change to desired seconds
```

### Token Limit
Default: 50 tokens (~20 words)

To adjust:
```python
"-n", "50",  # Change to desired token count
```

## Testing

Run the test script:
```bash
python3 test_ai_greeter.py
```

Output shows:
- Dynamic greeting generation
- Welcome banner
- Status line
- Sample fallback greetings

## Usage Examples

### Interactive Mode (Shows Greeting)
```bash
objectwire
```
Output:
```
╔══════════════════════════════════════════════════════════════╗
║                     🤖 OBJECTWIRE CLI                        ║
║              AI-Powered Prediction Market Assistant          ║
╚══════════════════════════════════════════════════════════════╝

Good afternoon! 🌤️ Let's analyze some trending events.
...
```

### With Subcommand (No Greeting)
```bash
objectwire scrape https://example.com
objectwire --help
objectwire rss add https://feed.example.com
```
No banner is shown when subcommand is provided.

### Debug Mode
```bash
objectwire --debug
```
Shows greeting plus debug status:
```
🔍 Debug mode enabled
[Welcome banner]
```

## Performance

### AI Greeting
- **Time**: ~1-3 seconds (with timeout)
- **Tokens**: 50 max (~20 words)
- **CPU**: Uses Metal GPU acceleration on Mac
- **Fallback**: Instant if timeout or unavailable

### Template Greeting
- **Time**: <1ms (instant)
- **Memory**: Minimal (templates in memory)
- **No dependencies**: Always works

## Benefits

### User Experience
✅ Personalized interaction
✅ Shows AI capabilities immediately
✅ Time-aware professionalism
✅ Reduces cognitive load (clear capabilities list)

### Technical
✅ No external API calls (offline)
✅ Fast fallback (never blocks startup)
✅ Model-agnostic (works with any llama.cpp model)
✅ Zero dependencies beyond existing stack

### Business
✅ Demonstrates AI features upfront
✅ Professional first impression
✅ Builds user confidence
✅ Encourages exploration

## Future Enhancements

### Planned
- [ ] User name personalization (store in config)
- [ ] RSS feed status in greeting ("3 new articles found!")
- [ ] Market stats in greeting ("You have 5 active markets")
- [ ] Greeting history tracking
- [ ] Custom greeting templates in config file

### Possible
- [ ] Multi-language greetings
- [ ] Weather integration (if user location known)
- [ ] Market trend summary in greeting
- [ ] Achievement badges ("🎉 10 markets deployed!")

## Troubleshooting

### Issue: "⚠ AI Offline" Status
**Cause**: Model file not found at `models/nuextract-smol-1.5-q4_k_m.gguf`

**Solution**:
1. Check if model exists: `ls models/`
2. Download model if missing (see INSTALL_GUIDE.md)
3. Verify path in `ai_greeter.py`

### Issue: Greeting Takes Too Long
**Cause**: llama.cpp processing time exceeds timeout

**Solution**:
1. Reduce token limit: `"-n", "30"`
2. Increase timeout: `timeout=5`
3. Use smaller model (faster inference)

### Issue: Same Greeting Every Time
**Cause**: AI model not generating, using fallback

**Solution**:
1. Check model availability
2. Test llama-completion manually
3. Check temperature setting (increase for more variety)

### Issue: Greeting Not Showing
**Cause**: Subcommand provided (e.g., `objectwire scrape`)

**Solution**: This is expected behavior. Greeting only shows in interactive mode without subcommand.

## Code References

### Integration Point (cli.py)
```python
@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx, dev: bool, debug: bool):
    # Show AI-powered greeting on startup
    if ctx.invoked_subcommand is None:
        from objectwire.ai_greeter import get_welcome_banner
        console.print(get_welcome_banner())
    
    if dev:
        run_dev_mode()
    elif ctx.invoked_subcommand is None:
        interactive_mode()
```

### Model Check
```python
model_path = Path("models/nuextract-smol-1.5-q4_k_m.gguf")
if model_path.exists():
    # Use AI greeting
else:
    # Use template fallback
```

## Contributing

To add new greeting templates:
1. Edit `_fallback_greeting()` in `ai_greeter.py`
2. Add templates to respective time period
3. Keep under 100 characters
4. Include emoji for visual appeal
5. Maintain professional tone

Example:
```python
"morning": [
    "Good morning! ☀️ Ready to discover profitable prediction markets?",
    "Your new template here! 🚀 Keep it enthusiastic!",
]
```
