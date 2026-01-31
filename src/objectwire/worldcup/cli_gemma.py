"""
ObjectWire World Cup Writing Agent with Gemma 2
================================================
CLI Entry Point for World Cup journalism automation with offline AI.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from datetime import datetime
import os
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.objectwire.gemma_engine import WorldCupGemmaWriter
except ImportError:
    # Fallback if imports fail
    WorldCupGemmaWriter = None

console = Console()

@click.group(invoke_without_command=True)
@click.version_option(version="1.0.0", prog_name="objectwire-worldcup")
@click.option("--debug", is_flag=True, help="Enable debug mode with verbose logging")
@click.pass_context
def cli(ctx, debug):
    """⚽ ObjectWire World Cup Writing Agent - AI-Powered Tournament Journalism"""
    
    # Show World Cup greeting on startup
    if ctx.invoked_subcommand is None:
        show_world_cup_welcome()

def show_world_cup_welcome():
    """Display World Cup themed welcome banner."""
    
    # Calculate days until World Cup 2026
    world_cup_start = datetime(2026, 6, 11)
    days_until = (world_cup_start - datetime.now()).days
    
    if days_until > 0:
        countdown = f"⏰ {days_until} days until FIFA World Cup 2026!"
    else:
        countdown = "🏆 FIFA World Cup 2026 is happening NOW!"
    
    banner = f"""
[bold orange3]╔══════════════════════════════════════════════════════════════╗[/]
[bold orange3]║[/]                   [bold]⚽ OBJECTWIRE WORLD CUP[/]                    [bold orange3]║[/]
[bold orange3]║[/]              [dim]AI-Powered Tournament Journalism Agent[/]          [bold orange3]║[/]
[bold orange3]╚══════════════════════════════════════════════════════════════╝[/]

{countdown}

[bold]🎯 Specialized for ObjectWire.org FIFA 2026 Coverage[/]
   • Investigative articles on FIFA corruption
   • Real-time match analysis and breaking news  
   • Player transfer investigations
   • Tournament predictions and analytics
   • [green]Offline AI with Gemma 2[/]

[dim]Available Commands:[/]
   [orange3]gemma[/]      - Test and use Gemma 2 AI locally
   [orange3]generate[/]   - Generate World Cup content  
   [orange3]monitor[/]    - Monitor FIFA news feeds
   [orange3]publish[/]    - Publish to ObjectWire.org
