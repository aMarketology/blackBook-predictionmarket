"""
ObjectWire Gemini Writer
========================
Content generation using Google Gemini 2.0 Flash for articles, threads, and market descriptions.

Why Gemini 2.0?
- 2M token context window (massive!)
- Faster than GPT-4 (avg 50 tokens/sec)
- Cheaper: $0.075/$0.30 per 1M tokens (input/output)
- Multimodal support (text, images, video)
- Better at following complex instructions
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("google-generativeai not installed. Run: pip install google-generativeai")

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class GeminiWriter:
    """Content generation using Google Gemini 2.0 Flash."""
    
    # Available models (as of Dec 2025)
    MODELS = {
        'flash': 'gemini-2.0-flash-exp',           # Fastest, recommended
        'pro': 'gemini-2.0-pro',                    # Most capable
        'thinking': 'gemini-2.0-flash-thinking-exp' # Extended reasoning
    }
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: str = 'flash',
        temperature: float = 0.7,
        max_output_tokens: int = 8192
    ):
        """Initialize Gemini writer.
        
        Args:
            api_key: Google AI API key (or set GEMINI_API_KEY env var)
            model: Model to use ('flash', 'pro', or 'thinking')
            temperature: Sampling temperature (0.0-2.0)
            max_output_tokens: Maximum tokens to generate
        """
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai not installed")
        
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        genai.configure(api_key=self.api_key)
        
        self.model_name = self.MODELS.get(model, self.MODELS['flash'])
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        
        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                'temperature': self.temperature,
                'max_output_tokens': self.max_output_tokens,
                'top_p': 0.95,
                'top_k': 40,
            }
        )
        
        logger.info(f"Initialized Gemini Writer with model: {self.model_name}")
    
    def write_article(
        self,
        event: Dict[str, Any],
        template: str = 'analysis',
        length: int = 750,
        style: str = 'formal',
        seo: bool = False
    ) -> Dict[str, str]:
        """Generate article about prediction market event.
        
        Args:
            event: Event dictionary with title, description, etc.
            template: Article template (analysis, news, profile, tutorial)
            length: Target word count
            style: Writing style (formal, casual, hype, technical)
            seo: Optimize for SEO
            
        Returns:
            Dictionary with 'title', 'content', 'meta_description', 'keywords'
        """
        # Build prompt based on template
        prompt = self._build_article_prompt(event, template, length, style, seo)
        
        try:
            start_time = time.time()
            response = self.model.generate_content(prompt)
            elapsed = time.time() - start_time
            
            logger.info(f"Generated article in {elapsed:.2f}s")
            
            # Parse response
            article = self._parse_article_response(response.text)
            article['generation_time'] = elapsed
            article['model'] = self.model_name
            
            return article
            
        except Exception as e:
            logger.error(f"Article generation failed: {e}")
            raise
    
    def write_thread(
        self,
        event: Dict[str, Any],
        num_tweets: int = 5,
        style: str = 'informative',
        hashtags: bool = False
    ) -> Dict[str, Any]:
        """Generate Twitter/X thread about event.
        
        Args:
            event: Event dictionary
            num_tweets: Number of tweets in thread (3-15)
            style: Thread style (hype, informative, question, debate)
            hashtags: Include relevant hashtags
            
        Returns:
            Dictionary with 'tweets' list and metadata
        """
        prompt = self._build_thread_prompt(event, num_tweets, style, hashtags)
        
        try:
            start_time = time.time()
            response = self.model.generate_content(prompt)
            elapsed = time.time() - start_time
            
            logger.info(f"Generated thread in {elapsed:.2f}s")
            
            # Parse tweets
            thread = self._parse_thread_response(response.text, num_tweets)
            thread['generation_time'] = elapsed
            thread['model'] = self.model_name
            
            return thread
            
        except Exception as e:
            logger.error(f"Thread generation failed: {e}")
            raise
    
    def write_description(
        self,
        event: Dict[str, Any],
        max_length: int = 500,
        include_rules: bool = True
    ) -> str:
        """Generate market description for blockchain.
        
        Args:
            event: Event dictionary
            max_length: Maximum character length
            include_rules: Include resolution rules
            
        Returns:
            Market description string
        """
        prompt = self._build_description_prompt(event, max_length, include_rules)
        
        try:
            response = self.model.generate_content(prompt)
            description = response.text.strip()
            
            # Ensure length limit
            if len(description) > max_length:
                description = description[:max_length-3] + "..."
            
            return description
            
        except Exception as e:
            logger.error(f"Description generation failed: {e}")
            raise
    
    def _build_article_prompt(
        self,
        event: Dict[str, Any],
        template: str,
        length: int,
        style: str,
        seo: bool
    ) -> str:
        """Build prompt for article generation."""
        
        base_prompt = f"""You are a professional content writer for ObjectWire, a prediction market platform.

