#!/usr/bin/env python3
"""
Test scraping ObjectWire article and generating new content with Gemma 2
"""

import sys
sys.path.insert(0, 'src')

from objectwire.cli import scrape_url, console, analyze, generate_article_with_gemma, save_generated_article
from rich.panel import Panel
import json

def main():
    url = 'https://www.objectwire.org/minnesota-feeding-our-future-fraud'
    
    console.print('[bold cyan]🔍 Scraping ObjectWire Article...[/]')
    console.print(f'[white]URL:[/] {url}')
    console.print()
    
    try:
        # Step 1: Scrape the article
        with console.status('[green]Scraping...', spinner='dots'):
            scraped = scrape_url(url)
        
        if not scraped:
            console.print('[red]❌ Failed to scrape article[/]')
            return False
        
        console.print('[green]✅ Successfully scraped![/]')
        console.print()
        
        # Display scraped content
        title = scraped.get('title', 'N/A')
        content = scraped.get('text') or scraped.get('content', '')
        
        console.print(Panel(
            f"[white]Title:[/] {title}\n"
            f"[white]URL:[/] {scraped.get('url', url)}\n"
            f"[white]Content Length:[/] {len(str(content))} characters\n"
            f"[white]Word Count:[/] {len(content.split())} words",
            title='[bold cyan]Scraped Metadata[/]',
            border_style='cyan'
        ))
        
        # Show content preview
        if content:
            preview = content[:600] + '...' if len(content) > 600 else content
            console.print()
            console.print('[bold white]Content Preview:[/]')
            console.print('[dim]' + preview + '[/]')
        
        # Save scraped data
        with open('scraped_objectwire_article.json', 'w') as f:
            json.dump(scraped, f, indent=2)
        
        console.print()
        console.print('[green]💾 Scraped content saved to: scraped_objectwire_article.json[/]')
        
        # Step 2: Analyze for prediction market
        console.print()
        console.print('[cyan]� Analyzing for prediction market...[/]')
        
        try:
            event = analyze(scraped)
            payload = {
                "market_id": "feeding_our_future_fraud",
                "title": event.title,
                "description": event.description,
                "outcomes": event.outcomes,
                "category": "politics",
                "tags": ["fraud", "minnesota", "feeding-our-future"]
            }
            
            console.print(Panel(
                f"[white]Market Title:[/] {event.title}\n"
                f"[white]Description:[/] {event.description[:150]}...\n"
                f"[white]Outcomes:[/] {', '.join(event.outcomes)}",
                title='[bold green]Prediction Market Created[/]',
                border_style='green'
            ))
        except Exception as e:
            console.print(f'[yellow]⚠ Could not analyze: {e}[/]')
            
            # Create mock event
            class MockEvent:
                def __init__(self, scraped_title, scraped_url):
                    self.title = scraped_title
                    self.source_url = scraped_url
                    self.description = "Minnesota Feeding Our Future fraud case"
                    self.outcomes = ["Yes", "No"]
            
            event = MockEvent(title, url)
            payload = {
                "market_id": "feeding_our_future_fraud",
                "title": event.title,
                "description": event.description,
                "outcomes": event.outcomes
            }
        
        # Step 3: Ask user if they want to generate article
        console.print()
        console.print('[bold yellow]📝 Generate new article with Gemma 2?[/]')
        console.print('[dim]This will create a fresh 500-word article based on the scraped content[/]')
        
        response = input('\nGenerate article? [y/N]: ').strip().lower()
        
        if response == 'y':
            console.print()
            console.print('[cyan]✍️  Generating article with Gemma 2...[/]')
            console.print('[dim]This may take 10-30 seconds...[/]')
            
            with console.status('[orange3]Gemma 2 is writing...', spinner='dots'):
                article = generate_article_with_gemma(scraped, payload)
            
            if article:
                word_count = len(article.split())
                console.print()
                console.print('[bold green]📰 Article Generated Successfully![/]')
                console.print('=' * 70)
                console.print(article)
                console.print('=' * 70)
                console.print(f'[bold]Word Count:[/] {word_count} words')
                
                # Step 4: Save article
                console.print()
                save_response = input('Save article? [y/N]: ').strip().lower()
                
                if save_response == 'y':
                    try:
                        filepath = save_generated_article(article, event, payload)
                        console.print(f'[green]✅ Article saved to:[/] {filepath}')
                    except Exception as e:
                        console.print(f'[yellow]⚠ Could not save: {e}[/]')
                
                console.print()
                console.print('[bold green]✅ Test Complete![/]')
                return True
            else:
                console.print('[red]❌ Article generation failed[/]')
                return False
        else:
            console.print('[yellow]Skipped article generation[/]')
            return True
        
    except Exception as e:
        console.print(f'[red]❌ Error: {e}[/]')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        console.print('\n[yellow]Test interrupted by user[/]')
        sys.exit(1)

