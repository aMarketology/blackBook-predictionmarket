#!/usr/bin/env python3
"""
Test Feed Monitor - Real-time RSS monitoring demo
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from objectwire.feed_monitor import FeedMonitor, POPULAR_FEEDS, start_monitoring
from objectwire.database import get_db
from objectwire.core.scraper import get_scraper
from objectwire.llama_engine import LlamaEngine

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout

console = Console()

def test_feed_monitor():
    """Test the feed monitor with real-time updates."""
    
    console.print("\n[bold cyan]🚀 ObjectWire Feed Monitor Test[/]\n")
    
    # Show configured feeds
    console.print("[bold]Configured Feeds:[/]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Feed", style="cyan")
    table.add_column("Platform", style="yellow")
    table.add_column("Category", style="green")
    table.add_column("Check Interval", style="blue")
    
    for feed_id, config in POPULAR_FEEDS.items():
        table.add_row(
            config['name'],
            config['platform'],
            config['category'],
            f"{config['check_interval_minutes']} min"
        )
    
    console.print(table)
    console.print()
    
    # Initialize components
    console.print("[bold]Initializing components...[/]")
    
    try:
        # Database
        console.print("  • Database... ", end="")
        db = get_db("objectwire_test.db")
        console.print("[green]✓[/]")
        
        # Scraper
        console.print("  • Scraper... ", end="")
        scraper = get_scraper()
        console.print("[green]✓[/]")
        
        # AI Engine (NuExtract)
        console.print("  • NuExtract AI... ", end="")
        try:
            ai_engine = LlamaEngine()
            console.print("[green]✓[/]")
        except Exception as e:
            console.print(f"[yellow]⚠ {e}[/]")
            ai_engine = None
        
        console.print()
        
        # Create monitor
        console.print("[bold]Starting feed monitor...[/]")
        
        monitor = FeedMonitor(
            database=db,
            scraper=scraper,
            ai_engine=ai_engine,
            use_ai_filter=True,
            min_ai_confidence=0.75
        )
        
        # Start monitoring in background
        monitor.start()
        
        console.print()
        console.print(Panel(
            "[bold green]Feed monitor is now running in the background![/]\n\n"
            "It will check feeds at these intervals:\n"
            "  • MrBeast YouTube: Every 15 minutes\n"
            "  • Sidemen YouTube: Every 20 minutes\n"
            "  • TechCrunch: Every 30 minutes\n"
            "  • ESPN NFL: Every 30 minutes\n"
            "  • CoinDesk: Every 20 minutes\n\n"
            "[dim]New articles are automatically scraped and analyzed with NuExtract AI.\n"
            "Important events are saved to the database.[/]",
            title="🎉 Monitor Active",
            border_style="green"
        ))
        
        console.print("\n[bold cyan]Monitoring for new entries...[/]")
        console.print("[dim]Press Ctrl+C to stop[/]\n")
        
        # Monitor and display stats
        try:
            while True:
                time.sleep(10)  # Update every 10 seconds
                
                stats = monitor.get_stats()
                
                # Display current stats
                console.print(f"\r[dim]Stats: {stats['total_checks']} checks | "
                            f"{stats['total_entries']} entries | "
                            f"{stats['important_events']} important events | "
                            f"{stats['filtered_entries']} filtered | "
                            f"{stats['errors']} errors[/]", end="")
        
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Stopping monitor...[/]")
            monitor.stop()
            
            # Show final stats
            console.print("\n[bold]Final Statistics:[/]")
            stats = monitor.get_stats()
            
            stats_table = Table(show_header=True, header_style="bold cyan")
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="green")
            
            stats_table.add_row("Total Checks", str(stats['total_checks']))
            stats_table.add_row("Total Entries", str(stats['total_entries']))
            stats_table.add_row("Important Events", str(stats['important_events']))
            stats_table.add_row("Filtered Out", str(stats['filtered_entries']))
            stats_table.add_row("Errors", str(stats['errors']))
            stats_table.add_row("Feeds Monitored", str(stats['feeds_monitored']))
            stats_table.add_row("Unique Entries Seen", str(stats['seen_entries']))
            
            console.print(stats_table)
            
            # Show events in database
            console.print("\n[bold]Events in Database:[/]")
            events = db.list_events(limit=10)
            
            if events:
                events_table = Table(show_header=True, header_style="bold magenta")
                events_table.add_column("Title", style="cyan", max_width=50)
                events_table.add_column("Category", style="yellow")
                events_table.add_column("Confidence", style="green")
                
                for event in events:
                    events_table.add_row(
                        event['title'][:50] + "..." if len(event['title']) > 50 else event['title'],
                        event['category'] or "N/A",
                        f"{event.get('ai_confidence', 0):.2f}" if event.get('ai_confidence') else "N/A"
                    )
                
                console.print(events_table)
            else:
                console.print("[dim]No events found yet. Monitor needs to run longer.[/]")
            
            console.print("\n[green]✅ Test complete![/]\n")
    
    except ImportError as e:
        console.print(f"\n[bold red]❌ Error: {e}[/]")
        console.print("\n[yellow]Install required dependencies:[/]")
        console.print("  pip install feedparser\n")
    
    except Exception as e:
        console.print(f"\n[bold red]❌ Unexpected error: {e}[/]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/]")


def test_single_feed():
    """Test monitoring a single feed (quick test)."""
    
    console.print("\n[bold cyan]🧪 Quick Feed Test (Single Check)[/]\n")
    
    import feedparser
    
    # Test MrBeast feed
    feed_url = POPULAR_FEEDS['mrbeast']['url']
    console.print(f"Checking: {POPULAR_FEEDS['mrbeast']['name']}")
    console.print(f"URL: {feed_url}\n")
    
    feed = feedparser.parse(feed_url)
    
    if feed.bozo:
        console.print(f"[red]❌ Feed parsing error: {feed.bozo_exception}[/]")
        return
    
    console.print(f"[green]✅ Feed parsed successfully![/]")
    console.print(f"Found {len(feed.entries)} entries\n")
    
    # Show recent entries
    console.print("[bold]Recent Videos:[/]")
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Title", style="cyan", max_width=60)
    table.add_column("Published", style="yellow")
    
    for entry in feed.entries[:5]:
        published = entry.get('published', 'Unknown')
        table.add_row(
            entry.get('title', 'Untitled'),
            published
        )
    
    console.print(table)
    console.print(f"\n[green]✅ Single feed test complete![/]\n")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        test_single_feed()
    else:
        test_feed_monitor()
