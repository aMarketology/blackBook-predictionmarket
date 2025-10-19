use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use regex::Regex;
use chrono::{DateTime, Utc, NaiveDate, Duration};
// Removed unused import

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObjectWireArticle {
    pub id: String,
    pub title: String,
    pub content: String,
    pub published_date: DateTime<Utc>,
    pub author: Option<String>,
    pub tags: Vec<String>,
    pub url: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PredictableClaim {
    pub article_id: String,
    pub claim_text: String,
    pub claim_type: ClaimType,
    pub prediction_question: String,
    pub outcomes: Vec<String>,
    pub resolution_date: Option<DateTime<Utc>>,
    pub confidence_score: f64, // 0.0 to 1.0 - how predictable this claim is
    pub market_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum ClaimType {
    PolicyImplementation,
    EconomicIndicator,
    CorporateAction,
    GeopoliticalEvent,
    TechnologyLaunch,
    RegulatoryDecision,
    MarketMovement,
    DateSpecific,
}

#[derive(Debug, Clone)]
pub struct ObjectWireParser {
    claim_patterns: HashMap<ClaimType, Vec<ClaimPattern>>,
}

#[derive(Clone)]
struct ClaimPattern {
    regex: Regex,
    question_template: String,
    outcomes_template: Vec<String>,
    confidence_modifier: f64,
}

// Implement Debug manually since Regex doesn't implement Debug in a useful way
impl std::fmt::Debug for ClaimPattern {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("ClaimPattern")
            .field("regex", &self.regex.as_str())
            .field("question_template", &self.question_template)
            .field("outcomes_template", &self.outcomes_template)
            .field("confidence_modifier", &self.confidence_modifier)
            .finish()
    }
}

impl ObjectWireParser {
    pub fn new() -> Self {
        let mut parser = ObjectWireParser {
            claim_patterns: HashMap::new(),
        };
        parser.initialize_patterns();
        parser
    }

    fn initialize_patterns(&mut self) {
        // Policy Implementation Patterns
        let policy_patterns = vec![
            ClaimPattern {
                regex: Regex::new(r"(?i)(?P<entity>[A-Z][A-Za-z\s]+)\s+(?:will|plans to|intends to|announces)\s+(?P<action>[^.]+)\s+by\s+(?P<date>[^.]+)").unwrap(),
                question_template: "Will {entity} {action} by {date}?".to_string(),
                outcomes_template: vec!["✅ Yes - {action}".to_string(), "❌ No - Delayed/Cancelled".to_string()],
                confidence_modifier: 0.8,
            },
            ClaimPattern {
                regex: Regex::new(r"(?i)(?P<country>[A-Z][a-z]+)\s+to\s+(?P<action>implement|introduce|launch)\s+(?P<policy>[^.]+)\s+in\s+(?P<timeframe>\d{4})").unwrap(),
                question_template: "Will {country} {action} {policy} in {timeframe}?".to_string(),
                outcomes_template: vec!["🏛️ Policy Implemented".to_string(), "⏰ Implementation Delayed".to_string()],
                confidence_modifier: 0.75,
            },
        ];

        // Economic Indicator Patterns
        let economic_patterns = vec![
            ClaimPattern {
                regex: Regex::new(r"(?i)(?P<indicator>GDP|inflation|unemployment|interest rates?)\s+(?:expected to|projected to|will)\s+(?P<direction>rise|fall|increase|decrease)\s+(?:to\s+)?(?P<target>[\d.]+%?)?\s*(?:by\s+(?P<date>[^.]+))?").unwrap(),
                question_template: "Will {indicator} {direction} to {target} by {date}?".to_string(),
                outcomes_template: vec!["📊 Target Reached".to_string(), "📈 Target Missed".to_string()],
                confidence_modifier: 0.7,
            },
            ClaimPattern {
                regex: Regex::new(r"(?i)Federal Reserve\s+(?:will|expected to|likely to)\s+(?P<action>raise|cut|maintain)\s+(?:interest\s+)?rates?\s+(?:by\s+(?P<amount>[\d.]+%?))?\s*(?:by\s+(?P<date>[^.]+))?").unwrap(),
                question_template: "Will the Federal Reserve {action} rates by {amount} by {date}?".to_string(),
                outcomes_template: vec!["🔺 Rate {action}".to_string(), "➡️ No Rate Change".to_string()],
                confidence_modifier: 0.85,
            },
        ];

        // Corporate Action Patterns
        let corporate_patterns = vec![
            ClaimPattern {
                regex: Regex::new(r"(?i)(?P<company>[A-Z][A-Za-z\s]+)\s+(?:will|plans to|announces)\s+(?P<action>acquire|merge with|launch|release)\s+(?P<target>[^.]+)\s+(?:by\s+(?P<date>[^.]+))?").unwrap(),
                question_template: "Will {company} {action} {target} by {date}?".to_string(),
                outcomes_template: vec!["🚀 Action Completed".to_string(), "⏸️ Action Delayed/Cancelled".to_string()],
                confidence_modifier: 0.72,
            },
            ClaimPattern {
                regex: Regex::new(r"(?i)(?P<company>[A-Z][A-Za-z\s]+)\s+(?:stock|shares)\s+(?:expected to|projected to|will)\s+(?P<direction>reach|hit|exceed|fall below)\s+(?P<price>\$[\d,]+)\s+(?:by\s+(?P<date>[^.]+))?").unwrap(),
                question_template: "Will {company} stock {direction} {price} by {date}?".to_string(),
                outcomes_template: vec!["🎯 Price Target Hit".to_string(), "📉 Price Target Missed".to_string()],
                confidence_modifier: 0.6,
            },
        ];

        // Geopolitical Event Patterns
        let geopolitical_patterns = vec![
            ClaimPattern {
                regex: Regex::new(r"(?i)(?P<country1>[A-Z][a-z]+)\s+(?:and|with)\s+(?P<country2>[A-Z][a-z]+)\s+(?:will|expected to|plan to)\s+(?P<action>[^.]+)\s+(?:by\s+(?P<date>[^.]+))?").unwrap(),
                question_template: "Will {country1} and {country2} {action} by {date}?".to_string(),
                outcomes_template: vec!["🤝 Agreement Reached".to_string(), "🚫 No Agreement".to_string()],
                confidence_modifier: 0.65,
            },
            ClaimPattern {
                regex: Regex::new(r"(?i)(?P<organization>UN|NATO|EU|G7|G20)\s+(?:will|plans to|expected to)\s+(?P<action>[^.]+)\s+(?:by\s+(?P<date>[^.]+))?").unwrap(),
                question_template: "Will {organization} {action} by {date}?".to_string(),
                outcomes_template: vec!["✅ Action Taken".to_string(), "❌ No Action".to_string()],
                confidence_modifier: 0.7,
            },
        ];

        // Technology Launch Patterns
        let tech_patterns = vec![
            ClaimPattern {
                regex: Regex::new(r"(?i)(?P<company>[A-Z][A-Za-z\s]+)\s+(?:will|plans to|announces)\s+(?:launch|release|unveil)\s+(?P<product>[^.]+)\s+(?:in|by)\s+(?P<timeframe>[^.]+)").unwrap(),
                question_template: "Will {company} launch {product} by {timeframe}?".to_string(),
                outcomes_template: vec!["🚀 Product Launched".to_string(), "⏰ Launch Delayed".to_string()],
                confidence_modifier: 0.78,
            },
        ];

        self.claim_patterns.insert(ClaimType::PolicyImplementation, policy_patterns);
        self.claim_patterns.insert(ClaimType::EconomicIndicator, economic_patterns);
        self.claim_patterns.insert(ClaimType::CorporateAction, corporate_patterns);
        self.claim_patterns.insert(ClaimType::GeopoliticalEvent, geopolitical_patterns);
        self.claim_patterns.insert(ClaimType::TechnologyLaunch, tech_patterns);
    }

    pub fn extract_claims(&self, article: &ObjectWireArticle) -> Vec<PredictableClaim> {
        let mut claims = Vec::new();
        let full_text = format!("{} {}", article.title, article.content);

        for (claim_type, patterns) in &self.claim_patterns {
            for pattern in patterns {
                if let Some(captures) = pattern.regex.captures(&full_text) {
                    if let Some(claim) = self.create_claim_from_match(
                        article,
                        claim_type.clone(),
                        pattern,
                        &captures,
                    ) {
                        claims.push(claim);
                    }
                }
            }
        }

        // Sort by confidence score (highest first)
        claims.sort_by(|a, b| b.confidence_score.partial_cmp(&a.confidence_score).unwrap());
        claims
    }

    fn create_claim_from_match(
        &self,
        article: &ObjectWireArticle,
        claim_type: ClaimType,
        pattern: &ClaimPattern,
        captures: &regex::Captures,
    ) -> Option<PredictableClaim> {
        let mut question = pattern.question_template.clone();
        let mut outcomes = pattern.outcomes_template.clone();
        
        // Replace placeholders with actual matches
        // Get all named capture groups from the regex
        for (name, value) in pattern.regex.capture_names()
            .enumerate()
            .filter_map(|(i, name)| {
                name.and_then(|n| captures.get(i + 1).map(|m| (n, m.as_str())))
            }) {
            let placeholder = format!("{{{}}}", name);
            question = question.replace(&placeholder, value);
            for outcome in &mut outcomes {
                *outcome = outcome.replace(&placeholder, value);
            }
        }

        // Extract and parse date if present
        let resolution_date = captures.name("date")
            .and_then(|date_str| self.parse_date(date_str.as_str()))
            .or_else(|| {
                // Default to 1 year from article publication if no specific date
                Some(article.published_date + Duration::days(365))
            });

        // Calculate confidence score based on article factors
        let base_confidence = pattern.confidence_modifier;
        let date_confidence = if resolution_date.is_some() { 0.2 } else { -0.1 };
        let length_confidence = if article.content.len() > 500 { 0.1 } else { -0.05 };
        
        let final_confidence = (base_confidence + date_confidence + length_confidence)
            .max(0.0)
            .min(1.0);

        Some(PredictableClaim {
            article_id: article.id.clone(),
            claim_text: captures.get(0)?.as_str().to_string(),
            claim_type,
            prediction_question: question,
            outcomes,
            resolution_date,
            confidence_score: final_confidence,
            market_id: None,
        })
    }

    fn parse_date(&self, date_str: &str) -> Option<DateTime<Utc>> {
        // Try various date formats commonly found in articles
        let date_formats = vec![
            "%B %d, %Y",      // "December 31, 2025"
            "%b %d, %Y",      // "Dec 31, 2025"
            "%Y-%m-%d",       // "2025-12-31"
            "%m/%d/%Y",       // "12/31/2025"
            "Q%q %Y",         // "Q4 2025" (needs custom parsing)
            "%Y",             // "2025" (assume end of year)
        ];

        // Handle quarterly formats
        if let Some(caps) = Regex::new(r"Q(\d)\s+(\d{4})").unwrap().captures(date_str) {
            if let (Some(quarter), Some(year)) = (caps.get(1), caps.get(2)) {
                if let (Ok(q), Ok(y)) = (quarter.as_str().parse::<u32>(), year.as_str().parse::<i32>()) {
                    let month = match q {
                        1 => 3,   // Q1 ends in March
                        2 => 6,   // Q2 ends in June  
                        3 => 9,   // Q3 ends in September
                        4 => 12,  // Q4 ends in December
                        _ => 12,
                    };
                    if let Some(date) = NaiveDate::from_ymd_opt(y, month, 1) {
                        return Some(date.and_hms_opt(23, 59, 59)?.and_utc());
                    }
                }
            }
        }

        // Try standard date parsing
        for format in date_formats {
            if let Ok(date) = NaiveDate::parse_from_str(date_str, format) {
                return Some(date.and_hms_opt(23, 59, 59)?.and_utc());
            }
        }

        None
    }

    pub async fn fetch_objectwire_articles(&self) -> Result<Vec<ObjectWireArticle>, Box<dyn std::error::Error>> {
        // This would integrate with ObjectWire's RSS feed or API
        // For now, return mock data that represents ObjectWire's style
        
        let mock_articles = vec![
            ObjectWireArticle {
                id: "ow_001".to_string(),
                title: "Federal Reserve Signals Rate Adjustment by December 2025 Meeting".to_string(),
                content: "Federal Reserve officials indicate they will reassess monetary policy stance based on inflation data, with potential rate adjustment expected by the December 2025 FOMC meeting. Market participants anticipate a 25 basis point modification based on current economic indicators.".to_string(),
                published_date: Utc::now(),
                author: Some("ObjectWire Economic Analysis".to_string()),
                tags: vec!["Federal Reserve".to_string(), "Interest Rates".to_string(), "Monetary Policy".to_string()],
                url: "https://objectwire.org/fed-rate-december-2025".to_string(),
            },
            ObjectWireArticle {
                id: "ow_002".to_string(),
                title: "OpenAI Plans IPO Filing by Q2 2026 According to Internal Sources".to_string(),
                content: "OpenAI executives are preparing for initial public offering documentation with target filing date of Q2 2026, pending regulatory review and market conditions. Valuation estimates range from $150-200 billion based on current revenue projections.".to_string(),
                published_date: Utc::now() - Duration::hours(2),
                author: Some("ObjectWire Corporate Intelligence".to_string()),
                tags: vec!["OpenAI".to_string(), "IPO".to_string(), "Technology".to_string()],
                url: "https://objectwire.org/openai-ipo-q2-2026".to_string(),
            },
        ];

        Ok(mock_articles)
    }

    pub fn generate_market_from_claim(&self, claim: &PredictableClaim) -> Option<crate::blockchain::Market> {
        if claim.confidence_score < 0.6 {
            return None; // Only create markets for high-confidence claims
        }

        // Calculate odds based on claim type and confidence
        let base_odds = match claim.claim_type {
            ClaimType::PolicyImplementation => (2.2, 1.7),   // Policy often delayed
            ClaimType::EconomicIndicator => (2.5, 1.5),     // Economic predictions moderately reliable
            ClaimType::CorporateAction => (1.8, 2.0),       // Corporate actions often happen as announced
            ClaimType::GeopoliticalEvent => (3.5, 1.25),    // Geopolitical events unpredictable
            ClaimType::TechnologyLaunch => (2.8, 1.4),      // Tech launches often delayed
            ClaimType::RegulatoryDecision => (2.1, 1.8),    // Regulatory decisions moderately predictable
            ClaimType::MarketMovement => (1.9, 1.9),        // Market movements are 50/50
            ClaimType::DateSpecific => (1.6, 2.3),          // Date-specific events more likely
        };

        // Adjust odds based on confidence score
        let confidence_factor = claim.confidence_score;
        let adjusted_odds = (
            base_odds.0 * (2.0 - confidence_factor),
            base_odds.1 * (1.0 + confidence_factor * 0.5),
        );

        Some(crate::blockchain::Market {
            id: format!("ow_{}", claim.article_id),
            title: format!("📰 {}", claim.prediction_question),
            description: format!("Market generated from ObjectWire analysis: {}", claim.claim_text),
            outcomes: claim.outcomes.clone(),
            odds: vec![adjusted_odds.0, adjusted_odds.1],
            total_volume: 0,
            is_active: true,
        })
    }
}