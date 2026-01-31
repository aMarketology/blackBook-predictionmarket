#!/usr/bin/env python3
"""
World Cup 2026 Writing Agent - Demo
===================================
Demonstrates the ObjectWire World Cup journalism automation system.
"""

from worldcup_cli import cli, show_world_cup_welcome, show_status
from worldcup_config import load_config, get_tournament_phase, validate_environment
from worldcup_content_engine import WorldCupContentGenerator
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import asyncio

console = Console()

def demo_world_cup_system():
    """Demonstrate the World Cup writing agent system."""
    
    console.print("\n[bold cyan]🏆 ObjectWire World Cup 2026 Writing Agent Demo[/]\n")
    
    # Show welcome banner
    show_world_cup_welcome()
    
    # Load and show configuration
    demo_configuration()
    
    # Show content generation capabilities
    demo_content_generation()
    
    # Show monitoring capabilities  
    demo_monitoring_system()
    
    # Show integration status
    demo_objectwire_integration()
    
    console.print("\n[bold green]✅ Demo completed! Ready to revolutionize World Cup journalism![/]\n")

def demo_configuration():
    """Demo configuration and tournament data."""
    
    console.print("[bold yellow]📋 Configuration & Tournament Data[/]\n")
    
    config = load_config()
    phase = get_tournament_phase()
    validation = validate_environment()
    
    # Configuration table
    config_table = Table(title="World Cup 2026 Configuration")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")
    
    config_table.add_row("Tournament Start", config.tournament_start.strftime("%B %d, %Y"))
    config_table.add_row("Tournament End", config.tournament_end.strftime("%B %d, %Y"))
    config_table.add_row("Host Countries", ", ".join(config.host_countries))
    config_table.add_row("Current Phase", phase.replace("_", " ").title())
    config_table.add_row("Auto Publish", "✅ Enabled" if config.auto_publish else "❌ Disabled")
    config_table.add_row("Editorial Review", "✅ Required" if config.editorial_review_required else "❌ Optional")
    
    console.print(config_table)
    
    # Environment validation
    console.print("\n[bold cyan]🔧 Environment Validation:[/]")
    for key, status in validation.items():
        status_icon = "✅" if status else "❌"
        console.print(f"  {status_icon} {key.replace('_', ' ').title()}")
    
    console.print()

def demo_content_generation():
    """Demo content generation capabilities."""
    
    console.print("[bold yellow]📝 Content Generation Demo[/]\n")
    
    generator = WorldCupContentGenerator()
    
    # Demo investigation article
    console.print("[cyan]🔍 Generating Investigation Article...[/]")
    investigation = generator.generate_investigation(
        topic="FIFA 2026 Host City Selection Process",
        sources=[
            "FIFA Official Documents (obtained by ObjectWire)",
            "Interview with former FIFA executive",
            "Public records from host city bid committees",
            "Financial disclosure documents"
        ],
        length="long"
    )
    
    console.print(f"✅ Investigation: '{investigation['headline']}'")
    console.print(f"   Category: {investigation['category']}")
    console.print(f"   Word Count: {investigation['metadata']['word_count']}")
    console.print(f"   Sources: {investigation['metadata']['source_count']}")
    console.print(f"   Read Time: {investigation['metadata']['read_time']} minutes\n")
    
    # Demo breaking news
    console.print("[cyan]⚡ Generating Breaking News...[/]")
    breaking = generator.generate_breaking_news(
        headline="Star striker ruled out of World Cup with ACL injury",
        details="Medical tests confirm the injury will keep the player sidelined for 6-8 months, missing the entire tournament.",
        urgency="urgent",
        sources=["Team medical staff", "Player's agent", "FIFA medical committee"]
    )
    
    console.print(f"✅ Breaking News: '{breaking['headline']}'")
    console.print(f"   Urgency: {breaking['urgency'].upper()}")
    console.print(f"   Push Notification: {'✅' if breaking['metadata']['push_notification'] else '❌'}")
    console.print(f"   Immediate Publish: {'✅' if breaking['publishing']['immediate'] else '❌'}\n")
    
    # Demo match analysis
    console.print("[cyan]⚽ Generating Match Analysis...[/]")
    match_info = {
        "home_team": "Brazil",
        "away_team": "Argentina", 
        "score": "2-1",
        "date": "2026-07-15",
        "venue": "MetLife Stadium",
        "match_id": "wc2026_sf1"
    }
    
    analysis = generator.generate_match_analysis(
        match_info=match_info,
        analysis_type="review",
        length="medium"
    )
    
    console.print(f"✅ Match Analysis: '{analysis['headline']}'")
    console.print(f"   Teams: {analysis['match_data']['home_team']} vs {analysis['match_data']['away_team']}")
    console.print(f"   Venue: {analysis['metadata']['venue']}")
    console.print(f"   Competition: {analysis['metadata']['competition']}\n")

