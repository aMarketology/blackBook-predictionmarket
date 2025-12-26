#!/usr/bin/env python3
"""
Test script for AI Greeter
===========================
Demonstrates the dynamic greeting system.
"""

from src.objectwire.ai_greeter import (
    get_dynamic_greeting,
    get_welcome_banner,
    get_status_line,
    _fallback_greeting
)
from datetime import datetime
from rich.console import Console

console = Console()


def test_greetings():
    """Test greeting generation."""
    console.print("\n[bold cyan]🤖 Testing AI Greeter System[/]\n")
    
    # Test 1: Dynamic greeting
    console.print("[yellow]Test 1: Dynamic Greeting[/]")
    greeting = get_dynamic_greeting()
    console.print(f"Generated: {greeting}\n")
    
    # Test 2: Welcome banner
    console.print("[yellow]Test 2: Welcome Banner[/]")
    banner = get_welcome_banner()
    console.print(banner)
    
    # Test 3: Status line
    console.print("\n[yellow]Test 3: Status Line[/]")
    status = get_status_line()
    console.print(f"Status: {status}\n")
    
    # Test 4: Time-based greetings
    console.print("[yellow]Test 4: Time-Based Fallback Greetings[/]")
    hour = datetime.now().hour
    day = datetime.now().strftime("%A")
    
    if hour < 12:
        time_period = "morning"
    elif hour < 17:
        time_period = "afternoon"
    else:
        time_period = "evening"
    
    console.print(f"Current time: {time_period}")
    console.print(f"Day: {day}")
    
    # Generate 3 different fallback greetings
    console.print("\n[dim]Sample fallback greetings:[/]")
    for i in range(3):
        fallback = _fallback_greeting(time_period, day)
        console.print(f"  {i+1}. {fallback}")
    
    console.print("\n[bold green]✓ All tests completed![/]\n")


if __name__ == "__main__":
    test_greetings()
