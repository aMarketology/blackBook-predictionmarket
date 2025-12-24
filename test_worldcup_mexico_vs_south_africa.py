#!/usr/bin/env python3
"""
Test AI extraction for World Cup match: Mexico vs South Africa
June 11, 2026 - Opening Match in Mexico City
"""

from src.objectwire.llama_engine import NuExtractEngine, LlamaConfig
import json

# Mock article about the World Cup match
article_content = """
Mexico vs South Africa - 2026 FIFA World Cup Opening Match

The 2026 FIFA World Cup kicks off Thursday, June 11, 2026, in Mexico City 
at Estadio Azteca, featuring co-host Mexico against South Africa.

Match Details:
- Date: June 11, 2026, 8:00 PM Mexico City time
- Venue: Estadio Azteca (87,000 capacity - sold out)
- Betting odds: Mexico 60%, Draw 25%, South Africa 15%

Mexico enters as favorites with home advantage. South Africa hopes to upset 
the hosts in this opening fixture.

Resolution: Official FIFA match result determines outcome after final whistle.
Data Source: fifa_api_v1 official results
"""

def main():
    print("🤖 Loading NuExtract AI...")
    config = LlamaConfig(model_path="./models/nuextract-smol-1.5-q4_k_m.gguf")
    engine = NuExtractEngine(config=config)
    print("✅ Loaded!\n")

    print("🔮 Analyzing World Cup match (10-15 sec)...\n")
    
    # Get BlockchainEvent object
    event_obj = engine.analyze_article_blockchain(
        title="Mexico vs South Africa - 2026 World Cup Opening Match",
        content=article_content,
        url="https://example.com/worldcup/mexico-vs-south-africa"
    )
    
    # Convert to dict properly
    event = event_obj.model_dump() if hasattr(event_obj, 'model_dump') else event_obj.dict()
    
    # Display results
    print("\n" + "="*70)
    print("⚽ BLOCKCHAIN EVENT - WORLD CUP 2026 OPENING MATCH")
    print("="*70)
    
    print(f"\n📌 Source: {event['source']}")
    print(f"📌 Title: {event['title']}")
    print(f"\n📝 Description:")
    print(f"   {event['description'][:250]}...")
    
    print(f"\n🏷️  Category: {event['category']}")
    print(f"🔖 Tags: {', '.join('#' + t for t in event['tags'])}")
    
    print(f"\n🎯 Market Type: {event['market_type']}")
    print(f"📊 Outcomes: {', '.join(event['outcomes'])}")
    
    print(f"\n🎲 Probabilities:")
    for outcome, prob in zip(event['outcomes'], event['initial_probabilities']):
        print(f"   {outcome}: {prob*100:.1f}%")
    
    print(f"\n📅 Dates:")
    print(f"   Published: {event['dates']['published']}")
    print(f"   Freeze: {event['dates']['freeze']}")
    print(f"   Resolution: {event['dates']['resolution']}")
    
    if event.get('resolution_rules'):
        print(f"\n🔮 Resolution:")
        print(f"   Provider: {event['resolution_rules']['provider']}")
        print(f"   Source: {event['resolution_rules']['data_source']}")
        if isinstance(event['resolution_rules']['conditions'], dict):
            print(f"   YES: {event['resolution_rules']['conditions'].get('YES', 'N/A')}")
            print(f"   NO: {event['resolution_rules']['conditions'].get('NO', 'N/A')}")
    
    print("\n" + "="*70)
    print("📤 JSON FOR BLOCKCHAIN API")
    print("="*70)
    print(json.dumps(event, indent=2))
    
    print(f"\n✅ Ready to POST to: http://localhost:3000/markets")

if __name__ == "__main__":
    main()
