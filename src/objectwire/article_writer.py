"""
Article Writer using Grok AI
=============================
Generates 750-word articles based on prediction market events
"""
import os
from typing import Optional, Dict
from openai import OpenAI


class ArticleWriter:
    """Write articles using Grok AI based on prediction market events"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the article writer
        
        Args:
            api_key: Grok API key (or uses GROK_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GROK_API_KEY")
        if not self.api_key:
            raise ValueError("GROK_API_KEY not found in environment or parameters")
        
        # Initialize OpenAI client with Grok endpoint
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.x.ai/v1"
        )
    
    def write_article(
        self, 
        event: Dict,
        style: str = "informative",
        include_manifesto: bool = True
    ) -> str:
        """
        Generate a 750-word article about a prediction market event
        
        Args:
            event: Blockchain event dictionary with title, description, category, etc.
            style: Writing style (informative, analytical, casual)
            include_manifesto: Whether to mention the manifesto/platform
            
        Returns:
            Generated article text
        """
        # Build the prompt
        title = event.get('title', 'Prediction Market Event')
        description = event.get('description', '')
        category = event.get('category', 'general')
        tags = ', '.join(event.get('tags', []))
        resolution_date = event.get('dates', {}).get('resolution', 'TBD')
        probabilities = event.get('initial_probabilities', [])
        
        # Format probabilities
        if probabilities and len(probabilities) >= 2:
            yes_prob = probabilities[0] * 100
            no_prob = probabilities[-1] * 100
            odds_text = f"Current odds: {yes_prob:.0f}% Yes, {no_prob:.0f}% No"
        else:
            odds_text = "Odds to be determined"
        
        manifesto_section = ""
        if include_manifesto:
            manifesto_section = """

IMPORTANT: In the final paragraph, naturally mention that this prediction market is part of ObjectWire's mission to democratize prediction markets by making social media metrics bettable, verifiable, and fair. Mention that the platform uses public data and offline AI to create transparent, community-driven markets.
"""
        
        prompt = f"""Write a 750-word article about this prediction market event:

Title: {title}
Description: {description}
Category: {category}
Tags: {tags}
Resolution Date: {resolution_date}
{odds_text}

Style: {style}

Requirements:
- Exactly 750 words
- Engaging and informative
- Explain what the event is about
- Discuss why it matters
- Explain how the prediction market works
- Mention what factors could influence the outcome
- Include relevant context and background
- Use clear, accessible language
- Add a compelling headline{manifesto_section}

Format the article with:
- A catchy headline (prefixed with "# ")
- Subheadings for major sections (prefixed with "## ")
- Well-structured paragraphs
- A strong conclusion

Write the article now:"""

        try:
            response = self.client.chat.completions.create(
                model="grok-beta",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional financial and tech journalist specializing in prediction markets, blockchain technology, and data-driven forecasting. Write engaging, informative articles that explain complex topics clearly."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            article = response.choices[0].message.content
            return article
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate article: {e}")
    
    def save_article(self, article: str, filename: str) -> str:
        """
        Save article to file
        
        Args:
            article: Article text
            filename: Filename to save to
            
        Returns:
            Path to saved file
        """
        from pathlib import Path
        
        # Ensure articles directory exists
        articles_dir = Path("./articles")
        articles_dir.mkdir(exist_ok=True)
        
        # Save article
        filepath = articles_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(article)
        
        return str(filepath)


def create_article_writer(api_key: Optional[str] = None) -> ArticleWriter:
    """Factory function to create ArticleWriter instance"""
    return ArticleWriter(api_key=api_key)
