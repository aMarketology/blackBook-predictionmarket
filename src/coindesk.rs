use serde::{Deserialize, Serialize};
use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};
use std::collections::HashMap;

// CoinGecko API response structures
#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct CoinGeckoPriceResponse {
    #[serde(flatten)]
    pub coins: HashMap<String, CoinPrice>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct CoinPrice {
    pub usd: f64,
}

// Live market structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LiveBTCMarket {
    pub market_id: String,
    pub asset: String,
    pub current_price: f64,
    pub entry_price: f64,
    pub entry_time: u64,
    pub remaining_seconds: u64,
    pub duration_seconds: u64,
    pub odds: PriceOdds,
    pub total_bets_higher: f64,
    pub total_bets_lower: f64,
    pub total_volume: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PriceOdds {
    pub higher: f64,
    pub lower: f64,
}

#[derive(Clone, Debug)]
pub struct CoinGeckoClient {
    current_markets: Arc<Mutex<HashMap<String, LiveBTCMarket>>>,
}

impl CoinGeckoClient {
    pub fn new() -> Self {
        Self {
            current_markets: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    /// Fetch current BTC price from CoinGecko API (real data)
    pub async fn get_bitcoin_price(&self) -> Result<f64, String> {
        let url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd";

        match reqwest::get(url).await {
            Ok(response) => {
                match response.json::<CoinGeckoPriceResponse>().await {
                    Ok(data) => {
                        if let Some(btc_data) = data.coins.get("bitcoin") {
                            let price = btc_data.usd;
                            println!("✅ CoinGecko BTC Price: ${:.2}", price);
                            Ok(price)
                        } else {
                            Err("Bitcoin data not found in response".to_string())
                        }
                    }
                    Err(e) => {
                        eprintln!("❌ Failed to deserialize CoinGecko response: {}", e);
                        Err(format!("Failed to parse response: {}", e))
                    }
                }
            }
            Err(e) => {
                eprintln!("❌ Failed to fetch from CoinGecko: {}", e);
                Err(format!("Failed to fetch BTC price: {}", e))
            }
        }
    }

    /// Fetch current SOL price from CoinGecko API (real data)
    pub async fn get_solana_price(&self) -> Result<f64, String> {
        let url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd";

        match reqwest::get(url).await {
            Ok(response) => {
                match response.json::<CoinGeckoPriceResponse>().await {
                    Ok(data) => {
                        if let Some(sol_data) = data.coins.get("solana") {
                            let price = sol_data.usd;
                            println!("✅ CoinGecko SOL Price: ${:.2}", price);
                            Ok(price)
                        } else {
                            Err("Solana data not found in response".to_string())
                        }
                    }
                    Err(e) => {
                        eprintln!("❌ Failed to deserialize CoinGecko response: {}", e);
                        Err(format!("Failed to parse response: {}", e))
                    }
                }
            }
            Err(e) => {
                eprintln!("❌ Failed to fetch from CoinGecko: {}", e);
                Err(format!("Failed to fetch SOL price: {}", e))
            }
        }
    }

    /// Create or update live BTC market
    pub async fn create_or_update_btc_market(&self) -> Result<LiveBTCMarket, String> {
        let current_price = self.get_bitcoin_price().await?;
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();

        let mut markets = self.current_markets.lock().unwrap();
        let key = "btc".to_string();

        // If no market exists or it expired, create new one
        let market_exists = markets.get(&key).map_or(false, |m| {
            now - m.entry_time < m.duration_seconds
        });

        if !market_exists {
            // Create new live market
            let market = LiveBTCMarket {
                market_id: format!("live_btc_{}", uuid::Uuid::new_v4()),
                asset: "BTC".to_string(),
                current_price,
                entry_price: current_price,
                entry_time: now,
                remaining_seconds: 900, // 15 minutes
                duration_seconds: 900,
                odds: calculate_odds(0.0, 0.0), // No bets yet
                total_bets_higher: 0.0,
                total_bets_lower: 0.0,
                total_volume: 0.0,
            };
            markets.insert(key.clone(), market);
        } else if let Some(m) = markets.get_mut(&key) {
            // Update existing market with new price
            m.current_price = current_price;
            m.remaining_seconds = m.duration_seconds.saturating_sub(now - m.entry_time);
            m.odds = calculate_odds(m.total_bets_higher, m.total_bets_lower);
        }

        Ok(markets.get(&key).unwrap().clone())
    }

    /// Create or update live SOL market
    pub async fn create_or_update_sol_market(&self) -> Result<LiveBTCMarket, String> {
        let current_price = self.get_solana_price().await?;
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();

        let mut markets = self.current_markets.lock().unwrap();
        let key = "sol".to_string();

        // If no market exists or it expired, create new one
        let market_exists = markets.get(&key).map_or(false, |m| {
            now - m.entry_time < m.duration_seconds
        });

        if !market_exists {
            // Create new live market
            let market = LiveBTCMarket {
                market_id: format!("live_sol_{}", uuid::Uuid::new_v4()),
                asset: "SOL".to_string(),
                current_price,
                entry_price: current_price,
                entry_time: now,
                remaining_seconds: 900, // 15 minutes
                duration_seconds: 900,
                odds: calculate_odds(0.0, 0.0), // No bets yet
                total_bets_higher: 0.0,
                total_bets_lower: 0.0,
                total_volume: 0.0,
            };
            markets.insert(key.clone(), market);
        } else if let Some(m) = markets.get_mut(&key) {
            // Update existing market with new price
            m.current_price = current_price;
            m.remaining_seconds = m.duration_seconds.saturating_sub(now - m.entry_time);
            m.odds = calculate_odds(m.total_bets_higher, m.total_bets_lower);
        }

        Ok(markets.get(&key).unwrap().clone())
    }

    /// Place a bet on a live market
    pub fn place_bet(&self, asset: &str, amount: f64, outcome: u8) -> Result<(), String> {
        if outcome > 1 {
            return Err("Invalid outcome: must be 0 (higher) or 1 (lower)".to_string());
        }

        let mut markets = self.current_markets.lock().unwrap();
        if let Some(market) = markets.get_mut(asset) {
            if outcome == 0 {
                market.total_bets_higher += amount;
            } else {
                market.total_bets_lower += amount;
            }
            market.total_volume += amount;
            market.odds = calculate_odds(market.total_bets_higher, market.total_bets_lower);
            Ok(())
        } else {
            Err(format!("No live market available for {}", asset))
        }
    }
}

/// Calculate dynamic odds based on betting volume
fn calculate_odds(bets_higher: f64, bets_lower: f64) -> PriceOdds {
    let total = bets_higher + bets_lower;

    if total == 0.0 {
        // No bets yet, default 50/50 odds
        return PriceOdds {
            higher: 0.5,
            lower: 0.5,
        };
    }

    // Adjust odds based on betting volume
    let higher_odds = bets_higher / total;
    let lower_odds = bets_lower / total;

    PriceOdds {
        higher: higher_odds,
        lower: lower_odds,
    }
}