Write a {length}-word article about this prediction market:

**Event Details:**
- Title: {event.get('title')}
- Description: {event.get('description', 'N/A')}
- Category: {event.get('category', 'general')}
- Resolution Date: {event.get('resolution_date', 'TBD')}
- Current Probabilities:
  - Yes: {event.get('yes_prob', 0)*100:.0f}%
  - No: {event.get('no_prob', 0)*100:.0f}%
  - No Change: {event.get('no_change_prob', 0)*100:.0f}%

"""

        # Template-specific instructions
        if template == 'analysis':
            base_prompt += """**Template: Market Analysis**
Structure:
1. Hook (1-2 sentences about why this market matters)
2. Context (background on the event/topic)
3. Analysis (examine the probabilities and factors)
4. Key Factors (what could influence the outcome)
5. Market Perspective (how traders are viewing this)
6. Conclusion (actionable insights)

"""
        elif template == 'news':
            base_prompt += """**Template: News Article**
Structure:
1. Headline (attention-grabbing)
2. Lede (who, what, when, where, why in first paragraph)
3. Background (context and history)
4. Details (key facts and quotes)
5. Implications (what this means)
6. Call to Action (invite readers to participate)

"""
        elif template == 'profile':
            base_prompt += """**Template: Profile/Feature**
Structure:
1. Introduction (who or what is being profiled)
2. Background (history and context)
3. Current Status (present situation)
4. Analysis (deeper examination)
5. Future Outlook (predictions)
6. Conclusion

"""
        elif template == 'tutorial':
            base_prompt += """**Template: Tutorial/Guide**
Structure:
1. Introduction (what readers will learn)
2. Prerequisites (what they need to know)
3. Step-by-step guide (clear numbered steps)
4. Examples (practical scenarios)
5. Tips & Best Practices
6. Conclusion (summary and next steps)

"""
        
        # Style instructions
        style_guide = {
            'formal': 'Use professional, academic tone. Cite sources. Avoid slang.',
            'casual': 'Conversational tone. Use contractions. Relatable examples.',
            'hype': 'Energetic, exciting tone. Use emojis sparingly. Create FOMO.',
            'technical': 'Data-driven. Include statistics. Explain mechanisms.'
        }
        
        base_prompt += f"**Style**: {style_guide.get(style, style_guide['formal'])}\n\n"
        
        # SEO instructions
        if seo:
            base_prompt += """**SEO Requirements**:
- Include target keywords naturally (prediction market, {category}, betting)
- Write compelling meta description (150-160 chars)
- Use H2/H3 headings
- Include relevant statistics and data
- Add internal/external link suggestions

"""
        
        base_prompt += """**Output Format**:
```
TITLE: [Compelling article title]

META_DESCRIPTION: [150-160 char SEO description]

KEYWORDS: [5-7 relevant keywords, comma-separated]

CONTENT:
[Full article in markdown format with headings]
```

Generate the article now:"""
        
        return base_prompt
    
    def _build_thread_prompt(
        self,
        event: Dict[str, Any],
        num_tweets: int,
        style: str,
        hashtags: bool
    ) -> str:
        """Build prompt for thread generation."""
        
        prompt = f"""You are a social media manager for ObjectWire prediction markets.

Create a {num_tweets}-tweet thread about this market:

**Event**: {event.get('title')}
**Category**: {event.get('category', 'general')}
**Description**: {event.get('description', 'N/A')}
**Probabilities**: Yes {event.get('yes_prob', 0)*100:.0f}% | No {event.get('no_prob', 0)*100:.0f}%

"""
        
        # Style instructions
        if style == 'hype':
            prompt += """**Style: Hype/Excitement**
- Create FOMO and excitement
- Use emojis (🚀🔥💰📊)
- Short, punchy sentences
- Call to action
"""
        elif style == 'informative':
            prompt += """**Style: Informative/Educational**
- Share insights and analysis
- Include statistics
- Explain key concepts
- Value-driven content
"""
        elif style == 'question':
            prompt += """**Style: Question/Engagement**
- Start with compelling question
- Present both sides
- Invite discussion
- Thought-provoking
"""
        elif style == 'debate':
            prompt += """**Style: Debate/Controversy**
- Present contrasting viewpoints
- Challenge assumptions
- Provocative but respectful
- Encourage engagement
"""
        
        # Hashtag instructions
        if hashtags:
            prompt += "\n- Include 2-3 relevant hashtags per tweet\n"
        
        prompt += f"""
**Rules**:
- Each tweet must be ≤280 characters
- Number tweets (1/{num_tweets}, 2/{num_tweets}, etc.)
- First tweet is the hook (grab attention)
- Last tweet is CTA (link to market)
- Use line breaks for readability

