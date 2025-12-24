"""
llama.cpp Engine for ObjectWire - Specialized for NuExtract
===========================================================
Provides Python interface to llama.cpp with NuExtract-specific prompting
"""
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse


class BlockchainEvent(BaseModel):
    """Complete blockchain event format matching API spec"""
    source: str
    title: str
    description: str
    category: str
    tags: List[str] = Field(default_factory=list)
    market_type: str = "three_choice"
    outcomes: List[str] = Field(default_factory=lambda: ["Yes", "No Change", "No"])
    initial_probabilities: Optional[List[float]] = None
    source_url: str
    image_url: Optional[str] = None
    dates: Dict[str, Optional[str]]
    resolution_rules: Optional[Dict[str, Any]] = None


class PredictionEvent(BaseModel):
    """Structured prediction event for blockchain (legacy)"""
    title: str
    description: str
    category: str
    tags: List[str]
    key_entities: List[str]
    confidence: float
    resolution_date: str
    resolution_criteria: str
    options: List[str]
    source_url: str


@dataclass
class LlamaConfig:
    """Configuration for llama.cpp"""
    model_path: str
    llama_cli_path: str = "llama-cli"
    context_size: int = 2048  # Reduced from 4096 for faster processing
    threads: int = 8
    temperature: float = 0.1  # Low temp for structured extraction
    top_p: float = 0.9
    max_tokens: int = 256  # Reduced from 1024 - simpler schema needs less tokens
    gpu_layers: int = 99  # Use all GPU layers


