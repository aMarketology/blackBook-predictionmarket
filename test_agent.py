"""
Quick test script for the BlackBook URL Scraping AI Agent
Run this to test the agent functionality
"""

import requests
import json
import time

AGENT_URL = "http://localhost:8082"

def test_health():
    """Test health endpoint"""
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get(f"{AGENT_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data['status']}")
            print(f"   🤖 OpenAI: {data['openai']}")
            print(f"   🔗 Blockchain: {data['blockchain']}")
            return True
        else:
            print(f"   ❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_analyze():
    """Test URL analysis without market creation"""
    print("\n🔍 Testing URL analysis...")
    
    test_urls = [
        "https://techcrunch.com",
        "https://www.coindesk.com",
    ]
    
    for url in test_urls:
        try:
            print(f"\n   Analyzing: {url}")
            response = requests.post(
                f"{AGENT_URL}/analyze",
                json={"url": url, "category": "tech"},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Title: {data['title'][:60]}...")
                print(f"   📊 Category: {data['category']}")
                print(f"   🎯 Options: {len(data['options'])} options")
                print(f"   💯 Confidence: {data['confidence']}")
            else:
                print(f"   ❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        time.sleep(2)  # Rate limiting

def test_scrape():
    """Test full scraping with market creation"""
    print("\n🚀 Testing scrape + market creation...")
    
    test_url = "https://techcrunch.com"
    
    try:
        print(f"   URL: {test_url}")
        response = requests.post(
            f"{AGENT_URL}/scrape",
            json={
                "url": test_url,
                "category": "tech",
                "auto_create_market": False  # Set to True when blockchain is ready
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {data['success']}")
            print(f"   📝 Title: {data['event_data']['title'][:60]}...")
            print(f"   🎯 Options: {data['event_data']['options']}")
            print(f"   💬 Message: {data['message']}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

def test_markets():
    """Test getting markets from blockchain"""
    print("\n📊 Testing market retrieval...")
    try:
        response = requests.get(f"{AGENT_URL}/markets")
        if response.status_code == 200:
            markets = response.json()
            print(f"   ✅ Found {len(markets)} markets")
            if markets:
                print(f"   Latest: {markets[0].get('title', 'N/A')[:60]}...")
        else:
            print(f"   ⚠️  No markets found or blockchain not running")
    except Exception as e:
        print(f"   ⚠️  Error: {str(e)}")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 BlackBook URL Scraping AI Agent - Test Suite")
    print("=" * 60)
    print("\nMake sure the agent is running on port 8082!")
    print("Start it with: python serve_frontend.py")
    print("\n" + "=" * 60)
    
    # Run tests
    if test_health():
        test_analyze()
        test_scrape()
        test_markets()
    else:
        print("\n❌ Agent not responding. Please start it first!")
        print("   Run: python serve_frontend.py")
    
    print("\n" + "=" * 60)
    print("✅ Test suite complete!")
    print("=" * 60)