**Output Format**:
```
Tweet 1/{num_tweets}:
[Tweet text]

Tweet 2/{num_tweets}:
[Tweet text]

...
```

Generate the thread now:"""
        
        return prompt
    
    def _build_description_prompt(
        self,
        event: Dict[str, Any],
        max_length: int,
        include_rules: bool
    ) -> str:
        """Build prompt for market description."""
        
        prompt = f"""Write a concise market description (max {max_length} characters) for this prediction market:

**Title**: {event.get('title')}
**Category**: {event.get('category', 'general')}
**Resolution Date**: {event.get('resolution_date', 'TBD')}
**Source**: {event.get('source_url', 'N/A')}

"""
        
        if include_rules:
            prompt += """Include:
1. Clear description of what is being predicted
2. Resolution criteria (how outcome will be determined)
3. Resolution date
4. Source for verification

"""
        else:
            prompt += "Provide a clear, concise description of what is being predicted.\n\n"
        
        prompt += f"**Character limit**: {max_length} (strict)\n\n"
        prompt += "Generate the description now:"
        
        return prompt
    
    def _parse_article_response(self, response: str) -> Dict[str, str]:
        """Parse article response into structured format."""
        
        article = {
            'title': '',
            'content': '',
            'meta_description': '',
            'keywords': '',
            'raw_response': response
        }
        
        try:
            # Extract title
            if 'TITLE:' in response:
                title_start = response.find('TITLE:') + 6
                title_end = response.find('\n', title_start)
                article['title'] = response[title_start:title_end].strip()
            
            # Extract meta description
            if 'META_DESCRIPTION:' in response:
                meta_start = response.find('META_DESCRIPTION:') + 17
                meta_end = response.find('\n', meta_start)
                article['meta_description'] = response[meta_start:meta_end].strip()
            
            # Extract keywords
            if 'KEYWORDS:' in response:
                kw_start = response.find('KEYWORDS:') + 9
                kw_end = response.find('\n', kw_start)
                article['keywords'] = response[kw_start:kw_end].strip()
            
            # Extract content
            if 'CONTENT:' in response:
                content_start = response.find('CONTENT:') + 8
                article['content'] = response[content_start:].strip()
            else:
                # Fallback: use everything after keywords
                if 'KEYWORDS:' in response:
                    kw_end = response.find('\n', response.find('KEYWORDS:'))
                    article['content'] = response[kw_end:].strip()
                else:
                    article['content'] = response
            
        except Exception as e:
            logger.warning(f"Error parsing article: {e}")
            article['content'] = response
        
        return article
    
    def _parse_thread_response(self, response: str, expected_tweets: int) -> Dict[str, Any]:
        """Parse thread response into list of tweets."""
        
        thread = {
            'tweets': [],
            'total_tweets': 0,
            'raw_response': response
        }
        
        try:
            # Split by "Tweet X/" pattern
            lines = response.split('\n')
            current_tweet = ''
            
            for line in lines:
                # Check if this is a tweet number line
                if 'Tweet' in line and '/' in line:
                    # Save previous tweet if exists
                    if current_tweet.strip():
                        thread['tweets'].append(current_tweet.strip())
                    current_tweet = ''
                else:
                    current_tweet += line + '\n'
            
            # Add last tweet
            if current_tweet.strip():
                thread['tweets'].append(current_tweet.strip())
            
            thread['total_tweets'] = len(thread['tweets'])
            
            # Validate tweet lengths
            for i, tweet in enumerate(thread['tweets']):
                if len(tweet) > 280:
                    logger.warning(f"Tweet {i+1} exceeds 280 chars: {len(tweet)}")
            
        except Exception as e:
            logger.warning(f"Error parsing thread: {e}")
            thread['tweets'] = [response]
        
        return thread
    
    def test_connection(self) -> bool:
        """Test Gemini API connection.
        
        Returns:
            True if connection successful
        """
        try:
            test_prompt = "Say 'Hello from Gemini!' in exactly 3 words."
            response = self.model.generate_content(test_prompt)
            logger.info(f"Gemini test successful: {response.text}")
            return True
        except Exception as e:
            logger.error(f"Gemini test failed: {e}")
            return False


def get_writer(model: str = 'flash', **kwargs) -> GeminiWriter:
    """Get or create Gemini writer instance.
    
    Args:
        model: Model to use ('flash', 'pro', 'thinking')
        **kwargs: Additional arguments for GeminiWriter
        
    Returns:
        GeminiWriter instance
    """
    return GeminiWriter(model=model, **kwargs)


# Singleton instance
_writer_instance: Optional[GeminiWriter] = None

def get_default_writer() -> GeminiWriter:
    """Get default Gemini writer instance (singleton).
    
    Returns:
        GeminiWriter instance
    """
    global _writer_instance
    if _writer_instance is None:
        _writer_instance = GeminiWriter()
    return _writer_instance
