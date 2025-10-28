use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use chrono::{DateTime, Utc, Duration};

/// Flexible event source configuration
/// Supports: HTML websites, RSS feeds, JSON APIs, or regex extraction
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EventSource {
    /// Unique identifier for this source
    pub id: String,
    
    /// Name of the event source (e.g., "UFC Events", "Stock Listings")
    pub name: String,
    
    /// URL to scrape
    pub url: String,
    
    /// Type of source: "html", "rss", "json", "text"
    pub source_type: SourceType,
    
    /// CSS selectors for HTML scraping
    #[serde(skip_serializing_if = "Option::is_none")]
    pub selectors: Option<HtmlSelectors>,
    
    /// Regex patterns for text/HTML extraction
    #[serde(skip_serializing_if = "Option::is_none")]
    pub regex_patterns: Option<HashMap<String, String>>,
    
    /// How often to refresh (in hours)
    pub refresh_interval_hours: u32,
    
    /// When this source was last scraped
    pub last_scraped: Option<DateTime<Utc>>,
    
    /// Whether this source is active
    pub is_active: bool,
    
    /// Category for markets created from this source
    pub category: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SourceType {
    Html,
    Rss,
    Json,
    Text,
}

/// CSS selectors for extracting data from HTML
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HtmlSelectors {
    /// Selector for event containers
    pub event_container: String,
    
    /// Selector for event title within container
    pub title: String,
    
    /// Selector for event description
    pub description: String,
    
    /// Selector for event date/time
    pub date: String,
    
    /// Optional: selector for options/outcomes
    pub options: Option<String>,
}

/// Raw scraped event data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScrapedEvent {
    pub title: String,
    pub description: String,
    pub date: String,
    pub source_id: String,
    pub category: String,
    pub url: Option<String>,
    pub raw_data: String,
}

/// Market generated from scraped event
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GeneratedMarketFromEvent {
    pub title: String,
    pub description: String,
    pub options: Vec<String>,
    pub category: String,
    pub source_event_id: String,
}

/// Event scraper - handles all scraping logic
#[derive(Debug)]
pub struct EventScraper {
    client: reqwest::Client,
    sources: HashMap<String, EventSource>,
}

impl EventScraper {
    pub fn new() -> Self {
        Self {
            client: reqwest::Client::new(),
            sources: HashMap::new(),
        }
    }

    /// Add an event source
    pub fn add_source(&mut self, source: EventSource) -> Result<(), String> {
        if self.sources.contains_key(&source.id) {
            return Err("Source already exists".to_string());
        }
        self.sources.insert(source.id.clone(), source);
        Ok(())
    }

    /// Remove an event source
    pub fn remove_source(&mut self, source_id: &str) -> Result<(), String> {
        if self.sources.remove(source_id).is_none() {
            return Err("Source not found".to_string());
        }
        Ok(())
    }

    /// Get all sources
    pub fn get_sources(&self) -> Vec<&EventSource> {
        self.sources.values().collect()
    }

    /// Get active sources that need refreshing
    pub fn get_sources_to_refresh(&self) -> Vec<&EventSource> {
        self.sources
            .values()
            .filter(|s| s.is_active && self.should_refresh(s))
            .collect()
    }

    /// Check if a source needs refreshing
    fn should_refresh(&self, source: &EventSource) -> bool {
        match source.last_scraped {
            None => true,
            Some(last) => {
                let now = Utc::now();
                let elapsed = now.signed_duration_since(last);
                let interval = Duration::hours(source.refresh_interval_hours as i64);
                elapsed >= interval
            }
        }
    }

    /// Scrape a single source
    pub async fn scrape_source(&mut self, source_id: &str) -> Result<Vec<ScrapedEvent>, String> {
        let source = self.sources
            .get(source_id)
            .ok_or("Source not found".to_string())?
            .clone();

        let events = match source.source_type {
            SourceType::Html => self.scrape_html(&source).await?,
            SourceType::Rss => self.scrape_rss(&source).await?,
            SourceType::Json => self.scrape_json(&source).await?,
            SourceType::Text => self.scrape_text(&source).await?,
        };

        // Update last_scraped timestamp
        if let Some(source_mut) = self.sources.get_mut(source_id) {
            source_mut.last_scraped = Some(Utc::now());
        }

        Ok(events)
    }

