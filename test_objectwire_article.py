#!/usr/bin/env python3
"""
Test blockchain extraction with ObjectWire article about Alphabet vs Nvidia
"""
from src.objectwire.llama_engine import create_nuextract_engine
from bs4 import BeautifulSoup
import requests
import json

def main():
    # Scrape the article
    url = 'https://www.objectwire.org/alphabet-or-nvidia-here-s-who-i-think-will-win-the-ai-chip-war'
    print('🌐 Scraping article...')
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract title
    title = soup.find('h1').get_text(strip=True) if soup.find('h1') else 'AI Chip War'
    print(f'📰 Title: {title}')

    # Extract content
    article = soup.find('article') or soup.find('main') or soup.find(class_='entry-content')
    if article:
        content = article.get_text(separator=' ', strip=True)[:2000]
    else:
        content = ' '.join([p.get_text(strip=True) for p in soup.find_all('p')])[:2000]

    print(f'📝 Content length: {len(content)} chars')
    print(f'📝 Preview: {content[:150]}...\n')

    # Initialize AI engine
    print('🤖 Loading NuExtract AI engine...')
    engine = create_nuextract_engine()
    print('✅ AI engine ready!\n')

    # Extract blockchain event using AI
    print('🔮 Analyzing article with AI (this takes ~10-15 seconds)...')
    event = engine.analyze_article_blockchain(title, content, url)
    print('✅ AI extraction complete!\n')

    # Display results
    print('=' * 70)
    print('📊 BLOCKCHAIN EVENT EXTRACTED')
    print('=' * 70)
    print(f'\n📋 Source ID: {event.source}')
    print(f'📌 Market Title: {event.title}')
    print(f'\n📝 Description:\n   {event.description[:200]}...')
    print(f'\n🏷️  Category: {event.category}')
    tags_str = ", ".join(event.tags)
    print(f'🔖 Tags: {tags_str}')
    print(f'\n🎯 Market Type: {event.market_type}')
    outcomes_str = ", ".join(event.outcomes)
    print(f'📊 Outcomes: {outcomes_str}')
    
    if event.initial_probabilities:
        probs = event.initial_probabilities
        print(f'\n🎲 Initial Probabilities:')
        print(f'   • Yes: {probs[0]:.1%}')
        print(f'   • No Change: {probs[1]:.1%}')
        print(f'   • No: {probs[2]:.1%}')
    
    print(f'\n📅 Dates:')
    print(f'   • Published: {event.dates["published"]}')
    freeze = event.dates.get("freeze")
    print(f'   • Freeze: {freeze if freeze else "Not set"}')
    resolution = event.dates.get("resolution")
    print(f'   • Resolution: {resolution if resolution else "Not set"}')
    
    if event.resolution_rules:
        print(f'\n🔮 Resolution Oracle:')
        print(f'   • Provider: {event.resolution_rules.get("provider")}')
        print(f'   • Data Source: {event.resolution_rules.get("data_source")}')
        conditions = event.resolution_rules.get('conditions', {})
        print(f'   • YES condition: {conditions.get("YES", "N/A")}')
        print(f'   • NO condition: {conditions.get("NO", "N/A")}')
    
    print('\n' + '=' * 70)
    print('📄 FULL JSON FOR BLOCKCHAIN API')
    print('=' * 70)
    print(json.dumps(event.model_dump(), indent=2))
    print('\n✅ Ready to post to blockchain!')

if __name__ == "__main__":
    main()
