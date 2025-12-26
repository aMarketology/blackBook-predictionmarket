#!/usr/bin/env python3
"""
Test RSS Monitor - Background feed monitoring
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from objectwire.rss_monitor import RSSMonitor, get_monitor
from rich.console import Console

console = Console()

def custom_alert(article, feed):
    """Custom alert handler for interesting articles."""
    console.print(f"\n[bold yellow]🔥 HOT ARTICLE DETECTED![/bold yellow]")
    console.print(f"[cyan]Feed:[/cyan] {feed['name']} ({feed['priority']} priority)")
    console.print(f"[cyan]Title:[/cyan] {article['title']}")
    console.print(f"[cyan]URL:[/cyan] {article['url']}")
    console.print(f"[dim]Published:[/dim] {article['published']}")
    console.print(f"\n[yellow]→ Review this article to create a prediction market![/yellow]\n")

def test_rss_monitor():
    """Test RSS monitor functionality."""
    
    console.print("\n[bold cyan]🔍 ObjectWire RSS Monitor Test[/]\n")
    
    # Create monitor with custom alert
    monitor = RSSMonitor(on_interesting_article=custom_alert)
    
    console.print("[yellow]Starting RSS monitor...[/yellow]")
    console.print("[dim]This will run in the background and alert you when interesting articles are found.[/dim]\n")
    
    # Start monitoring
    monitor.start()
    
    try:
        console.print("[green]✓ Monitor is running![/green]")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")
        
        # Keep running and show stats every 30 seconds
        while True:
            time.sleep(30)
            console.print("\n[cyan]--- Stats Update ---[/cyan]")
            monitor.print_stats()
            console.print()
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping monitor...[/yellow]")
        monitor.stop()
        console.print("\n[cyan]Final Statistics:[/cyan]")
        monitor.print_stats()
        console.print("\n[green]✓ Monitor stopped gracefully[/green]\n")

if __name__ == '__main__':
    test_rss_monitor()