    /// Scrape HTML website
    async fn scrape_html(&self, source: &EventSource) -> Result<Vec<ScrapedEvent>, String> {
        let response = self.client
            .get(&source.url)
            .send()
            .await
            .map_err(|e| format!("Failed to fetch {}: {}", source.url, e))?;

        let html = response
            .text()
            .await
            .map_err(|e| format!("Failed to read response: {}", e))?;

        let selectors = source.selectors.as_ref()
            .ok_or("No selectors configured for HTML scraping")?;

        self.extract_html_events(&html, source, selectors)
    }

    /// Extract events from HTML using CSS selectors
    fn extract_html_events(
        &self,
        html: &str,
        source: &EventSource,
        selectors: &HtmlSelectors,
    ) -> Result<Vec<ScrapedEvent>, String> {
        use scraper::{Html, Selector};

        let document = Html::parse_document(html);
        let container_selector = Selector::parse(&selectors.event_container)
            .map_err(|_| "Invalid container selector")?;
        let title_selector = Selector::parse(&selectors.title)
            .map_err(|_| "Invalid title selector")?;
        let desc_selector = Selector::parse(&selectors.description)
            .map_err(|_| "Invalid description selector")?;
        let date_selector = Selector::parse(&selectors.date)
            .map_err(|_| "Invalid date selector")?;

        let mut events = Vec::new();

        for container in document.select(&container_selector) {
            let title = container
                .select(&title_selector)
                .next()
                .and_then(|e| e.text().next())
                .unwrap_or("Unknown")
                .to_string();

            let description = container
                .select(&desc_selector)
                .next()
                .and_then(|e| e.text().next())
                .unwrap_or("No description")
                .to_string();

            let date = container
                .select(&date_selector)
                .next()
                .and_then(|e| e.text().next())
                .unwrap_or("Unknown date")
                .to_string();

            events.push(ScrapedEvent {
                title,
                description,
                date,
                source_id: source.id.clone(),
                category: source.category.clone(),
                url: Some(source.url.clone()),
                raw_data: String::new(),
            });
        }

        Ok(events)
    }

    /// Scrape RSS feed
    async fn scrape_rss(&self, source: &EventSource) -> Result<Vec<ScrapedEvent>, String> {
        let response = self.client
            .get(&source.url)
            .send()
            .await
            .map_err(|e| format!("Failed to fetch RSS: {}", e))?;

        let xml = response
            .text()
            .await
            .map_err(|e| format!("Failed to read RSS: {}", e))?;

        // Simple RSS parsing (in production, use rss crate)
        self.extract_rss_events(&xml, source)
    }

    /// Extract events from RSS feed
    fn extract_rss_events(
        &self,
        xml: &str,
        source: &EventSource,
    ) -> Result<Vec<ScrapedEvent>, String> {
        let mut events = Vec::new();

        // Simple regex-based RSS parsing
        // For production, use the `rss` crate
        for item_match in regex::Regex::new(r"<item>(.*?)</item>")
            .unwrap()
            .captures_iter(xml)
        {
            let item = &item_match[1];

            let title = regex::Regex::new(r"<title>(.*?)</title>")
                .unwrap()
                .captures(item)
                .and_then(|c| c.get(1))
                .map(|m| m.as_str().to_string())
                .unwrap_or_default();

            let description = regex::Regex::new(r"<description>(.*?)</description>")
                .unwrap()
                .captures(item)
                .and_then(|c| c.get(1))
                .map(|m| m.as_str().to_string())
                .unwrap_or_default();

            let date = regex::Regex::new(r"<pubDate>(.*?)</pubDate>")
                .unwrap()
                .captures(item)
                .and_then(|c| c.get(1))
                .map(|m| m.as_str().to_string())
                .unwrap_or_default();

            events.push(ScrapedEvent {
                title,
                description,
                date,
                source_id: source.id.clone(),
                category: source.category.clone(),
                url: Some(source.url.clone()),
                raw_data: item.to_string(),
            });
        }

        Ok(events)
    }

