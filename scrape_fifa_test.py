#!/usr/bin/env python3
"""
Scrape FIFA Women's Champions Cup article
"""

import sys
sys.path.insert(0, 'src')

from objectwire.cli import scrape_url, console, analyze
from rich.panel import Panel
import json

url = 'https://www.fifa.com/en/tournaments/womens/womens-champions-cup/2026/articles/record-breaking-prize-money'

console.print('[bold cyan]🔍 Scraping FIFA Women\'s Champions Cup Article...[/]')
console.print(f'[white]URL:[/] {url}')
console.print()

try:
    with console.status('[green]Scraping...', spinner='dots'):
        scraped = scrape_url(url)
    
    if scraped:
        console.print('[green]✅ Successfully scraped![/]')
        console.print()
        
        # Display scraped content
        console.print(Panel(
            f"[white]Title:[/] {scraped.get('title', 'N/A')}\n"
            f"[white]URL:[/] {scraped.get('url', url)}\n"
            f"[white]Content Length:[/] {len(str(scraped.get('text', scraped.get('content', ''))))} characters",
            title='[bold cyan]Scraped Metadata[/]',
            border_style='cyan'
        ))
        
        # Show content preview
        content = scraped.get('text') or scraped.get('content', '')
        if content:
            preview = content[:500] + '...' if len(content) > 500 else content
            console.print()
            console.print('[bold white]Content Preview:[/]')
            console.print('[dim]' + preview + '[/]')
        
        # Try to analyze for prediction market
        console.print()
        console.print('[cyan]📊 Analyzing for prediction market...[/]')
        try:
            event = analyze(scraped)
            console.print(Panel(
                f"[white]Market Title:[/] {event.title}\n"
                f"[white]Description:[/] {event.description[:200]}...\n"
                f"[white]Outcomes:[/] {', '.join(event.outcomes)}",
                title='[bold green]Prediction Market[/]',
                border_style='green'
            ))
        except Exception as e:
            console.print(f'[yellow]⚠ Could not analyze: {e}[/]')
        
        # Save to file for inspection
        with open('scraped_fifa_article.json', 'w') as f:
            json.dump(scraped, f, indent=2)
        
        console.print()
        console.print('[green]💾 Full content saved to: scraped_fifa_article.json[/]')
        
        # Ask if user wants to generate article
        console.print()
        console.print('[bold yellow]Ready to generate article with Gemma 2?[/]')
        console.print('[dim]Run: python3 test_phase2b_article.py[/]')
        
    else:
        console.print('[red]❌ Failed to scrape article[/]')
        
except Exception as e:
    console.print(f'[red]❌ Error: {e}[/]')
    import traceback
    traceback.print_exc()
