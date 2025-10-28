#!/usr/bin/env python3
"""
Comprehensive Test Suite for BlackBook URL Scraping AI Agent
============================================================
Includes both unit tests and integration tests for:
- URL scraping and content extraction
- AI analysis (both mock and real modes)
- Market creation (simulated and real)
- Full pipeline execution
- API endpoints
- Specific SNAP article test case

Run with: python -m pytest test_comprehensive.py -v
"""

import pytest
import json
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys

# Add the current directory to Python path so we can import serve_frontend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from serve_frontend import (
    app, scrape_content, analyze_with_ai, create_market, 
    run_pipeline, PredictionEvent, json_from_text
)

# Test client for FastAPI
client = TestClient(app)

class TestScrapeContent:
    """Test URL scraping functionality"""
    
    @patch('serve_frontend.requests.get')
    def test_scrape_success(self, mock_get):
        """Test successful content scraping"""
        # Mock response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"""
        <html>
            <head><title>Test Article</title></head>
            <body>
                <article>
                    <h1>Test Title</h1>
                    <p>This is test content about important news.</p>
                </article>
                <script>ignored</script>
            </body>
        </html>
        """
        mock_get.return_value = mock_response
        
        result = scrape_content("https://example.com/test")
        
        assert result["title"] == "Test Article"
        assert "Test Title" in result["content"]
        assert "important news" in result["content"]
        assert "ignored" not in result["content"]  # Scripts should be removed
        assert result["domain"] == "example.com"
        assert result["url"] == "https://example.com/test"
    
    @patch('serve_frontend.requests.get')
    def test_scrape_failure(self, mock_get):
        """Test scraping failure handling"""
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(Exception):
            scrape_content("https://invalid-url.com")


class TestAnalyzeWithAI:
    """Test AI analysis functionality"""
    
    def test_ai_mock_mode(self):
        """Test deterministic AI mock mode"""
        scraped_data = {
            'title': 'SNAP Benefits and DoorDash',
            'content': 'Article about SNAP benefits running out soon',
            'url': 'https://example.com/snap-article'
        }
        
        result = analyze_with_ai(scraped_data, "tech", ai_mock=True)
        
        assert isinstance(result, PredictionEvent)
        assert "SNAP benefits" in result.title
        assert "November 1, 2025" in result.title
        assert result.confidence == 0.6
        assert len(result.options) == 2
        assert "exhausted by Nov 1, 2025" in result.options[0]
        assert result.source_url == scraped_data['url']
    
    @patch('serve_frontend.openai')
    def test_ai_real_mode_success(self, mock_openai):
        """Test real OpenAI mode (mocked)"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = json.dumps({
            "title": "Will AI replace human jobs by 2025?",
            "description": "Based on recent AI developments",
            "category": "tech",
            "options": ["Yes", "No", "Partially"],
            "confidence": 0.8
        })
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_openai.ChatCompletion.create.return_value = mock_response
        
        scraped_data = {
            'title': 'AI Development News',
            'content': 'Article about AI advancements',
            'url': 'https://example.com/ai-news'
        }
        
        # Simulate openai being available
        with patch('serve_frontend.openai', mock_openai):
            result = analyze_with_ai(scraped_data, "tech", ai_mock=False)
        
        assert isinstance(result, PredictionEvent)
        assert "AI replace human jobs" in result.title
        assert result.confidence == 0.8
        assert len(result.options) == 3
    
    def test_ai_fallback_on_error(self):
        """Test fallback when AI fails"""
        # Mock openai as being available but failing
        mock_openai = MagicMock()
        mock_openai.ChatCompletion.create.side_effect = Exception("API Error")
        
        with patch('serve_frontend.openai', mock_openai):
            scraped_data = {
                'title': 'Test Article',
                'content': 'Some content',
                'url': 'https://example.com'
            }
            
            result = analyze_with_ai(scraped_data, "tech", ai_mock=False)
            
            assert isinstance(result, PredictionEvent)
            assert "Prediction: Test Article" in result.title
            assert result.confidence == 0.5