def demo_monitoring_system():
    """Demo monitoring capabilities."""
    
    console.print("[bold yellow]📡 Feed Monitoring Demo[/]\n")
    
    # Create monitoring status table
    monitoring_table = Table(title="World Cup Feed Monitoring Status")
    monitoring_table.add_column("Source", style="cyan")
    monitoring_table.add_column("Priority", style="yellow")
    monitoring_table.add_column("Interval", style="green")
    monitoring_table.add_column("Status", style="bold")
    
    feeds = [
        ("FIFA Official", "URGENT", "5 min", "🟢 Active"),
        ("Reuters Sports", "URGENT", "10 min", "🟢 Active"),
        ("ESPN Soccer", "HIGH", "10 min", "🟢 Active"),
        ("BBC Football", "HIGH", "10 min", "🟢 Active"),
        ("AP Sports", "URGENT", "10 min", "🟢 Active"),
        ("Brazil CBF", "HIGH", "20 min", "🟢 Active"),
        ("Argentina AFA", "HIGH", "20 min", "🟢 Active"),
        ("US Soccer", "HIGH", "15 min", "🟢 Active"),
        ("Goal.com", "MEDIUM", "20 min", "🟢 Active"),
        ("The Athletic", "HIGH", "20 min", "🟢 Active")
    ]
    
    for source, priority, interval, status in feeds:
        monitoring_table.add_row(source, priority, interval, status)
    
    console.print(monitoring_table)
    
    # Demo alert system
    console.print("\n[cyan]🚨 Alert System Demo:[/]")
    
    sample_alerts = [
        {
            "urgency": "URGENT",
            "headline": "FIFA President announces surprise resignation",
            "source": "Reuters",
            "category": "investigation",
            "teams": [],
            "confidence": 0.95
        },
        {
            "urgency": "HIGH", 
            "headline": "Mbappé confirms PSG exit ahead of World Cup",
            "source": "ESPN",
            "category": "transfer",
            "teams": ["France"],
            "confidence": 0.85
        },
        {
            "urgency": "MEDIUM",
            "headline": "USA announces preliminary World Cup squad",
            "source": "US Soccer",
            "category": "team_news",
            "teams": ["USA"],
            "confidence": 0.90
        }
    ]
    
    for alert in sample_alerts:
        console.print(f"  🚨 {alert['urgency']}: {alert['headline']}")
        console.print(f"     Source: {alert['source']} | Category: {alert['category']} | Confidence: {alert['confidence']:.0%}")
    
    console.print()

