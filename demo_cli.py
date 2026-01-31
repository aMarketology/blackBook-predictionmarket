#!/usr/bin/env python3
"""
Demo: ObjectWire CLI with AI Greeter
=====================================
Shows the new dynamic greeting system in action.
"""

from src.objectwire.ai_greeter import get_welcome_banner
from rich.console import Console
import sys

console = Console()

def demo_greeting():
    """Demonstrate the AI greeting system."""
    console.print("\n[bold cyan]🎉 ObjectWire CLI - Latest Version Installed![/]\n")
    
    console.print("[yellow]Now you can run ObjectWire with:[/]")
    console.print("  • [bold green]objectwire[/] - Start interactive mode with AI greeting")
    console.print("  • [bold green]objectwire scrape <url>[/] - Scrape a URL")
    console.print("  • [bold green]objectwire rss <feed>[/] - Parse RSS feed")
    console.print("  • [bold green]objectwire --help[/] - Show all commands\n")
    
    console.print("[bold cyan]Preview: Here's the AI greeting you'll see:[/]\n")
    console.print(get_welcome_banner())
    
    console.print("\n[dim]💡 Tip: The greeting changes based on time of day![/]")
    console.print("[dim]   Try running 'objectwire' in morning, afternoon, and evening.[/]\n")

if __name__ == "__main__":
    demo_greeting()