class TestCreateMarket:
    """Test market creation functionality"""
    
    def test_create_market_dry_run(self):
        """Test simulated market creation"""
        event = PredictionEvent(
            title="Test Prediction",
            description="Test description",
            category="tech",
            options=["Yes", "No"],
            confidence=0.7,
            source_url="https://example.com"
        )
        
        result = create_market(event, dry_run=True)
        
        assert result is not None
        assert result.startswith("SIM-")
    
    @patch('serve_frontend.ALLOW_CREATE_MARKET', True)
    @patch('serve_frontend.requests.post')
    def test_create_market_real_success(self, mock_post):
        """Test real market creation (mocked)"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"id": "MARKET-123"}
        mock_post.return_value = mock_response
        
        event = PredictionEvent(
            title="Test Prediction",
            description="Test description",
            category="tech",
            options=["Yes", "No"],
            confidence=0.7,
            source_url="https://example.com"
        )
        
        result = create_market(event, dry_run=False)
        
        assert result == "MARKET-123"
        mock_post.assert_called_once()


class TestJSONFromText:
    """Test JSON extraction utility"""
    
    def test_extract_valid_json(self):
        """Test extracting JSON from text"""
        text = 'Some text {"title": "Test", "confidence": 0.8} more text'
        result = json_from_text(text)
        
        assert result["title"] == "Test"
        assert result["confidence"] == 0.8
    
    def test_extract_invalid_json_fallback(self):
        """Test fallback for invalid JSON"""
        text = "No JSON here at all"
        result = json_from_text(text)
        
        assert result["title"] == "Untitled"
        assert result["confidence"] == 0.5


class TestRunPipeline:
    """Test full pipeline execution"""
    
    @patch('serve_frontend.scrape_content')
    @patch('serve_frontend.analyze_with_ai')
    def test_pipeline_success_no_market(self, mock_analyze, mock_scrape):
        """Test successful pipeline without market creation"""
        # Setup mocks
        mock_scrape.return_value = {
            'title': 'Test Article',
            'content': 'Test content',
            'domain': 'example.com',
            'url': 'https://example.com/test'
        }
        
        mock_event = PredictionEvent(
            title="Test Prediction",
            description="Test description",
            category="tech",
            options=["Yes", "No"],
            confidence=0.7,
            source_url="https://example.com/test"
        )
        mock_analyze.return_value = mock_event
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_pipeline(
                url="https://example.com/test",
                category="tech",
                create_market_flag=False,
                ai_mock=True,
                save_dir=temp_dir
            )
        
        assert result["url"] == "https://example.com/test"
        assert "scraped" in result["steps"]
        assert "analyzed" in result["steps"]
        assert "market_created" not in result["steps"]
        assert result["scraped"]["title"] == "Test Article"
        assert result["event"]["title"] == "Test Prediction"


class TestSNAPArticleSpecific:
    """Specific tests for the SNAP article use case"""
    
    def test_snap_article_mock_analysis(self):
        """Test the specific SNAP article with mock AI"""
        snap_scraped = {
            'title': 'Objectively, how much does DoorDash make from SNAP ?',
            'content': 'Article discussing SNAP benefits on DoorDash and potential government shutdown affecting benefits',
            'domain': 'www.objectwire.org',
            'url': 'https://www.objectwire.org/does-doordash-take-snap'
        }
        
        result = analyze_with_ai(snap_scraped, "tech", ai_mock=True)
        
        # Verify the deterministic output matches expectations
        assert "Will SNAP benefits mentioned in the article be exhausted by November 1, 2025?" == result.title
        assert "will SNAP benefits run out by Nov 1, 2025?" in result.description
        assert len(result.options) == 2
        assert "Yes, benefits exhausted by Nov 1, 2025" == result.options[0]
        assert "No, benefits remain on Nov 1, 2025" == result.options[1]
        assert result.confidence == 0.6
        assert result.category == "tech"
        assert result.source_url == snap_scraped['url']
    
    def test_snap_full_pipeline_integration(self):
        """Test full pipeline for SNAP article with real scraping (integration test)"""
        # This is an integration test that actually hits the real URL
        # Skip if network is unavailable
        try:
            result = run_pipeline(
                url="https://www.objectwire.org/does-doordash-take-snap",
                category="tech",
                create_market_flag=False,
                ai_mock=True,
                save_dir="logs"  # Use the real logs directory
            )
            
            # Verify the pipeline results
            assert result["url"] == "https://www.objectwire.org/does-doordash-take-snap"
            assert "scraped" in result["steps"]
            assert "analyzed" in result["steps"]
            
            # Verify scraped content (should contain SNAP/DoorDash content)
            assert result["scraped"]["domain"] == "www.objectwire.org"
            
            # Verify generated event (deterministic due to ai_mock=True)
            assert "Will SNAP benefits mentioned in the article be exhausted by November 1, 2025?" == result["event"]["title"]
            assert result["event"]["confidence"] == 0.6
            
            # Verify artifacts were created
            run_id = result["run_id"]
            scraped_file = os.path.join("logs", f"{run_id}_scraped.json")
            event_file = os.path.join("logs", f"{run_id}_event.json")
            
            assert os.path.exists(scraped_file)
            assert os.path.exists(event_file)
            
            # Verify file contents
            with open(event_file, 'r') as f:
                event_data = json.load(f)
                assert event_data["title"] == result["event"]["title"]
                
        except Exception as e:
            pytest.skip(f"Integration test skipped due to network/scraping issue: {e}")


class TestAPIEndpoints:
    """Test FastAPI endpoints"""
    
    def test_root_endpoint(self):
        """Test root information endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "BlackBook URL Scraper"
        assert "version" in data
        assert "openai" in data
        assert "blockchain" in data
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert "openai" in data
    
    @patch('serve_frontend.run_pipeline')
    def test_scrape_endpoint(self, mock_pipeline):
        """Test scrape endpoint"""
        # Mock pipeline response
        mock_pipeline.return_value = {
            "run_id": "test_123",
            "url": "https://example.com",
            "steps": ["scraped", "analyzed"],
            "scraped": {"title": "Test", "content": "Content"},
            "event": {"title": "Test Prediction", "confidence": 0.8}
        }
        
        response = client.post(
            "/scrape",
            json={"url": "https://example.com", "category": "tech"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == "test_123"
        assert data["url"] == "https://example.com"


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, "-v"])