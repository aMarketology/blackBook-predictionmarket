use serde::{Deserialize, Serialize};

/// Simple scraped event data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScrapedEvent {
    pub title: String,
    pub description: String,
    pub date: String,
    pub url: String,
}

/// Scrape a URL and extract basic event information
pub async fn scrape_url(url: &str) -> Result<ScrapedEvent, String> {
    // Fetch the webpage
    let response = reqwest::get(url)
        .await
        .map_err(|e| format!("Failed to fetch URL: {}", e))?;

    let html = response
        .text()
        .await
        .map_err(|e| format!("Failed to read response: {}", e))?;

    // Extract title, description, and date from HTML
    let title = extract_title(&html).unwrap_or_else(|| "Untitled Event".to_string());
    let description = extract_description(&html).unwrap_or_else(|| "No description available".to_string());
    let date = extract_date(&html).unwrap_or_else(|| "Date unknown".to_string());

    Ok(ScrapedEvent {
        title,
        description,
        date,
        url: url.to_string(),
    })
}

/// Extract title from HTML
fn extract_title(html: &str) -> Option<String> {
    use scraper::{Html, Selector};

    let document = Html::parse_document(html);
    
    // Try common title selectors
    let selectors = vec![
        "h1",
        ".title",
        ".event-title",
        "[data-title]",
        "meta[property='og:title']",
    ];

    for selector_str in selectors {
        if let Ok(selector) = Selector::parse(selector_str) {
            if let Some(element) = document.select(&selector).next() {
                if selector_str.contains("meta") {
                    if let Some(content) = element.value().attr("content") {
                        return Some(content.trim().to_string());
                    }
                } else {
                    let text: String = element.text().collect::<String>().trim().to_string();
                    if !text.is_empty() {
                        return Some(text);
                    }
                }
            }
        }
    }

    None
}

/// Extract description from HTML
fn extract_description(html: &str) -> Option<String> {
    use scraper::{Html, Selector};

    let document = Html::parse_document(html);

    // Try common description selectors
    let selectors = vec![
        ".description",
        ".event-description",
        ".details",
        "p",
        "[data-description]",
        "meta[name='description']",
    ];

    for selector_str in selectors {
        if let Ok(selector) = Selector::parse(selector_str) {
            if let Some(element) = document.select(&selector).next() {
                if selector_str.contains("meta") {
                    if let Some(content) = element.value().attr("content") {
                        return Some(content.trim().to_string());
                    }
                } else {
                    let text: String = element
                        .text()
                        .collect::<Vec<_>>()
                        .join(" ")
                        .trim()
                        .to_string();
                    if !text.is_empty() && text.len() > 10 {
                        // Only return if meaningful length
                        return Some(text);
                    }
                }
            }
        }
    }

    None
}

/// Extract date from HTML
fn extract_date(html: &str) -> Option<String> {
    use scraper::{Html, Selector};

    let document = Html::parse_document(html);

    // Try common date selectors
    let selectors = vec![
        ".date",
        ".event-date",
        "time",
        "[data-date]",
        ".timestamp",
    ];

    for selector_str in selectors {
        if let Ok(selector) = Selector::parse(selector_str) {
            if let Some(element) = document.select(&selector).next() {
                if selector_str == "time" {
                    if let Some(datetime) = element.value().attr("datetime") {
                        return Some(datetime.to_string());
                    }
                } else if selector_str.contains("[data-date]") {
                    if let Some(date_attr) = element.value().attr("data-date") {
                        return Some(date_attr.to_string());
                    }
                }

                let text: String = element.text().collect::<String>().trim().to_string();
                if !text.is_empty() {
                    return Some(text);
                }
            }
        }
    }

    None
}