    /// Scrape JSON API
    async fn scrape_json(&self, source: &EventSource) -> Result<Vec<ScrapedEvent>, String> {
        let response = self.client
            .get(&source.url)
            .send()
            .await
            .map_err(|e| format!("Failed to fetch JSON: {}", e))?;

        let json: serde_json::Value = response
            .json()
            .await
            .map_err(|e| format!("Failed to parse JSON: {}", e))?;

        let mut events = Vec::new();

        // Handle array of events
        if let Some(array) = json.as_array() {
            for item in array {
                events.push(ScrapedEvent {
                    title: item.get("title")
                        .and_then(|v| v.as_str())
                        .unwrap_or("Unknown")
                        .to_string(),
                    description: item.get("description")
                        .and_then(|v| v.as_str())
                        .unwrap_or("No description")
                        .to_string(),
                    date: item.get("date")
                        .and_then(|v| v.as_str())
                        .unwrap_or("Unknown")
                        .to_string(),
                    source_id: source.id.clone(),
                    category: source.category.clone(),
                    url: Some(source.url.clone()),
                    raw_data: item.to_string(),
                });
            }
        }

        Ok(events)
    }

    /// Scrape plain text (using regex patterns)
    async fn scrape_text(&self, source: &EventSource) -> Result<Vec<ScrapedEvent>, String> {
        let response = self.client
            .get(&source.url)
            .send()
            .await
            .map_err(|e| format!("Failed to fetch text: {}", e))?;

        let text = response
            .text()
            .await
            .map_err(|e| format!("Failed to read response: {}", e))?;

        let patterns = source.regex_patterns.as_ref()
            .ok_or("No regex patterns configured")?;

        let mut events = Vec::new();

        // Apply regex patterns to extract events
        if let Some(title_pattern) = patterns.get("title") {
            if let Ok(re) = regex::Regex::new(title_pattern) {
                for cap in re.captures_iter(&text) {
                    events.push(ScrapedEvent {
                        title: cap.get(1)
                            .map(|m| m.as_str().to_string())
                            .unwrap_or_default(),
                        description: patterns.get("description")
                            .and_then(|p| regex::Regex::new(p).ok())
                            .and_then(|re| re.captures(&text))
                            .and_then(|c| c.get(1))
                            .map(|m| m.as_str().to_string())
                            .unwrap_or_default(),
                        date: patterns.get("date")
                            .and_then(|p| regex::Regex::new(p).ok())
                            .and_then(|re| re.captures(&text))
                            .and_then(|c| c.get(1))
                            .map(|m| m.as_str().to_string())
                            .unwrap_or_default(),
                        source_id: source.id.clone(),
                        category: source.category.clone(),
                        url: Some(source.url.clone()),
                        raw_data: text.clone(),
                    });
                }
            }
        }

        Ok(events)
    }

    /// Convert scraped event to betting market
    pub fn event_to_market(&self, event: &ScrapedEvent) -> GeneratedMarketFromEvent {
        GeneratedMarketFromEvent {
            title: event.title.clone(),
            description: format!(
                "{}\n\nSource: {}\nDate: {}",
                event.description, event.source_id, event.date
            ),
            options: vec!["Yes".to_string(), "No".to_string()],
            category: event.category.clone(),
            source_event_id: format!("{}_{}", event.source_id, event.title),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_event_scraper_creation() {
        let scraper = EventScraper::new();
        assert_eq!(scraper.get_sources().len(), 0);
    }

    #[test]
    fn test_add_event_source() {
        let mut scraper = EventScraper::new();
        let source = EventSource {
            id: "ufc".to_string(),
            name: "UFC Events".to_string(),
            url: "https://www.ufc.com".to_string(),
            source_type: SourceType::Html,
            selectors: Some(HtmlSelectors {
                event_container: ".event-item".to_string(),
                title: ".title".to_string(),
                description: ".description".to_string(),
                date: ".date".to_string(),
                options: None,
            }),
            regex_patterns: None,
            refresh_interval_hours: 24,
            last_scraped: None,
            is_active: true,
            category: "sports".to_string(),
        };

        scraper.add_source(source).unwrap();
        assert_eq!(scraper.get_sources().len(), 1);
    }
}
