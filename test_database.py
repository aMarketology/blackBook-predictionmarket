#!/usr/bin/env python3
"""
Test database module functionality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from objectwire.database import Database
from rich.console import Console
from rich.table import Table
import json

console = Console()

def test_database():
    """Test database operations."""
    
    console.print("\n[bold cyan]🗄️  Testing ObjectWire Database[/]\n")
    
    # Initialize database
    db = Database("test_objectwire.db")
    console.print("✅ Database initialized\n")
    
    # Test 1: Save event
    console.print("[bold]Test 1: Save Event[/]")
    event = {
        'market_id': 'test-market-123',
        'title': 'Will Bitcoin hit $100k by end of 2025?',
        'description': 'Bitcoin price prediction market',
        'category': 'crypto',
        'source_url': 'https://example.com/btc-100k',
        'freeze_date': '2025-12-30T00:00:00Z',
        'resolution_date': '2025-12-31T23:59:59Z',
        'yes_prob': 0.65,
        'no_prob': 0.30,
        'no_change_prob': 0.05,
        'status': 'pending',
        'ai_confidence': 0.85
    }
    
    event_id = db.save_event(event)
    console.print(f"✅ Saved event with ID: {event_id}\n")
    
    # Test 2: Get event
    console.print("[bold]Test 2: Get Event[/]")
    retrieved = db.get_event('test-market-123')
    console.print(f"✅ Retrieved event: {retrieved['title']}\n")
    
    # Test 3: List events
    console.print("[bold]Test 3: List Events[/]")
    events = db.list_events(status='pending', limit=10)
    console.print(f"✅ Found {len(events)} pending events\n")
    
    # Test 4: Log scrape
    console.print("[bold]Test 4: Log Scrape[/]")
    scrape_id = db.log_scrape(
        url='https://example.com/test',
        success=True,
        event_id=event_id,
        processing_time_ms=1250
    )
    console.print(f"✅ Logged scrape with ID: {scrape_id}\n")
    
    # Test 5: Add creator
    console.print("[bold]Test 5: Add Creator[/]")
    creator_id = db.add_creator(
        name='MrBeast',
        platform='youtube',
        platform_id='UCX6OQ3DkcsbYNE6H8uQQuVA',
        followers=250000000,
        metadata={'avg_views': 100000000, 'niche': 'entertainment'}
    )
    console.print(f"✅ Added creator with ID: {creator_id}\n")
    
    # Test 6: Add RSS feed
    console.print("[bold]Test 6: Add RSS Feed[/]")
    feed_id = db.add_feed(
        url='https://techcrunch.com/feed/',
        title='TechCrunch',
        category='tech'
    )
    console.print(f"✅ Added feed with ID: {feed_id}\n")
    
    # Test 7: Get statistics
    console.print("[bold]Test 7: Database Statistics[/]")
    stats = db.get_stats()
    
    table = Table(title="Database Stats", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Events", str(stats['events']['total']))
    table.add_row("Pending Events", str(stats['events']['by_status'].get('pending', 0)))
    table.add_row("Total Scrapes", str(stats['scrapes']['total']))
    table.add_row("Success Rate", f"{stats['scrapes']['success_rate']}%")
    table.add_row("Total Creators", str(stats['creators']))
    table.add_row("Active RSS Feeds", str(stats['feeds']))
    
    console.print(table)
    console.print()
    
    # Test 8: Update event status
    console.print("[bold]Test 8: Update Event Status[/]")
    success = db.update_event_status(
        market_id='test-market-123',
        status='posted',
        blockchain_tx_id='0x123abc456def'
    )
    console.print(f"✅ Updated event status: {success}\n")
    
    # Test 9: Export events
    console.print("[bold]Test 9: Export Events[/]")
    db.export_events('test_export.json', status='posted')
    console.print("✅ Exported events to test_export.json\n")
    
    # Test 10: List creators
    console.print("[bold]Test 10: List Creators[/]")
    creators = db.list_creators()
    
    creator_table = Table(title="Tracked Creators", show_header=True)
    creator_table.add_column("Name", style="cyan")
    creator_table.add_column("Platform", style="yellow")
    creator_table.add_column("Followers", style="green")
    
    for creator in creators:
        creator_table.add_row(
            creator['name'],
            creator['platform'],
            f"{creator['followers']:,}" if creator['followers'] else "N/A"
        )
    
    console.print(creator_table)
    console.print()
    
    console.print("[bold green]✅ All tests passed![/]\n")
    console.print(f"[dim]Test database created at: test_objectwire.db[/]")
    console.print(f"[dim]Test export created at: test_export.json[/]")

if __name__ == '__main__':
    test_database()
