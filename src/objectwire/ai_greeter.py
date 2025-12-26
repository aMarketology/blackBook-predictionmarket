"""
ObjectWire AI Greeter
=====================
Dynamic AI-powered greetings using offline NuExtract model.
"""

import subprocess
import json
import random
from datetime import datetime
from typing import Optional
from pathlib import Path


def get_dynamic_greeting() -> str:
    """Generate dynamic AI greeting using offline llama.cpp model.
    
    Returns:
        Greeting message string
    """
    # Check time of day
    hour = datetime.now().hour
    if hour < 12:
        time_of_day = "morning"
    elif hour < 17:
        time_of_day = "afternoon"
    else:
        time_of_day = "evening"
    
    # Day of week
    day_name = datetime.now().strftime("%A")
    
    # Try to use llama.cpp for dynamic greeting
    try:
        # Simple prompt for quick greeting
        prompt = f"""Generate a friendly, professional greeting for a user starting ObjectWire CLI.
Context: It's {time_of_day} on {day_name}. Keep it under 20 words and enthusiastic about prediction markets.
Greeting:"""
        
        # Check if llama-completion is available
        model_path = Path("models/nuextract-smol-1.5-q4_k_m.gguf")
        if not model_path.exists():
            return _fallback_greeting(time_of_day, day_name)
        
        # Run llama-completion with very short timeout
        result = subprocess.run(
            [
                "llama-completion",
                "-m", str(model_path),
                "-p", prompt,
                "-n", "50",  # Max 50 tokens
                "--temp", "0.8",
                "--single-turn"
            ],
            capture_output=True,
            text=True,
            timeout=3  # 3 second timeout
        )
        
        if result.returncode == 0 and result.stdout.strip():
            greeting = result.stdout.strip()
            # Clean up the greeting
            greeting = greeting.replace('"', '').replace('\n', ' ').strip()
            if len(greeting) > 10 and len(greeting) < 150:
                return greeting
        
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    
    # Fallback to template greetings
    return _fallback_greeting(time_of_day, day_name)


def _fallback_greeting(time_of_day: str, day_name: str) -> str:
    """Fallback greeting templates when AI is unavailable.
    
    Args:
        time_of_day: "morning", "afternoon", or "evening"
        day_name: Name of the day (e.g., "Monday")
        
    Returns:
        Greeting message
    """
    greetings = {
        "morning": [
            f"Good morning! ☀️ Ready to discover profitable prediction markets?",
            f"Happy {day_name} morning! Let's find some winning markets today.",
            f"Morning! Your AI prediction market assistant is ready to go.",
            f"Rise and shine! Time to scrape some events and make markets.",
        ],
        "afternoon": [
            f"Good afternoon! 🌤️ Let's analyze some trending events.",
            f"Afternoon! Ready to generate some high-confidence markets?",
            f"Happy {day_name} afternoon! Your AI agent is standing by.",
            f"Afternoon! Let's find opportunities in the prediction market space.",
        ],
        "evening": [
            f"Good evening! 🌙 Time to catch up on today's best market opportunities.",
            f"Evening! Let's review what the AI found in the feeds today.",
            f"Happy {day_name} evening! Ready to deploy some markets?",
            f"Evening! Your offline AI has been watching the feeds all day.",
        ]
    }
    
    return random.choice(greetings.get(time_of_day, greetings["morning"]))


def get_welcome_banner() -> str:
    """Get welcome banner for CLI startup.
    
    Returns:
        ASCII art banner with greeting
    """
    greeting = get_dynamic_greeting()
    
    banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                     🤖 OBJECTWIRE CLI                        ║
║              AI-Powered Prediction Market Assistant          ║
╚══════════════════════════════════════════════════════════════╝

{greeting}

📊 Capabilities:
  • Scrape & analyze events with offline AI
  • Generate articles & threads with Gemini 2.0
  • Monitor RSS feeds in real-time
  • Deploy markets to blockchain

Type 'help' for commands or press Ctrl+C to exit.
"""
    return banner


def get_status_line() -> str:
    """Get system status line for CLI prompt.
    
    Returns:
        Status line with AI model status
    """
    # Check if model is available
    model_path = Path("models/nuextract-smol-1.5-q4_k_m.gguf")
    
    if model_path.exists():
        model_status = "✓ AI Ready"
    else:
        model_status = "⚠ AI Offline"
    
    return f"[{model_status}]"