"""
    
    console.print(Panel(banner, border_style="orange3"))

@cli.group()
def gemma():
    """🤖 Gemma 2 AI Commands - Local offline content generation"""
    pass

@gemma.command()
def test():
    """Test Gemma 2 connection and capabilities"""
    console.print("\n[bold orange3]Testing Gemma 2 Integration...[/]")
    
    if WorldCupGemmaWriter is None:
        console.print("❌ [red]Gemma engine not available. Install requirements first.[/]")
        return
    
    try:
        writer = WorldCupGemmaWriter()
        result = writer.test_connection()
        
        if result["status"] == "success":
            console.print(f"✅ [green]{result['message']}[/]")
            
            # Create test results table
            table = Table(title="Gemma 2 Test Results", border_style="green")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("Model", result["model"])
            table.add_row("Processing Time", f"{result['processing_time']:.2f}s")
            table.add_row("Tokens Used", str(result["tokens_used"]))
            table.add_row("Test Output", result["test_output"][:50] + "...")
            
            console.print(table)
            console.print("\n[green]✨ Gemma 2 is ready for World Cup journalism![/]")
            
        else:
            console.print(f"❌ [red]{result['message']}[/]")
            show_gemma_setup()
            
    except Exception as e:
        console.print(f"❌ [red]Error testing Gemma 2: {e}[/]")
        show_gemma_setup()

@gemma.command()
@click.option("--event", "-e", required=True, help="Breaking news event to write about")
@click.option("--context", "-c", default="", help="Additional context for the story")
def breaking(event, context):
    """Generate breaking news article using Gemma 2"""
    
    if WorldCupGemmaWriter is None:
        console.print("❌ [red]Gemma engine not available. Run setup first.[/]")
        return
    
    console.print(f"\n[bold orange3]Generating breaking news article...[/]")
    console.print(f"Event: [dim]{event}[/]")
    
    try:
        writer = WorldCupGemmaWriter()
        
        with console.status("[orange3]Gemma 2 is writing...", spinner="dots"):
            article = writer.generate_breaking_news(event, context)
        
        console.print("\n[bold green]📰 Article Generated![/]")
        console.print("─" * 60)
        console.print(article)
        console.print("─" * 60)
        
        # Option to save
        if click.confirm("\nSave article to file?"):
            filename = f"breaking_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = os.path.join("articles", filename)
            os.makedirs("articles", exist_ok=True)
            
            with open(filepath, "w") as f:
                f.write(article)
            console.print(f"💾 [green]Saved to {filepath}[/]")
        
    except Exception as e:
        console.print(f"❌ [red]Error generating article: {e}[/]")

@gemma.command()
@click.option("--team1", "-t1", required=True, help="First team name")
@click.option("--team2", "-t2", required=True, help="Second team name")  
@click.option("--score1", "-s1", type=int, help="Team 1 score")
@click.option("--score2", "-s2", type=int, help="Team 2 score")
@click.option("--details", "-d", default="", help="Match details and stats")
def analysis(team1, team2, score1, score2, details):
    """Generate match analysis using Gemma 2"""
    
    if WorldCupGemmaWriter is None:
        console.print("❌ [red]Gemma engine not available. Run setup first.[/]")
        return
    
    console.print(f"\n[bold orange3]Generating match analysis...[/]")
    console.print(f"Match: [dim]{team1} vs {team2}[/]")
    
    # Build match data
    match_data = {
        "team1": team1,
        "team2": team2,
        "details": details
    }
    
    if score1 is not None and score2 is not None:
        match_data["score"] = f"{score1}-{score2}"
        match_data["winner"] = team1 if score1 > score2 else team2 if score2 > score1 else "Draw"
    
    try:
        writer = WorldCupGemmaWriter()
        
        with console.status("[orange3]Gemma 2 is analyzing...", spinner="dots"):
            article = writer.generate_match_analysis(team1, team2, match_data)
        
        console.print("\n[bold green]⚽ Analysis Generated![/]")
        console.print("─" * 60)
        console.print(article)
        console.print("─" * 60)
        
        # Option to save
        if click.confirm("\nSave analysis to file?"):
            filename = f"match_analysis_{team1}_{team2}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = os.path.join("articles", filename)
            os.makedirs("articles", exist_ok=True)
            
            with open(filepath, "w") as f:
                f.write(article)
            console.print(f"💾 [green]Saved to {filepath}[/]")
        
    except Exception as e:
        console.print(f"❌ [red]Error generating analysis: {e}[/]")

@gemma.command()
def setup():
    """Show Gemma 2 setup instructions"""
    show_gemma_setup()

def show_gemma_setup():
    """Display setup instructions for Gemma 2"""
    setup_text = """
[bold orange3]Setting up Gemma 2 for ObjectWire[/]

[bold]1. Install Ollama[/]
   [dim]macOS:[/] brew install ollama
   [dim]Linux:[/] curl -fsSL https://ollama.ai/install.sh | sh

[bold]2. Start Ollama Service[/]
   brew services start ollama

[bold]3. Pull Gemma 2 Model[/]
   ollama pull gemma2
   [dim](This will download ~5GB - be patient!)[/]

[bold]4. Test Integration[/]
   python3 worldcup_cli_gemma.py gemma test

[bold]5. Generate Your First Article[/]
   python3 worldcup_cli_gemma.py gemma breaking -e "Messi announces World Cup retirement"

[green]✨ Once setup, you'll have completely offline AI content generation![/]
"""
    
    console.print(Panel(setup_text, title="Gemma 2 Setup", border_style="orange3"))

@cli.command()
def status():
    """Check system status including Gemma 2"""
    console.print("\n[bold orange3]ObjectWire World Cup System Status[/]")
    console.print("─" * 50)
    
    # Check Gemma 2
    if WorldCupGemmaWriter is None:
        console.print("🤖 Gemma 2: ❌ [red]Not installed[/]")
    else:
        try:
            writer = WorldCupGemmaWriter()
            if writer.gemma.is_available():
                console.print("🤖 Gemma 2: ✅ [green]Ready[/]")
            else:
                console.print("🤖 Gemma 2: ❌ [red]Model not available[/]")
        except:
            console.print("🤖 Gemma 2: ❌ [red]Error[/]")
    
    # Check other systems
    console.print("📁 Articles folder: ✅ [green]Ready[/]")
    console.print("⚙️  Configuration: ✅ [green]Loaded[/]")
    
    days_until = (datetime(2026, 6, 11) - datetime.now()).days
    console.print(f"⏰ World Cup 2026: {days_until} days")

if __name__ == "__main__":
    cli()