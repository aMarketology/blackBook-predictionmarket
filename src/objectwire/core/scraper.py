"""
ObjectWire Scraper Module
=========================
Web scraping engine for extracting content from URLs.

Features:
- Retry logic with exponential backoff
- Browser-like headers to avoid blocks
- Content validation
- Batch processing
- Error handling
"""

import time
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from dataclasses import dataclass
from datetime import datetime

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ScrapedContent:
    """Scraped content from a URL."""
    url: str
    title: str
    content: str
    domain: str
    scraped_at: datetime
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Scraper:
    """Web scraping engine with retry logic and validation."""
    
    # Browser-like headers to avoid 403 blocks
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.109 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
    }
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        max_content_length: int = 5000,
        min_content_length: int = 100
    ):
        """Initialize scraper.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            max_content_length: Maximum content length to extract
            min_content_length: Minimum content length for validity
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_content_length = max_content_length
        self.min_content_length = min_content_length
        self.session = requests.Session()
    
    def scrape_url(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None
    ) -> ScrapedContent:
        """Scrape content from a single URL.
        
        Args:
            url: URL to scrape
            headers: Custom headers (optional)
            
        Returns:
            ScrapedContent object with scraped data
        """
        start_time = time.time()
        domain = urlparse(url).netloc
        
        logger.info(f"Scraping URL: {url}")
        
        # Use custom headers or defaults
        request_headers = headers or self.DEFAULT_HEADERS
        
        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Attempt {attempt + 1}/{self.max_retries}")
                
                response = self.session.get(
                    url,
                    headers=request_headers,
                    timeout=self.timeout,
                    allow_redirects=True
                )
                
                response.raise_for_status()
                logger.info(f"Successfully fetched URL: {url} (status {response.status_code})")
                
                # Parse HTML
                soup = BeautifulSoup(response.content, "html.parser")
                
                # Remove noise
                for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    tag.decompose()
                
                # Extract title
                title = soup.title.get_text(strip=True) if soup.title else "Untitled"
                
                # Extract main content
                main = soup.find('article') or soup.find('main') or soup.body
                content = main.get_text("\n", strip=True)[:self.max_content_length] if main else ""
                
                # Validate content
                if not self.validate_content(content):
                    error_msg = f"Content too short ({len(content)} chars)"
                    logger.warning(error_msg)
                    return ScrapedContent(
                        url=url,
                        title=title,
                        content=content,
                        domain=domain,
                        scraped_at=datetime.utcnow(),
                        success=False,
                        error=error_msg
                    )
                
                # Calculate processing time
                processing_time = int((time.time() - start_time) * 1000)
                
                logger.info(f"Successfully scraped {url} ({processing_time}ms)")
                
                return ScrapedContent(
                    url=url,
                    title=title,
                    content=content,
                    domain=domain,
                    scraped_at=datetime.utcnow(),
                    success=True,
                    metadata={
                        'processing_time_ms': processing_time,
                        'content_length': len(content),
                        'status_code': response.status_code
                    }
                )
                
            except requests.exceptions.HTTPError as e:
                last_error = f"HTTP error: {e}"
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                
            except requests.exceptions.RequestException as e:
                last_error = f"Request error: {e}"
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
            
            except Exception as e:
                last_error = f"Unexpected error: {e}"
                logger.error(f"Attempt {attempt + 1} failed: {last_error}")
            
            # Exponential backoff
            if attempt < self.max_retries - 1:
                backoff_time = 2 ** attempt
                logger.debug(f"Waiting {backoff_time}s before retry...")
                time.sleep(backoff_time)
        
        # All retries failed
        logger.error(f"Failed to scrape {url} after {self.max_retries} attempts")
        return ScrapedContent(
            url=url,
            title="",
            content="",
            domain=domain,
            scraped_at=datetime.utcnow(),
            success=False,
            error=last_error
        )
    
    def scrape_batch(
        self,
        urls: List[str],
        parallel: bool = False,
        max_workers: int = 5
    ) -> List[ScrapedContent]:
        """Scrape multiple URLs.
        
        Args:
            urls: List of URLs to scrape
            parallel: Whether to scrape in parallel (not yet implemented)
            max_workers: Number of parallel workers (not yet implemented)
            
        Returns:
            List of ScrapedContent objects
        """
        logger.info(f"Batch scraping {len(urls)} URLs")
        
        results = []
        for i, url in enumerate(urls, 1):
            logger.info(f"Scraping {i}/{len(urls)}: {url}")
            result = self.scrape_url(url)
            results.append(result)
            
            # Small delay to be respectful
            if i < len(urls):
                time.sleep(0.5)
        
        successful = sum(1 for r in results if r.success)
        logger.info(f"Batch complete: {successful}/{len(urls)} successful")
        
        return results
    
    def validate_content(self, content: str) -> bool:
        """Validate scraped content.
        
        Args:
            content: Content to validate
            
        Returns:
            True if content is valid
        """
        if not content:
            return False
        
        if len(content) < self.min_content_length:
            return False
        
        # Check if content is mostly whitespace
        if len(content.strip()) < self.min_content_length:
            return False
        
        return True
    
    def get_domain(self, url: str) -> str:
        """Extract domain from URL.
        
        Args:
            url: URL to parse
            
        Returns:
            Domain name
        """
        return urlparse(url).netloc


# Singleton instance
_scraper_instance: Optional[Scraper] = None

def get_scraper(**kwargs) -> Scraper:
    """Get or create scraper instance.
    
    Args:
        **kwargs: Arguments for Scraper initialization
        
    Returns:
        Scraper instance
    """
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = Scraper(**kwargs)
    return _scraper_instance
