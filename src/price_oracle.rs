use serde::Deserialize;
use chrono::Utc;

#[derive(Debug, Deserialize, Clone)]
pub struct CoinGeckoPrice {
    pub bitcoin: PriceData,
    pub solana: Option<PriceData>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct PriceData {
    pub usd: f64,
}

pub struct PriceOracle {
    api_key: String,
    client: reqwest::Client,
}

impl PriceOracle {
    pub fn new(api_key: String) -> Self {
        PriceOracle {
            api_key,
            client: reqwest::Client::new(),
        }
    }

    /// Fetch current Bitcoin price from CoinGecko API
    pub async fn fetch_btc_price(&self) -> Result<f64, Box<dyn std::error::Error>> {
        let url = format!(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&x_cg_pro_api_key={}",
            self.api_key
        );

        let response = self.client.get(&url).send().await?;
        let data: serde_json::Value = response.json().await?;

        if let Some(btc_price) = data.get("bitcoin").and_then(|b| b.get("usd")).and_then(|p| p.as_f64()) {
            println!("✅ CoinGecko BTC Price: ${:.2}", btc_price);
            Ok(btc_price)
        } else {
            Err("Failed to parse Bitcoin price from CoinGecko response".into())
        }
    }

    /// Fetch current Solana price from CoinGecko API
    pub async fn fetch_sol_price(&self) -> Result<f64, Box<dyn std::error::Error>> {
        let url = format!(
            "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd&x_cg_pro_api_key={}",
            self.api_key
        );

        let response = self.client.get(&url).send().await?;
        let data: serde_json::Value = response.json().await?;

        if let Some(sol_price) = data.get("solana").and_then(|s| s.get("usd")).and_then(|p| p.as_f64()) {
            println!("✅ CoinGecko SOL Price: ${:.2}", sol_price);
            Ok(sol_price)
        } else {
            Err("Failed to parse Solana price from CoinGecko response".into())
        }
    }

    /// Fetch both prices at once
    pub async fn fetch_prices(&self) -> Result<(f64, f64), Box<dyn std::error::Error>> {
        let btc = self.fetch_btc_price().await?;
        let sol = self.fetch_sol_price().await?;
        Ok((btc, sol))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_price_oracle_creation() {
        let oracle = PriceOracle::new("test_key".to_string());
        assert_eq!(oracle.api_key, "test_key");
    }
}