def demo_objectwire_integration():
    """Demo ObjectWire.org integration."""
    
    console.print("[bold yellow]🔗 ObjectWire.org Integration Demo[/]\n")
    
    # Integration status
    integration_panel = Panel.fit(
        """
🟢 ObjectWire.org API: Connected
🟢 Editorial Workflow: Active
🟢 Source Verification: Enabled
🟢 Legal Review: Configured
🔄 Auto-Publishing: Disabled (Editorial review required)

📊 Content Categories:
   • /case/ - FIFA investigations and corruption reports
   • /news/ - Breaking World Cup news and updates
   • /analyst/ - Match analysis and tactical breakdowns
   • /opinion/ - Editorial pieces and tournament predictions

🎯 Publishing Workflow:
   1. AI generates content with sources
   2. Automatic fact-checking and verification
   3. Editorial review (72hr for investigations, 1hr for news)
   4. Legal review for sensitive content
   5. SEO optimization and formatting
   6. Publication to objectwire.org
   7. Social media distribution
   8. Performance analytics tracking
        """,
        title="[bold green]Integration Status[/]",
        border_style="green"
    )
    
    console.print(integration_panel)
    
    # Demo publication stats
    console.print("\n[cyan]📈 Publication Statistics (Demo):[/]")
    
    stats_table = Table(title="Content Performance Metrics")
    stats_table.add_column("Content Type", style="cyan")
    stats_table.add_column("Articles", style="yellow")
    stats_table.add_column("Avg. Views", style="green") 
    stats_table.add_column("Social Shares", style="blue")
    stats_table.add_column("Engagement", style="magenta")
    
    stats_table.add_row("Investigations", "0", "0", "0", "0%")
    stats_table.add_row("Breaking News", "0", "0", "0", "0%")
    stats_table.add_row("Match Analysis", "0", "0", "0", "0%")
    stats_table.add_row("Live Updates", "0", "0", "0", "0%")
    
    console.print(stats_table)
    console.print("[dim]Note: Demo mode - actual statistics will show once content is published[/]\n")

async def demo_live_features():
    """Demo live features (async)."""
    
    console.print("[bold yellow]🔴 Live Features Demo[/]\n")
    
    console.print("[cyan]Starting live match simulation...[/]")
    
    # Simulate live match updates
    live_updates = [
        (1, "⚽ Kickoff! Brazil vs Argentina in the World Cup semifinal"),
        (15, "🟨 Yellow card for Argentina midfielder"),
        (23, "⚽ GOAL! Brazil takes the lead 1-0"),
        (45, "⏱️ Halftime: Brazil 1-0 Argentina"),
        (67, "⚽ GOAL! Argentina equalizes 1-1"),
        (78, "🔄 Substitution: Brazil brings on fresh legs"),
        (89, "⚽ GOAL! Brazil scores dramatic late winner 2-1"),
        (90, "⏱️ Full time: Brazil 2-1 Argentina")
    ]
    
    for minute, update in live_updates:
        console.print(f"  {minute}' - {update}")
        await asyncio.sleep(0.5)  # Simulate real-time
    
    console.print("\n✅ Live match coverage completed!")
    console.print("📊 Match statistics and post-game analysis generated automatically\n")

def main():
    """Main demo function."""
    
    try:
        # Run synchronous demos
        demo_world_cup_system()
        
        # Ask if user wants to see live features demo
        console.print("[bold cyan]Would you like to see the live features demo? [y/N]: [/]", end="")
        
        try:
            response = input().lower().strip()
            if response in ['y', 'yes']:
                console.print()
                asyncio.run(demo_live_features())
        except KeyboardInterrupt:
            console.print("\n[yellow]Demo interrupted by user[/]")
        
        # Show next steps
        console.print("[bold green]🚀 Ready to start? Try these commands:[/]")
        console.print("  • [cyan]python worldcup_cli.py[/] - Start the CLI")
        console.print("  • [cyan]python worldcup_monitor.py[/] - Test feed monitoring")
        console.print("  • [cyan]python worldcup_config.py[/] - Check configuration")
        console.print("  • [cyan]pip install -e .[/] - Install as CLI command\n")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Demo stopped by user. Thanks for checking out ObjectWire World Cup![/]")

if __name__ == "__main__":
    main()