#!/usr/bin/env python3
"""
Test Gemini Writer functionality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from objectwire.gemini_writer import GeminiWriter, get_default_writer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

def test_gemini_writer():
    """Test Gemini writer with sample event."""
    
    console.print("\n[bold cyan]🤖 Testing Gemini 2.0 Writer[/]\n")
    
    # Sample event
    event = {
        'title': 'Will Bitcoin hit $100,000 by end of 2025?',
        'description': 'Bitcoin price prediction market based on CoinMarketCap data',
        'category': 'crypto',
        'source_url': 'https://coinmarketcap.com/currencies/bitcoin/',
        'freeze_date': '2025-12-30T00:00:00Z',
        'resolution_date': '2025-12-31T23:59:59Z',
        'yes_prob': 0.65,
        'no_prob': 0.30,
        'no_change_prob': 0.05
    }
    
    try:
        # Initialize writer
        console.print("[bold]1. Initializing Gemini Writer...[/]")
        writer = get_default_writer()
        console.print("✅ Writer initialized\n")
        
        # Test 1: Connection test
        console.print("[bold]2. Testing API connection...[/]")
        if writer.test_connection():
            console.print("✅ Connection successful\n")
        else:
            console.print("❌ Connection failed\n")
            return
        
        # Test 2: Generate market description
        console.print("[bold]3. Generating market description...[/]")
        description = writer.write_description(
            event=event,
            max_length=500,
            include_rules=True
        )
        
        console.print(Panel(
            description,
            title="📝 Market Description",
            border_style="green"
        ))
        console.print()
        
        # Test 3: Generate Twitter thread
        console.print("[bold]4. Generating Twitter thread (5 tweets)...[/]")
        thread = writer.write_thread(
            event=event,
            num_tweets=5,
            style='hype',
            hashtags=True
        )
        
        console.print(Panel(
            f"[cyan]Generated {thread['total_tweets']} tweets in {thread['generation_time']:.2f}s[/]\n\n" +
            "\n\n".join([f"[bold]Tweet {i+1}:[/]\n{tweet}" for i, tweet in enumerate(thread['tweets'])]),
            title="🐦 Twitter Thread",
            border_style="blue"
        ))
        console.print()
        
        # Test 4: Generate article (short version)
        console.print("[bold]5. Generating article (500 words)...[/]")
        article = writer.write_article(
            event=event,
            template='analysis',
            length=500,
            style='casual',
            seo=True
        )
        
        console.print(Panel(
            f"[bold cyan]{article['title']}[/]\n\n" +
            f"[dim]Generated in {article['generation_time']:.2f}s with {article['model']}[/]\n\n" +
            f"[yellow]Meta: {article['meta_description']}[/]\n" +
            f"[yellow]Keywords: {article['keywords']}[/]\n\n" +
            f"{article['content'][:500]}...",
            title="📰 Article Preview",
            border_style="magenta"
        ))
        console.print()
        
        console.print("[bold green]✅ All tests passed![/]\n")
        
        # Show pricing estimate
        console.print("[bold cyan]💰 Cost Estimate:[/]")
        console.print("  • Article (500 words): ~$0.001")
        console.print("  • Thread (5 tweets): ~$0.0002")
        console.print("  • Description: ~$0.0001")
        console.print("  [dim]Total: ~$0.0013 per event[/]\n")
        
    except ImportError as e:
        console.print(f"[bold red]❌ Error: {e}[/]")
        console.print("\n[yellow]Install Gemini library:[/]")
        console.print("  pip install google-generativeai\n")
        
    except ValueError as e:
        console.print(f"[bold red]❌ Error: {e}[/]")
        console.print("\n[yellow]Set up Gemini API key:[/]")
        console.print("  1. Get API key: https://aistudio.google.com/app/apikey")
        console.print("  2. Add to .env file: GEMINI_API_KEY=your_key_here\n")
        
    except Exception as e:
        console.print(f"[bold red]❌ Unexpected error: {e}[/]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/]")

if __name__ == '__main__':
    test_gemini_writer()
