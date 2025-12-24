#!/usr/bin/env python3
"""
Test script for new blockchain event format
"""
import json
from src.objectwire.llama_engine import create_nuextract_engine

def test_blockchain_extraction():
    """Test the new blockchain format extraction"""
    
    print("🧪 Testing Blockchain Event Format Extraction\n")
    print("=" * 60)
    
    # Initialize engine
    print("\n1️⃣  Initializing NuExtract engine...")
    engine = create_nuextract_engine()
    
    # Test article about crypto
    test_cases = [
        {
            "title": "Bitcoin Breaks $100k Barrier, Analysts Predict Further Gains",
            "content": """
            Bitcoin surpassed the $100,000 milestone for the first time today, 
            reaching $102,450 on Coinbase at 2:15 PM EST. The cryptocurrency 
            has rallied 45% this quarter driven by institutional adoption and 
            ETF inflows. Market analysts at Bloomberg predict BTC could reach 
            $150k by Q2 2025 if the current trajectory continues. The surge 
            comes as MicroStrategy announced an additional $1B bitcoin purchase.
            """,
            "url": "https://coindesk.com/markets/2024/12/24/bitcoin-breaks-100k"
        },
        {
            "title": "MrBeast Announces 100 New Feastables Stores Coming to Walmart",
            "content": """
            YouTube star MrBeast revealed plans to expand his Feastables 
            chocolate brand to 100 additional Walmart locations by summer 2025. 
            The announcement came during a livestream where he showcased new 
            product flavors. Currently available in 300 stores, the expansion 
            would bring Feastables to over 400 Walmart locations nationwide. 
            The brand has generated over $10M in sales since launching last year.
            """,
            "url": "https://tubefilter.com/2024/12/24/mrbeast-feastables-walmart-expansion"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}️⃣  Processing: {test['title'][:50]}...")
        print("-" * 60)
        
        try:
            # Extract using new blockchain format
            event = engine.analyze_article_blockchain(
                title=test['title'],
                content=test['content'],
                url=test['url']
            )
            
            # Display results
            print(f"\n✅ Extracted Blockchain Event:")
            print(f"\n📋 Source ID: {event.source}")
            print(f"📌 Title: {event.title}")
            print(f"📝 Description: {event.description[:100]}...")
            print(f"🏷️  Category: {event.category}")
            print(f"🔖 Tags: {', '.join(event.tags)}")
            print(f"🎯 Market Type: {event.market_type}")
            print(f"📊 Outcomes: {', '.join(event.outcomes)}")
            
            if event.initial_probabilities:
                probs = event.initial_probabilities
                print(f"🎲 Initial Odds: Yes={probs[0]:.1%}, No Change={probs[1]:.1%}, No={probs[2]:.1%}")
            
            print(f"📅 Published: {event.dates['published']}")
            print(f"❄️  Freeze: {event.dates.get('freeze', 'Not set')}")
            print(f"✅ Resolution: {event.dates.get('resolution', 'Not set')}")
            
            if event.resolution_rules:
                print(f"\n🔮 Resolution Oracle:")
                print(f"   Provider: {event.resolution_rules.get('provider')}")
                print(f"   Data Source: {event.resolution_rules.get('data_source')}")
                conditions = event.resolution_rules.get('conditions', {})
                print(f"   YES condition: {conditions.get('YES', 'N/A')}")
                print(f"   NO condition: {conditions.get('NO', 'N/A')}")
            
            # Show full JSON
            print(f"\n📄 Full Blockchain JSON:")
            print(json.dumps(event.model_dump(), indent=2))
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Test complete!\n")


if __name__ == "__main__":
    test_blockchain_extraction()
