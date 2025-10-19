use serde::{Deserialize, Serialize};
use reqwest;
use chrono::{DateTime, Utc};
use crate::blockchain::{Market, PredictionMarketBlockchain};
use feed_rs::parser;
// Removed unused import

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TechEvent {
    pub id: String,
    pub title: String,
    pub description: String,
    pub event_type: EventType,
    pub start_date: DateTime<Utc>,
    pub end_date: Option<DateTime<Utc>>,
    pub source: String,
    pub confidence_score: f64,
    pub tags: Vec<String>,
    pub related_companies: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum EventType {
    ProductLaunch,
    EarningsAnnouncement,
    Conference,
    IPO,
    Acquisition,
    Regulation,
    Partnership,
    TechBreakthrough,
    MarketMovement, // For live crypto price betting
}

pub struct EventDataProvider {
    newsapi_key: Option<String>,
    alphavantage_key: Option<String>,
    max_events: usize,
}

#[derive(Debug, Clone)]
struct EventScore {
    event: TechEvent,
    importance_score: f64,
}

impl EventDataProvider {
    pub fn new() -> Self {
        Self {
            newsapi_key: std::env::var("NEWSAPI_KEY").ok(),
            alphavantage_key: std::env::var("ALPHAVANTAGE_KEY").ok(),
            max_events: 100, // Maximum 100 events to keep it focused
        }
    }

    // Fetch upcoming tech events from multiple sources (TOP 100 ONLY)
    pub async fn fetch_upcoming_events(&self) -> Result<Vec<TechEvent>, Box<dyn std::error::Error>> {
        let mut all_events = Vec::new();

        // 1. Fetch from Google News RSS - Tech & Business (NO API KEY REQUIRED!)
        all_events.extend(fetch_google_news_tech_business().await?);

        // Add live crypto events (BTC/SOL price predictions every 15 minutes)
        all_events.extend(get_live_crypto_events());

        // Add known upcoming events
        all_events.extend(get_known_upcoming_events());

        // 4. Fetch from NewsAPI (if API key available)
        if let Some(ref api_key) = self.newsapi_key {
            all_events.extend(fetch_newsapi_events(api_key).await?);
        }

        // Score all events by importance and return top 100
        let scored_events = score_events_by_importance(all_events);
        let top_events: Vec<TechEvent> = scored_events
            .into_iter()
            .take(self.max_events)
            .map(|scored| scored.event)
            .collect();

        Ok(top_events)
    }
}

// Google News RSS for Tech and Business (Free, No API Key)
pub async fn fetch_google_news_tech_business() -> Result<Vec<TechEvent>, Box<dyn std::error::Error>> {
        let mut events = Vec::new();

        // Google News RSS URLs for different tech/business topics
        let rss_feeds = vec![
            // Tech Companies
            ("https://news.google.com/rss/search?q=Apple+OR+Google+OR+Microsoft+OR+Amazon+OR+Meta+OR+Tesla+OR+NVIDIA+when:7d&hl=en-US&gl=US&ceid=US:en", "Tech Giants"),
            
            // Business & Finance
            ("https://news.google.com/rss/search?q=IPO+OR+earnings+OR+acquisition+OR+merger+when:7d&hl=en-US&gl=US&ceid=US:en", "Business Events"),
            
            // AI & Technology
            ("https://news.google.com/rss/search?q=artificial+intelligence+OR+AI+OR+machine+learning+OR+ChatGPT+OR+OpenAI+when:7d&hl=en-US&gl=US&ceid=US:en", "AI News"),
            
            // Cryptocurrency
            ("https://news.google.com/rss/search?q=Bitcoin+OR+cryptocurrency+OR+crypto+OR+blockchain+when:7d&hl=en-US&gl=US&ceid=US:en", "Crypto News"),
            
            // Product Launches
            ("https://news.google.com/rss/search?q=\"will+launch\"+OR+\"announces\"+OR+\"plans+to+release\"+OR+\"coming+soon\"+when:7d&hl=en-US&gl=US&ceid=US:en", "Product Launches"),
        ];

        for (url, category) in rss_feeds {
            match parse_google_news_rss(url, category).await {
                Ok(mut feed_events) => {
                    events.append(&mut feed_events);
                }
                Err(e) => {
                    eprintln!("Failed to fetch Google News RSS for {}: {}", category, e);
                }
            }
        }

        Ok(events)
    }

    // Parse Google News RSS feed
async fn parse_google_news_rss(url: &str, category: &str) -> Result<Vec<TechEvent>, Box<dyn std::error::Error>> {
        let response = reqwest::get(url).await?;
        let content = response.bytes().await?;
        let feed = parser::parse(&content[..])?;

        let mut events = Vec::new();

        for entry in feed.entries.iter().take(20) { // Limit to 20 per feed
            if let Some(event) = parse_rss_entry_to_event(entry, category) {
                // Only include events with predictable outcomes
                if is_predictable_event(&event) {
                    events.push(event);
                }
            }
        }

        Ok(events)
    }

// Standalone helper functions for parsing RSS

fn parse_rss_entry_to_event(entry: &feed_rs::model::Entry, category: &str) -> Option<TechEvent> {
        let title = entry.title.as_ref().map(|t| t.content.as_str()).unwrap_or("Untitled");
        let summary = entry.summary.as_ref().map(|s| s.content.as_str()).unwrap_or("");
        let published = entry.published.unwrap_or_else(|| chrono::Utc::now());

        // Look for predictable patterns in tech/business news
        let predictable_patterns = [
            ("earnings", "beats estimates", EventType::EarningsAnnouncement),
            ("will launch", "launches successfully", EventType::ProductLaunch),
            ("plans to release", "releases on time", EventType::ProductLaunch),
            ("IPO", "exceeds price range", EventType::IPO),
            ("acquisition", "deal completes", EventType::Acquisition),
            ("announces", "announcement happens", EventType::Conference),
            ("expected to", "expectation met", EventType::TechBreakthrough),
        ];

        for (trigger, outcome, event_type) in predictable_patterns {
            if title.to_lowercase().contains(trigger) || summary.to_lowercase().contains(trigger) {
                let prediction_question = generate_prediction_question(title, &trigger, &outcome);
                
                return Some(TechEvent {
                    id: format!("gnews_{}_{}", category.to_lowercase().replace(" ", "_"), uuid::Uuid::new_v4()),
                    title: prediction_question.clone(),
                    description: format!("Based on: {} (Source: Google News)", title),
                    event_type,
                    start_date: published + chrono::Duration::days(7), // Resolve in 1 week
                    end_date: Some(published + chrono::Duration::days(30)), // Expire in 30 days
                    source: "Google News RSS".to_string(),
                    confidence_score: calculate_confidence_from_title(title, summary),
                    tags: extract_tags(title, summary),
                    related_companies: extract_companies(title, summary),
                });
            }
        }

        None
    }

// Generate prediction question from news title
fn generate_prediction_question(title: &str, trigger: &str, _outcome: &str) -> String {
        match trigger {
            "earnings" => {
                if let Some(company) = extract_company_from_earnings(title) {
                    format!("Will {} earnings beat analyst estimates?", company)
                } else {
                    format!("Will the earnings report mentioned beat estimates?")
                }
            },
            "will launch" | "plans to release" => {
                format!("Will the product launch mentioned in '{}' happen on schedule?", 
                    title.chars().take(50).collect::<String>())
            },
            "IPO" => {
                if let Some(company) = extract_company_from_ipo(title) {
                    format!("Will {} IPO exceed its initial price range?", company)
                } else {
                    format!("Will the IPO mentioned exceed its price range?")
                }
            },
            "acquisition" => {
                format!("Will the acquisition deal mentioned be completed successfully?")
            },
            _ => {
                format!("Will the event '{}' happen as predicted?", 
                    title.chars().take(60).collect::<String>())
            }
        }
    }

// Get live crypto events (15-minute intervals)
fn get_live_crypto_events() -> Vec<TechEvent> {
        let now = chrono::Utc::now();
        
        vec![
            TechEvent {
                id: "btc_15min_live".to_string(),
                title: "Bitcoin Price Higher in 15 Minutes".to_string(),
                description: "Will Bitcoin price be higher than current price in exactly 15 minutes?".to_string(),
                event_type: EventType::MarketMovement,
                start_date: now + chrono::Duration::minutes(15),
                end_date: Some(now + chrono::Duration::minutes(16)),
                source: "Live Crypto Feed".to_string(),
                confidence_score: 0.5, // Pure 50/50 bet
                tags: vec!["Bitcoin".to_string(), "Crypto".to_string(), "Live".to_string()],
                related_companies: vec!["Bitcoin".to_string()],
            },
            TechEvent {
                id: "sol_15min_live".to_string(),
                title: "Solana Price Higher in 15 Minutes".to_string(),
                description: "Will Solana price be higher than current price in exactly 15 minutes?".to_string(),
                event_type: EventType::MarketMovement,
                start_date: now + chrono::Duration::minutes(15),
                end_date: Some(now + chrono::Duration::minutes(16)),
                source: "Live Crypto Feed".to_string(),
                confidence_score: 0.5,
                tags: vec!["Solana".to_string(), "Crypto".to_string(), "Live".to_string()],
                related_companies: vec!["Solana".to_string()],
            },
        ]
    }

// Score events by importance (return top 100)
fn score_events_by_importance(events: Vec<TechEvent>) -> Vec<EventScore> {
        let mut scored_events: Vec<EventScore> = events
            .into_iter()
            .map(|event| {
                let importance_score = calculate_importance_score(&event);
                EventScore { event, importance_score }
            })
            .collect();

        // Sort by importance score (highest first)
        scored_events.sort_by(|a, b| b.importance_score.partial_cmp(&a.importance_score).unwrap());
        
        scored_events
    }

    // Calculate importance score for filtering
fn calculate_importance_score(event: &TechEvent) -> f64 {
        let mut score = 0.0;

        // Base score from confidence
        score += event.confidence_score * 50.0;

        // Company importance multipliers
        let major_companies = [
            ("apple", 20.0), ("google", 18.0), ("microsoft", 17.0), 
            ("amazon", 16.0), ("tesla", 15.0), ("nvidia", 14.0),
            ("meta", 13.0), ("openai", 12.0), ("bitcoin", 11.0),
        ];

        for company in &event.related_companies {
            for (major_company, multiplier) in major_companies {
                if company.to_lowercase().contains(major_company) {
                    score += multiplier;
                }
            }
        }

        // Event type importance
        match event.event_type {
            EventType::EarningsAnnouncement => score += 15.0,
            EventType::ProductLaunch => score += 12.0,
            EventType::IPO => score += 18.0,
            EventType::Acquisition => score += 16.0,
            EventType::TechBreakthrough => score += 10.0,
            EventType::MarketMovement => score += 5.0, // Live crypto markets
            _ => score += 8.0,
        }

        // Recency bonus (newer events more important)
        let days_old = (chrono::Utc::now() - event.start_date).num_days().abs();
        if days_old < 7 {
            score += 10.0 - (days_old as f64);
        }

        // Tag-based bonuses
        let important_tags = ["AI", "Bitcoin", "IPO", "Earnings", "Launch"];
        for tag in &event.tags {
            if important_tags.contains(&tag.as_str()) {
                score += 5.0;
            }
        }

        score
    }

    // Helper functions
fn is_predictable_event(event: &TechEvent) -> bool {
        event.confidence_score >= 0.4 && !event.title.is_empty()
    }

fn calculate_confidence_from_title(title: &str, summary: &str) -> f64 {
        let mut confidence: f64 = 0.5; // Base confidence

        // Higher confidence indicators
        let high_confidence_words = ["earnings", "scheduled", "announced", "confirmed"];
        let medium_confidence_words = ["expected", "plans", "will", "likely"];
        let low_confidence_words = ["rumors", "might", "could", "possibly"];

        let text = format!("{} {}", title, summary).to_lowercase();

        for word in high_confidence_words {
            if text.contains(word) { confidence += 0.2; }
        }
        for word in medium_confidence_words {
            if text.contains(word) { confidence += 0.1; }
        }
        for word in low_confidence_words {
            if text.contains(word) { confidence -= 0.1; }
        }

        confidence.min(0.95).max(0.1)
    }

fn extract_company_from_earnings(title: &str) -> Option<String> {
        let companies = ["Apple", "Google", "Microsoft", "Amazon", "Tesla", "NVIDIA", "Meta"];
        for company in companies {
            if title.contains(company) {
                return Some(company.to_string());
            }
        }
        None
    }

fn extract_company_from_ipo(title: &str) -> Option<String> {
        // Simple extraction - look for company name before "IPO"
        if let Some(ipo_pos) = title.find("IPO") {
            let before_ipo = &title[..ipo_pos];
            let words: Vec<&str> = before_ipo.split_whitespace().collect();
            if let Some(last_word) = words.last() {
                return Some(last_word.to_string());
            }
        }
        None
    }

    // NewsAPI - tech news that can be turned into prediction markets
async fn fetch_newsapi_events(api_key: &str) -> Result<Vec<TechEvent>, Box<dyn std::error::Error>> {
        let url = format!(
            "https://newsapi.org/v2/everything?q=(\"will launch\" OR \"plans to\" OR \"announces\" OR \"expected to\") AND (apple OR google OR microsoft OR tesla OR nvidia OR meta OR openai)&language=en&sortBy=publishedAt&apiKey={}",
            api_key
        );

        let response = reqwest::get(&url).await?;
        let data: serde_json::Value = response.json().await?;

        let mut events = Vec::new();
        
        if let Some(articles) = data["articles"].as_array() {
            for article in articles {
                if let Some(event) = parse_news_article_to_event(article) {
                    events.push(event);
                }
            }
        }

        Ok(events)
    }

    // Alpha Vantage - earnings announcements and IPO calendar
async fn fetch_alphavantage_events(api_key: &str) -> Result<Vec<TechEvent>, Box<dyn std::error::Error>> {
        // Earnings Calendar API
        let earnings_url = format!(
            "https://www.alphavantage.co/query?function=EARNINGS_CALENDAR&horizon=3month&apikey={}",
            api_key
        );

        let response = reqwest::get(&earnings_url).await?;
        let earnings_data = response.text().await?;

        // IPO Calendar API
        let ipo_url = format!(
            "https://www.alphavantage.co/query?function=IPO_CALENDAR&apikey={}",
            api_key
        );

        let ipo_response = reqwest::get(&ipo_url).await?;
        let ipo_data = ipo_response.text().await?;

        // Parse CSV responses into events
        let mut events = Vec::new();
        events.extend(parse_earnings_csv(&earnings_data)?);
        events.extend(parse_ipo_csv(&ipo_data)?);

        Ok(events)
    }

    // Hardcoded reliable upcoming tech events
fn get_known_upcoming_events() -> Vec<TechEvent> {
        vec![
            TechEvent {
                id: "apple_q4_2024_earnings".to_string(),
                title: "Apple Q4 2024 Earnings Beat Estimates".to_string(),
                description: "Will Apple Q4 2024 earnings beat analyst estimates?".to_string(),
                event_type: EventType::EarningsAnnouncement,
                start_date: chrono::Utc::now() + chrono::Duration::days(30),
                end_date: None,
                source: "Known Schedule".to_string(),
                confidence_score: 0.95,
                tags: vec!["Apple".to_string(), "Earnings".to_string()],
                related_companies: vec!["Apple Inc.".to_string()],
            },
            TechEvent {
                id: "ces_2025_ai_announcement".to_string(),
                title: "Major AI Breakthrough Announced at CES 2025".to_string(),
                description: "Will a major AI company announce a breakthrough at CES 2025 (Jan 7-10)?".to_string(),
                event_type: EventType::Conference,
                start_date: chrono::DateTime::parse_from_rfc3339("2025-01-07T00:00:00Z").unwrap().into(),
                end_date: Some(chrono::DateTime::parse_from_rfc3339("2025-01-10T23:59:59Z").unwrap().into()),
                source: "CES Schedule".to_string(),
                confidence_score: 0.8,
                tags: vec!["CES".to_string(), "AI".to_string(), "Conference".to_string()],
                related_companies: vec!["NVIDIA".to_string(), "AMD".to_string(), "Intel".to_string()],
            },
            TechEvent {
                id: "google_io_2025_android".to_string(),
                title: "Google I/O 2025 Announces New Android Version".to_string(),
                description: "Will Google announce Android 16 or major Android update at I/O 2025?".to_string(),
                event_type: EventType::ProductLaunch,
                start_date: chrono::DateTime::parse_from_rfc3339("2025-05-14T00:00:00Z").unwrap().into(),
                end_date: None,
                source: "Google I/O Schedule".to_string(),
                confidence_score: 0.9,
                tags: vec!["Google".to_string(), "Android".to_string(), "I/O".to_string()],
                related_companies: vec!["Google".to_string(), "Alphabet Inc.".to_string()],
            },
        ]
    }

    // Scrape major tech conference websites
async fn fetch_tech_conferences() -> Result<Vec<TechEvent>, Box<dyn std::error::Error>> {
        // This would scrape conference websites or use APIs like:
        // - Eventbrite API
        // - Meetup API  
        // - Conference websites RSS feeds
        
        Ok(vec![
            TechEvent {
                id: "tc_disrupt_2025".to_string(),
                title: "TechCrunch Disrupt 2025 - Startup Unicorn Announcement".to_string(),
                description: "Will a new unicorn ($1B+ valuation) be announced at TechCrunch Disrupt 2025?".to_string(),
                event_type: EventType::Conference,
                start_date: chrono::DateTime::parse_from_rfc3339("2025-09-08T00:00:00Z").unwrap().into(),
                end_date: Some(chrono::DateTime::parse_from_rfc3339("2025-09-10T23:59:59Z").unwrap().into()),
                source: "TechCrunch".to_string(),
                confidence_score: 0.75,
                tags: vec!["TechCrunch".to_string(), "Startup".to_string(), "Unicorn".to_string()],
                related_companies: vec!["Various Startups".to_string()],
            },
        ])
    }

    // Parse news article into predictable event
fn parse_news_article_to_event(article: &serde_json::Value) -> Option<TechEvent> {
        let title = article["title"].as_str()?;
        let description = article["description"].as_str().unwrap_or("");
        let published_at = article["publishedAt"].as_str()?;
        
        // Look for predictable phrases
        let predictable_phrases = [
            ("will launch", EventType::ProductLaunch),
            ("plans to release", EventType::ProductLaunch),
            ("announces plans", EventType::ProductLaunch),
            ("expected earnings", EventType::EarningsAnnouncement),
            ("IPO filing", EventType::IPO),
            ("acquisition talks", EventType::Acquisition),
        ];

        for (phrase, event_type) in predictable_phrases {
            if title.to_lowercase().contains(phrase) || description.to_lowercase().contains(phrase) {
                let published_date: chrono::DateTime<chrono::Utc> = chrono::DateTime::parse_from_rfc3339(published_at).ok()?.into();
                
                return Some(TechEvent {
                    id: format!("news_{}", uuid::Uuid::new_v4()),
                    title: format!("Prediction: {}", title),
                    description: description.to_string(),
                    event_type,
                    start_date: published_date + chrono::Duration::days(30), // Assume 30 day resolution
                    end_date: None,
                    source: "NewsAPI".to_string(),
                    confidence_score: 0.6,
                    tags: extract_tags(title, description),
                    related_companies: extract_companies(title, description),
                });
            }
        }

        None
    }

fn extract_tags(title: &str, description: &str) -> Vec<String> {
        let text = format!("{} {}", title, description).to_lowercase();
        let mut tags = Vec::new();

        let tag_keywords = [
            ("ai", "AI"),
            ("artificial intelligence", "AI"),
            ("machine learning", "ML"),
            ("blockchain", "Blockchain"),
            ("cryptocurrency", "Crypto"),
            ("bitcoin", "Bitcoin"),
            ("ethereum", "Ethereum"),
            ("iphone", "iPhone"),
            ("android", "Android"),
            ("tesla", "Tesla"),
            ("electric vehicle", "EV"),
            ("autonomous", "Autonomous"),
            ("quantum", "Quantum"),
            ("5g", "5G"),
            ("metaverse", "Metaverse"),
            ("vr", "VR"),
            ("ar", "AR"),
        ];

        for (keyword, tag) in tag_keywords {
            if text.contains(keyword) {
                tags.push(tag.to_string());
            }
        }

        tags
    }

fn extract_companies(title: &str, description: &str) -> Vec<String> {
        let text = format!("{} {}", title, description).to_lowercase();
        let mut companies = Vec::new();

        let company_names = [
            "apple", "google", "microsoft", "amazon", "meta", "tesla", 
            "nvidia", "amd", "intel", "openai", "anthropic", "netflix",
            "spotify", "uber", "airbnb", "twitter", "x corp", "spacex"
        ];

        for company in company_names {
            if text.contains(company) {
                companies.push(company.to_string());
            }
        }

        companies
    }

// Standalone function for parsing earnings CSV
fn parse_earnings_csv(csv_data: &str) -> Result<Vec<TechEvent>, Box<dyn std::error::Error>> {
        let mut events = Vec::new();
        
        for line in csv_data.lines().skip(1) { // Skip header
            let fields: Vec<&str> = line.split(',').collect();
            if fields.len() >= 3 {
                let symbol = fields[0].trim();
                let company_name = fields[1].trim();
                let report_date = fields[2].trim();
                
                // Only include major tech companies
                let tech_companies = ["AAPL", "GOOGL", "MSFT", "AMZN", "META", "TSLA", "NVDA"];
                if tech_companies.contains(&symbol) {
                    if let Ok(date) = chrono::DateTime::parse_from_str(&format!("{} 00:00:00 +0000", report_date), "%Y-%m-%d %H:%M:%S %z") {
                        events.push(TechEvent {
                            id: format!("earnings_{}_{}", symbol, report_date),
                            title: format!("{} Earnings Beat Estimates", company_name),
                            description: format!("Will {} earnings beat analyst estimates on {}?", company_name, report_date),
                            event_type: EventType::EarningsAnnouncement,
                            start_date: date.into(),
                            end_date: None,
                            source: "Alpha Vantage".to_string(),
                            confidence_score: 0.85,
                            tags: vec!["Earnings".to_string(), symbol.to_string()],
                            related_companies: vec![company_name.to_string()],
                        });
                    }
                }
            }
        }
        
        Ok(events)
    }

fn parse_ipo_csv(csv_data: &str) -> Result<Vec<TechEvent>, Box<dyn std::error::Error>> {
        let mut events = Vec::new();
        
        for line in csv_data.lines().skip(1) { // Skip header
            let fields: Vec<&str> = line.split(',').collect();
            if fields.len() >= 4 {
                let symbol = fields[0].trim();
                let company_name = fields[1].trim();
                let ipo_date = fields[2].trim();
                let price_range = fields[3].trim();
                
                if let Ok(date) = chrono::DateTime::parse_from_str(&format!("{} 00:00:00 +0000", ipo_date), "%Y-%m-%d %H:%M:%S %z") {
                    events.push(TechEvent {
                        id: format!("ipo_{}_{}", symbol, ipo_date),
                        title: format!("{} IPO Above Price Range", company_name),
                        description: format!("Will {} IPO price exceed the high end of range {} on {}?", company_name, price_range, ipo_date),
                        event_type: EventType::IPO,
                        start_date: date.into(),
                        end_date: None,
                        source: "Alpha Vantage".to_string(),
                        confidence_score: 0.7,
                        tags: vec!["IPO".to_string(), symbol.to_string()],
                        related_companies: vec![company_name.to_string()],
                    });
                }
            }
        }
        
        Ok(events)
    }

// Integration with blockchain for automatic market creation
impl PredictionMarketBlockchain {
    pub async fn sync_real_tech_events(&mut self) -> Result<usize, String> {
        let event_provider = EventDataProvider::new();
        
        let events = event_provider
            .fetch_upcoming_events()
            .await
            .map_err(|e| format!("Failed to fetch tech events: {}", e))?;

        let mut new_markets = 0;
        
        for event in events {
            // Only create markets for high-confidence events
            if event.confidence_score >= 0.7 {
                if let Some(market) = self.create_market_from_tech_event(&event) {
                    if !self.markets.contains_key(&market.id) {
                        self.markets.insert(market.id.clone(), market);
                        new_markets += 1;
                    }
                }
            }
        }

        Ok(new_markets)
    }

    fn create_market_from_tech_event(&self, event: &TechEvent) -> Option<Market> {
        let (outcome_yes, outcome_no) = match event.event_type {
            EventType::ProductLaunch => ("🚀 Product Launches", "⏰ Launch Delayed/Cancelled"),
            EventType::EarningsAnnouncement => ("📈 Beats Estimates", "📉 Misses Estimates"),
            EventType::IPO => ("🎯 Above Price Range", "📊 Within/Below Range"),
            EventType::Acquisition => ("✅ Deal Completed", "❌ Deal Falls Through"),
            EventType::Conference => ("🎤 Announcement Made", "🤐 No Major News"),
            EventType::TechBreakthrough => ("🔬 Breakthrough Confirmed", "⚠️ Overhyped/False"),
            EventType::Regulation => ("⚖️ Regulation Passed", "🚫 Blocked/Delayed"),
            EventType::Partnership => ("🤝 Partnership Announced", "💔 No Partnership"),
            EventType::MarketMovement => ("📈 Price HIGHER", "📉 Price LOWER/Same"), // Crypto 15min betting
        };

        // Calculate odds based on event type and confidence
        let base_odds = match event.event_type {
            EventType::EarningsAnnouncement => (1.8, 2.0), // Earnings are somewhat predictable
            EventType::ProductLaunch => (2.5, 1.5),        // Product launches often delayed
            EventType::IPO => (2.2, 1.7),                  // IPO success varies
            EventType::Conference => (3.0, 1.35),          // Conference announcements unpredictable
            EventType::MarketMovement => (1.95, 1.95),     // 15-minute crypto betting - nearly even odds
            EventType::TechBreakthrough => (4.0, 1.25),    // Tech breakthroughs rare but valuable
            _ => (2.0, 1.8),                               // Default balanced odds
        };

        Some(Market {
            id: format!("event_{}", event.id),
            title: event.title.clone(),
            description: format!("{} (Source: {}, Confidence: {:.0}%)", 
                event.description, event.source, event.confidence_score * 100.0),
            outcomes: vec![outcome_yes.to_string(), outcome_no.to_string()],
            odds: vec![base_odds.0, base_odds.1],
            total_volume: 0,
            is_active: true,
        })
    }
}