class NuExtractEngine:
    """
    Specialized engine for NuExtract model
    NuExtract requires specific prompt formatting for structured extraction
    """
    
    def __init__(self, config: LlamaConfig):
        self.config = config
        self._validate_setup()
    
    def _validate_setup(self):
        """Ensure llama.cpp and model are available"""
        # Check llama-cli exists
        try:
            result = subprocess.run(
                [self.config.llama_cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise FileNotFoundError(f"llama-cli not found")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            raise FileNotFoundError(
                "❌ llama-cli not found. Install with: brew install llama.cpp"
            )
        
        # Check model exists
        if not Path(self.config.model_path).exists():
            raise FileNotFoundError(
                f"❌ Model not found at: {self.config.model_path}\n"
                f"Download NuExtract to: {Path(self.config.model_path).parent}"
            )
        
        print(f"✅ NuExtract initialized: {Path(self.config.model_path).name}")
    
    def _build_nuextract_prompt(self, schema: Dict, text: str) -> str:
        """
        Build NuExtract-specific prompt format
        
        NuExtract expects:
        <|input|>
        ### Template:
        {schema}
        ### Text:
        {text}
        <|output|>
        """
        schema_str = json.dumps(schema, indent=2)
        
        prompt = f"""<|input|>
### Template:
{schema_str}

### Text:
{text}

<|output|>
"""
        return prompt
    
    def extract(self, prompt: str, stop_tokens: List[str] = None) -> str:
        """
        Run llama.cpp inference with NuExtract
        
        Args:
            prompt: Formatted NuExtract prompt
            stop_tokens: Tokens to stop generation
            
        Returns:
            Generated text
        """
        if stop_tokens is None:
            stop_tokens = ["<|end|>", "\n\n\n", "<|input|>"]
        
        # Build command - single-turn, non-interactive mode
        cmd = [
            self.config.llama_cli_path,
            "-m", self.config.model_path,
            "-p", prompt,
            "-n", str(self.config.max_tokens),
            "-c", str(self.config.context_size),
            "-t", str(self.config.threads),
            "--temp", str(self.config.temperature),
            "--top-p", str(self.config.top_p),
            "-ngl", str(self.config.gpu_layers),
            "--no-display-prompt",
            "--no-conversation",  # Disable conversation mode
            "-st",  # Single turn mode - exit after generation
        ]
        
        # Add stop tokens
        for stop in stop_tokens:
            cmd.extend(["--reverse-prompt", stop])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # Give it 60 seconds
            )
            
            if result.returncode != 0:
                print(f"⚠️  llama-cli stderr: {result.stderr[:500]}")
                raise RuntimeError(f"llama.cpp error: {result.stderr}")
            
            output = result.stdout.strip()
            
            # Clean up output
            output = self._clean_output(output)
            
            return output
        
        except subprocess.TimeoutExpired:
            raise TimeoutError("AI generation timed out after 2 minutes")
        except Exception as e:
            raise RuntimeError(f"Error running llama.cpp: {e}")
    
    def _clean_output(self, output: str) -> str:
        """Clean up model output"""
        # Remove any remaining prompt artifacts
        if "<|output|>" in output:
            output = output.split("<|output|>")[-1]
        
        # Remove stop tokens
        for stop in ["<|end|>", "\n\n\n"]:
            if stop in output:
                output = output.split(stop)[0]
        
        return output.strip()
    
    def analyze_article_blockchain(self, title: str, content: str, url: str) -> BlockchainEvent:
        """
        Analyze article and extract blockchain-ready event using NuExtract
        
        Args:
            title: Article title
            content: Article content (will be truncated)
            url: Source URL
            
        Returns:
            Complete BlockchainEvent matching API spec
        """
        # Truncate content more aggressively for faster processing
        max_content = 800  # Reduced from 1500
        truncated_content = content[:max_content]
        if len(content) > max_content:
            truncated_content += "..."
        
        # Simplified schema - only essential fields
        schema = {
            "title": "Market question: Will [event] happen?",
            "category": "crypto|sports|politics|social|tech|business",
            "tags": ["tag1", "tag2"],
            "yes_prob": "0-1 number",
            "no_prob": "0-1 number",
            "resolution_date": "YYYY-MM-DD or null",
            "data_source": "API name"
        }
        
        # Build shorter article text
        article_text = f"{title}\n\n{truncated_content}"
        
        # Build NuExtract prompt
        prompt = self._build_nuextract_prompt(schema, article_text)
        
        # Extract data with shorter timeout
        output = self.extract(prompt)
        print(f"\n🔍 DEBUG - Raw AI output:\n{output}\n")
        
        # Parse JSON from output
        json_match = re.search(r'\{.*\}', output, re.DOTALL)
        if not json_match:
            print(f"❌ No JSON pattern found in output")
            raise ValueError("No JSON found in AI output")
        
        print(f"✅ JSON match found: {json_match.group()[:200]}...")
        raw_data = json.loads(json_match.group())
        
        # Normalize keys to lowercase for case-insensitive parsing
        data = {}
        for key, value in raw_data.items():
            normalized_key = key.lower().replace('_', '').replace('-', '')
            data[normalized_key] = value
        
        # Generate source ID from URL
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace('www.', '').split('.')[0]
        slug = parsed_url.path.strip('/').replace('/', '_')[:50]
        source_id = f"article_{domain}_{slug}" if slug else f"article_{domain}_untitled"
        
        # Extract title
        market_title = data.get("title") or data.get("markettitle") or title
        if not market_title.strip().endswith('?'):
            market_title = f"Will {market_title}?"
        
        # Get probabilities - try multiple key variations
        yes_prob = 0.5
        no_prob = 0.5
        
        for key in data.keys():
            if 'yesprob' in key or 'yesprobability' in key:
                try:
                    yes_prob = float(data[key]) if data[key] else 0.5
                except (ValueError, TypeError):
                    pass
            if 'noprob' in key or 'noprobability' in key:
                try:
                    no_prob = float(data[key]) if data[key] else 0.5
                except (ValueError, TypeError):
                    pass
        
        # Calculate no_change as remaining probability
        no_change_prob = max(0.0, 1.0 - yes_prob - no_prob)
        
        # Normalize to sum to 1.0
        total = yes_prob + no_change_prob + no_prob
        if total > 0:
            yes_prob /= total
            no_change_prob /= total
            no_prob /= total
        else:
            yes_prob, no_change_prob, no_prob = 0.4, 0.2, 0.4
        
        # Get data source
        data_source = data.get("datasource") or data.get("data_source") or "news_api"
        
        # Build resolution rules
        resolution_rules = {
            "provider": "oracle_v1",
            "data_source": data_source,
            "conditions": {
                "YES": f"Event confirmed via {data_source}",
                "NO": f"Event not confirmed via {data_source}"
            }
        }
        
        # Parse resolution date - try multiple formats
        resolution_date = None
        for key in data.keys():
            if 'resolutiondate' in key or 'resolution' in key:
                date_val = data[key]
                if date_val and date_val != "null" and isinstance(date_val, str):
                    # Handle various date formats
                    if len(date_val) == 10:  # YYYY-MM-DD
                        resolution_date = f"{date_val}T23:59:59Z"
                    elif 'T' in date_val:
                        resolution_date = date_val
                    else:
                        # Try to parse natural language dates (re already imported at top)
                        date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_val)
                        if date_match:
                            resolution_date = f"{date_match.group(0)}T23:59:59Z"
                break
        
        # Build category
        category = data.get("category", "").lower().strip()
        if not category or category not in ["crypto", "sports", "politics", "social", "tech", "business"]:
            # Detect from content
            text_lower = f"{title} {truncated_content}".lower()
            if any(word in text_lower for word in ["bitcoin", "crypto", "blockchain", "eth", "nft"]):
                category = "crypto"
            elif any(word in text_lower for word in ["world cup", "soccer", "football", "match", "tournament", "game"]):
                category = "sports"
            elif any(word in text_lower for word in ["election", "president", "congress", "senate", "vote"]):
                category = "politics"
            elif any(word in text_lower for word in ["twitter", "youtube", "tiktok", "followers", "views"]):
                category = "social"
            elif any(word in text_lower for word in ["startup", "funding", "ipo", "stock", "market cap"]):
                category = "business"
            else:
                category = "tech"
        
        # Get tags
        tags = data.get("tags", [])
        if not tags:
            tags = [category]
        
        # Map to BlockchainEvent and return
        return BlockchainEvent(
            source=source_id,
            title=market_title,
            description=f"Market based on: {truncated_content[:250]}",
            category=category,
            tags=tags[:5],  # Max 5 tags
            market_type="three_choice",
            outcomes=["Yes", "No Change", "No"],
            initial_probabilities=[round(yes_prob, 3), round(no_change_prob, 3), round(no_prob, 3)],
            source_url=url,
            image_url=None,
            dates={
                "published": datetime.now(timezone.utc).isoformat(),
                "freeze": resolution_date,
                "resolution": resolution_date
            },
            resolution_rules=resolution_rules
        )
    
    def analyze_article(self, title: str, content: str, url: str) -> PredictionEvent:
        """
        Legacy method for backward compatibility
        Use analyze_article_blockchain() for new blockchain format
        """
        # Truncate content to fit context
        max_content = 1500
        truncated_content = content[:max_content]
        if len(content) > max_content:
            truncated_content += "..."
        
        # Define extraction schema
        schema = {
            "prediction_question": "A clear prediction question in format: Will [X] happen by [date]?",
            "summary": "2-3 sentence summary of what the article is about",
            "category": "One of: tech, crypto, politics, sports, finance, automotive, ai, general",
            "tags": ["list", "of", "hashtags"],
            "key_people_or_companies": ["List", "of", "entities"],
            "confidence_level": "0.0 to 1.0 number indicating confidence",
            "resolution_date": "ISO date when prediction can be verified (YYYY-MM-DD)",
            "how_to_verify": "Specific criteria to determine if prediction came true",
            "outcome_options": ["Option 1", "Option 2", "Option 3"]
        }
        
        # Build article text
        article_text = f"Title: {title}\n\nContent: {truncated_content}\n\nURL: {url}"
        
        # Build NuExtract prompt
        prompt = self._build_nuextract_prompt(schema, article_text)
        
        # Extract data
        try:
            output = self.extract(prompt)
            
            # Parse JSON from output
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                # Map to PredictionEvent
                return PredictionEvent(
                    title=data.get("prediction_question", f"Will events in '{title[:50]}' occur?"),
                    description=data.get("summary", truncated_content[:200]),
                    category=data.get("category", "general"),
                    tags=data.get("tags", [])[:5],  # Max 5 tags
                    key_entities=data.get("key_people_or_companies", [])[:5],
                    confidence=float(data.get("confidence_level", 0.5)),
                    resolution_date=data.get("resolution_date", "2025-12-31"),
                    resolution_criteria=data.get("how_to_verify", "Based on mainstream news coverage"),
                    options=data.get("outcome_options", ["Yes", "No", "Uncertain"]),
                    source_url=url
                )
            else:
                # Fallback if no JSON found
                return self._fallback_event(title, content, url)
        
        except Exception as e:
            print(f"⚠️  Extraction failed: {e}")
            return self._fallback_event(title, content, url)
    
    def _fallback_blockchain_event(self, title: str, content: str, url: str) -> BlockchainEvent:
        """Create fallback blockchain event if extraction fails"""
        # Extract basic tags from content
        tags = self._extract_basic_tags(title, content)
        category = self._guess_category(title, content)
        
        # Generate source ID from URL
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace('www.', '').split('.')[0]
        slug = parsed_url.path.strip('/').replace('/', '_')[:50]
        source_id = f"article_{domain}_{slug}" if slug else f"article_{domain}_fallback"
        
        return BlockchainEvent(
            source=source_id,
            title=f"Will the events described in '{title[:60]}' occur as predicted?",
            description=f"Market based on article: {title}. {content[:200]}... Verified via mainstream news coverage within 6 months.",
            category=category,
            tags=tags,
            market_type="three_choice",
            outcomes=["Yes", "No Change", "No"],
            initial_probabilities=[0.40, 0.20, 0.40],  # Neutral odds
            source_url=url,
            image_url=None,
            dates={
                "published": datetime.now(timezone.utc).isoformat(),
                "freeze": None,
                "resolution": None
            },
            resolution_rules={
                "provider": "oracle_v1",
                "data_source": "news_verification",
                "conditions": {
                    "YES": "Events confirmed by 3+ major news sources",
                    "NO": "Events not confirmed or contradicted by news sources"
                }
            }
        )
    
    def _fallback_event(self, title: str, content: str, url: str) -> PredictionEvent:
        """Create fallback event if extraction fails"""
        # Extract basic tags from content
        tags = self._extract_basic_tags(title, content)
        category = self._guess_category(title, content)
        
        return PredictionEvent(
            title=f"Will the events described in '{title[:60]}' occur as predicted?",
            description=content[:250] + "...",
            category=category,
            tags=tags,
            key_entities=[],
            confidence=0.5,
            resolution_date="2025-12-31",
            resolution_criteria="Based on mainstream news coverage within 6 months",
            options=["Yes, events occur", "No, events don't occur", "Partially accurate"],
            source_url=url
        )
    
    def _extract_basic_tags(self, title: str, content: str) -> List[str]:
        """Extract basic tags from text"""
        text = f"{title} {content}".lower()
        
        tag_map = {
            "#crypto": ["bitcoin", "crypto", "blockchain", "ethereum", "btc"],
            "#ai": ["ai", "artificial intelligence", "gpt", "llm", "machine learning"],
            "#tesla": ["tesla", "elon musk", "electric vehicle"],
            "#tech": ["technology", "software", "startup", "app"],
            "#finance": ["stock", "market", "trading", "investment"],
            "#politics": ["politics", "election", "government", "president"],
            "#sports": ["sports", "game", "player", "team", "championship"],
        }
        
        tags = ["#news"]
        for tag, keywords in tag_map.items():
            if any(kw in text for kw in keywords):
                tags.append(tag)
                if len(tags) >= 5:
                    break
        
        return tags
    
    def _guess_category(self, title: str, content: str) -> str:
        """Guess category from content"""
        text = f"{title} {content}".lower()
        
        categories = {
            "crypto": ["bitcoin", "crypto", "blockchain", "ethereum"],
            "ai": ["ai", "artificial intelligence", "gpt", "llm"],
            "automotive": ["tesla", "car", "vehicle", "ev", "autonomous"],
            "tech": ["technology", "software", "startup", "app"],
            "finance": ["stock", "market", "trading", "bank"],
            "politics": ["politics", "election", "government"],
            "sports": ["sports", "game", "player", "team"],
        }
        
        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category
        
        return "general"


