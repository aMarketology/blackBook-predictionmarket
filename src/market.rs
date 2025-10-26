use serde::{Deserialize, Serialize};

/// Represents a prediction market
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PredictionMarket {
    pub id: String,
    pub title: String,
    pub description: String,
    pub options: Vec<String>,
    pub is_resolved: bool,
    pub winning_option: Option<usize>,
    pub escrow_address: String, // The market's escrow account for bets
    pub created_at: u64,
}

impl PredictionMarket {
    /// Create a new prediction market
    pub fn new(
        id: String,
        title: String,
        description: String,
        options: Vec<String>,
    ) -> Self {
        let escrow_address = format!("MARKET_{}", id);
        
        Self {
            id,
            title,
            description,
            options,
            is_resolved: false,
            winning_option: None,
            escrow_address,
            created_at: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
        }
    }

    /// Resolve the market with a winning option
    pub fn resolve(&mut self, winning_option: usize) -> Result<(), String> {
        if self.is_resolved {
            return Err("Market is already resolved".to_string());
        }

        if winning_option >= self.options.len() {
            return Err("Invalid option index".to_string());
        }

        self.is_resolved = true;
        self.winning_option = Some(winning_option);
        Ok(())
    }

    /// Check if market is still open for betting
    pub fn is_open(&self) -> bool {
        !self.is_resolved
    }
}
