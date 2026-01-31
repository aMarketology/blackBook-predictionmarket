"""
ObjectWire Gemma 2 Integration
Local AI content generation using Gemma 2 via Ollama
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

import requests
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)

@dataclass
class GemmaResponse:
    """Response from Gemma 2 model"""
    content: str
    model: str
    created_at: datetime
    tokens_used: int
    processing_time: float

class GemmaEngine:
    """
    Local Gemma 2 AI engine for World Cup content generation
    Uses Ollama for offline AI capabilities
    """
    
    def __init__(self, model_name: str = "gemma2", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        
    def is_available(self) -> bool:
        """Check if Ollama service and Gemma 2 are available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(model["name"].startswith(self.model_name) for model in models)
            return False
        except Exception as e:
            logger.warning(f"Ollama service not available: {e}")
            return False
    
    def generate_content(self, prompt: str, system_prompt: str = None, 
                        temperature: float = 0.7, max_tokens: int = 1000) -> GemmaResponse:
        """Generate content using Gemma 2"""
        start_time = datetime.now()
        
        # Build the full prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nHuman: {prompt}\n\nAssistant:"
        
        payload = {
            "model": self.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "stop": ["Human:", "System:"]
            }
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return GemmaResponse(
                content=result.get("response", "").strip(),
                model=self.model_name,
                created_at=datetime.now(),
                tokens_used=result.get("eval_count", 0),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Gemma generation failed: {e}")
            raise RuntimeError(f"Failed to generate content: {e}")

class WorldCupGemmaWriter:
    """
    Specialized World Cup content writer using Gemma 2
    Offline AI for ObjectWire journalism
    """
    
    def __init__(self):
        self.gemma = GemmaEngine()
        self.system_prompt = """You are a professional sports journalist writing for ObjectWire, 
        a premium investigative journalism platform. Write engaging, accurate, and well-researched 
        articles about World Cup 2026. Focus on facts, analysis, and compelling storytelling. 
        Use a professional tone suitable for serious journalism."""
    
    def generate_breaking_news(self, news_event: str, context: str = "") -> str:
        """Generate breaking news article"""
        prompt = f"""
        Write a breaking news article about this World Cup event:
        {news_event}
        
        Additional context: {context}
        
        Requirements:
        - Lead with the most important facts
        - Include relevant background information
        - Keep it under 400 words
        - Use AP style journalism
        - Include potential impact on tournament
        """
        
        try:
            response = self.gemma.generate_content(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.6,
                max_tokens=600
            )
            return response.content
        except Exception as e:
            return f"Error generating content: {e}"
    
    def generate_match_analysis(self, team1: str, team2: str, 
                              match_data: Dict[str, Any]) -> str:
        """Generate post-match analysis"""
        prompt = f"""
        Write a detailed match analysis for:
        {team1} vs {team2}
        
        Match data: {json.dumps(match_data, indent=2)}
        
        Requirements:
        - Analyze key moments and turning points
        - Discuss tactical decisions
        - Player performances and standouts
        - Impact on World Cup progression
        - 600-800 words
        - Professional sports journalism style
        """
        
        try:
            response = self.gemma.generate_content(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.7,
                max_tokens=1200
            )
            return response.content
        except Exception as e:
            return f"Error generating analysis: {e}"
    
    def generate_transfer_rumor(self, player: str, current_club: str, 
                              target_club: str, details: str) -> str:
        """Generate transfer rumor article"""
        prompt = f"""
        Write an investigative article about this transfer rumor:
        
        Player: {player}
        Current Club: {current_club}
        Target Club: {target_club}
        Details: {details}
        
        Requirements:
        - Investigative journalism approach
        - Cite sources (use "sources close to the situation" format)
        - Include potential transfer fee and contract details
        - Analyze impact on both clubs
        - 400-500 words
        - Maintain journalistic skepticism
        """
        
        try:
            response = self.gemma.generate_content(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.5,
                max_tokens=800
            )
            return response.content
        except Exception as e:
            return f"Error generating transfer article: {e}"
    
    def generate_tournament_preview(self, tournament_phase: str, 
                                  teams: List[str], key_storylines: str) -> str:
        """Generate tournament phase preview"""
        prompt = f"""
        Write a comprehensive preview for the {tournament_phase} phase of World Cup 2026:
        
        Teams involved: {', '.join(teams)}
        Key storylines: {key_storylines}
        
        Requirements:
        - Preview each team's chances
        - Highlight key players to watch
        - Discuss tactical matchups
        - Predict potential outcomes
        - Include historical context
        - 800-1000 words
        - Engaging but analytical tone
        """
        
        try:
            response = self.gemma.generate_content(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.8,
                max_tokens=1500
            )
            return response.content
        except Exception as e:
            return f"Error generating preview: {e}"
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Gemma 2 connection and capabilities"""
        if not self.gemma.is_available():
            return {
                "status": "error",
                "message": "Gemma 2 model not available. Run 'ollama pull gemma2' first."
            }
        
        try:
            test_prompt = "Write a one-sentence summary of the FIFA World Cup 2026."
            response = self.gemma.generate_content(
                prompt=test_prompt,
                temperature=0.5,
                max_tokens=100
            )
            
            return {
                "status": "success",
                "message": "Gemma 2 is ready for World Cup content generation!",
                "model": response.model,
                "test_output": response.content,
                "processing_time": response.processing_time,
                "tokens_used": response.tokens_used
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Gemma 2 test failed: {e}"
            }

# CLI integration functions
def setup_gemma():
    """Setup instructions for Gemma 2"""
    console.print("\n[bold orange3]Setting up Gemma 2 for ObjectWire[/]")
    console.print("─" * 50)
    console.print("1. Install Ollama: [dim]brew install ollama[/]")
    console.print("2. Start service: [dim]brew services start ollama[/]")
    console.print("3. Pull Gemma 2: [dim]ollama pull gemma2[/]")
    console.print("4. Test connection: [dim]objectwire gemma test[/]")

def main():
    """Test the Gemma engine"""
    writer = WorldCupGemmaWriter()
    
    console.print("[bold orange3]Testing ObjectWire Gemma 2 Integration[/]")
    console.print("─" * 50)
    
    # Test connection
    test_result = writer.test_connection()
    
    if test_result["status"] == "success":
        console.print(f"✅ [green]{test_result['message']}[/]")
        console.print(f"Model: [dim]{test_result['model']}[/]")
        console.print(f"Processing time: [dim]{test_result['processing_time']:.2f}s[/]")
        console.print(f"Test output: [italic]{test_result['test_output']}[/]")
    else:
        console.print(f"❌ [red]{test_result['message']}[/]")
        setup_gemma()

if __name__ == "__main__":
    main()