def create_nuextract_engine(model_name: str = "nuextract-smol-1.5") -> NuExtractEngine:
    """
    Create NuExtractEngine with default configuration
    
    Args:
        model_name: Model filename (without .gguf extension)
        
    Returns:
        Configured NuExtractEngine instance
    """
    # Determine project root and model path
    project_root = Path(__file__).parent.parent.parent
    model_path = project_root / "models" / f"{model_name}-q4_k_m.gguf"
    
    config = LlamaConfig(
        model_path=str(model_path),
        temperature=0.1,  # Low temperature for structured output
        max_tokens=1024,
    )
    
    return NuExtractEngine(config)


# Convenience function for quick testing
def test_extraction():
    """Test NuExtract with a sample article"""
    engine = create_nuextract_engine()
    
    test_title = "Tesla Gets California Approval for Full Self-Driving"
    test_content = """
    Tesla has received regulatory approval from the California DMV to test its
    Full Self-Driving (FSD) beta software on public roads. The approval marks
    a significant milestone for the company's autonomous driving ambitions.
    Elon Musk announced the news on Twitter, stating that FSD will begin
    rolling out to California customers in the coming weeks. The system
    uses cameras and neural networks to enable autonomous navigation.
    """
    test_url = "https://example.com/tesla-fsd-california"
    
    print("🧪 Testing NuExtract extraction...")
    result = engine.analyze_article(test_title, test_content, test_url)
    
    print("\n✅ Extraction Result:")
    print(f"Title: {result.title}")
    print(f"Category: {result.category}")
    print(f"Tags: {', '.join(result.tags)}")
    print(f"Entities: {', '.join(result.key_entities)}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Options: {', '.join(result.options)}")
    print(f"\nFull JSON:")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    test_extraction()
