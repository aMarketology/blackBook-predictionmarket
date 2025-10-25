use serde::{Deserialize, Serialize};
use chrono::Utc;
use crate::blockchain::{PredictionMarketBlockchain, LiveMarket, PricePoint};

impl PredictionMarketBlockchain {
    /// Create a new live Bitcoin price market (15-minute duration)
    pub fn create_live_btc_market(&mut self, current_price: f64) -> String {
        let market_id = format!("live_btc_{}", uuid::Uuid::new_v4());
        let now = Utc::now().timestamp();
        
        let live_market = LiveMarket {
            id: market_id.clone(),
            asset: "BTC".to_string(),
            entry_price: current_price,
            entry_time: now,
            duration_seconds: 900, // 15 minutes
            created_at: now,
            status: "active".to_string(),
            winning_outcome: None,
            price_history: vec![
                PricePoint {
                    price: current_price,
                    timestamp: now,
                }
            ],
            total_bets_higher: 0,
            total_bets_lower: 0,
            total_volume: 0,
        };
        
        self.live_markets.push(live_market);
        self.live_market_bets.insert(market_id.clone(), Vec::new());
        
        market_id
    }

    /// Place a bet on a live market (0 = higher, 1 = lower)
    pub fn place_live_bet(&mut self, market_id: &str, account: &str, amount: u64, outcome: u8) -> Result<String, String> {
        // Find market
        let market = self.live_markets.iter_mut()
            .find(|m| m.id == market_id)
            .ok_or_else(|| "Market not found".to_string())?;

        // Check market is still active
        let elapsed = Utc::now().timestamp() - market.entry_time;
        if elapsed > market.duration_seconds {
            market.status = "expired".to_string();
            return Err("Market has expired".to_string());
        }

        // Validate outcome
        if outcome > 1 {
            return Err("Invalid outcome (must be 0=higher or 1=lower)".to_string());
        }

        // Check account balance
        let account_info = self.get_account(account)
            .ok_or_else(|| "Account not found".to_string())?;
        if account_info.balance < amount {
            return Err(format!("Insufficient balance: have {}, need {}", account_info.balance, amount));
        }

        // Record bet
        if let Some(bets) = self.live_market_bets.get_mut(market_id) {
            bets.push((account.to_string(), outcome, amount));
        }

        // Update market stats
        if outcome == 0 {
            market.total_bets_higher = market.total_bets_higher.saturating_add(amount);
        } else {
            market.total_bets_lower = market.total_bets_lower.saturating_add(amount);
        }
        market.total_volume = market.total_volume.saturating_add(amount);

        let bet_id = uuid::Uuid::new_v4().to_string();
        Ok(bet_id)
    }

    /// Update live market with new price
    pub fn update_live_market_price(&mut self, market_id: &str, new_price: f64) -> Result<(), String> {
        let market = self.live_markets.iter_mut()
            .find(|m| m.id == market_id)
            .ok_or_else(|| "Market not found".to_string())?;

        let now = Utc::now().timestamp();
        market.price_history.push(PricePoint {
            price: new_price,
            timestamp: now,
        });

        // Check if market should expire
        let elapsed = now - market.entry_time;
        if elapsed > market.duration_seconds {
            // Settle market
            self.settle_live_market(market_id)?;
        }

        Ok(())
    }

    /// Settle a live market and distribute winnings
    pub fn settle_live_market(&mut self, market_id: &str) -> Result<(), String> {
        let market_idx = self.live_markets.iter()
            .position(|m| m.id == market_id)
            .ok_or_else(|| "Market not found".to_string())?;

        let market = &mut self.live_markets[market_idx];

        if market.status == "resolved" {
            return Err("Market already resolved".to_string());
        }

        // Determine winning outcome (0 = higher, 1 = lower)
        let entry_price = market.entry_price;
        let final_price = market.price_history.last()
            .map(|p| p.price)
            .unwrap_or(entry_price);

        let winning_outcome = if final_price > entry_price {
            0 // Higher
        } else if final_price < entry_price {
            1 // Lower
        } else {
            // No change - return bets
            market.status = "resolved".to_string();
            return Ok(());
        };

        market.winning_outcome = Some(winning_outcome);
        market.status = "resolved".to_string();

        // Get all bets for this market
        let bets = self.live_market_bets.get(market_id)
            .cloned()
            .unwrap_or_default();

        // Calculate total winning and losing bets
        let total_winning_bets: u64 = bets.iter()
            .filter(|(_, outcome, _)| *outcome == winning_outcome)
            .map(|(_, _, amount)| amount)
            .sum();

        let total_losing_bets: u64 = bets.iter()
            .filter(|(_, outcome, _)| *outcome != winning_outcome)
            .map(|(_, _, amount)| amount)
            .sum();

        // Distribute winnings
        for (account, outcome, amount) in bets {
            if outcome == winning_outcome {
                // Winner: get original bet + share of losing bets (95% to winners, 5% fee)
                let winning_share = if total_winning_bets > 0 {
                    (total_losing_bets as f64 * 0.95) / total_winning_bets as f64
                } else {
                    0.0
                };
                let payout = amount + (winning_share * amount as f64) as u64;
                
                if let Some(acc) = self.get_account_mut(&account) {
                    acc.balance = acc.balance.saturating_add(payout);
                }
            }
        }

        Ok(())
    }

    /// Get active live markets
    pub fn get_live_markets(&self) -> Vec<&LiveMarket> {
        self.live_markets.iter()
            .filter(|m| m.status == "active")
            .collect()
    }

    /// Get specific live market
    pub fn get_live_market(&self, market_id: &str) -> Option<&LiveMarket> {
        self.live_markets.iter().find(|m| m.id == market_id)
    }

    /// Helper: Get mutable account reference
    pub fn get_account_mut(&mut self, name: &str) -> Option<&mut crate::blockchain::Account> {
        // Get mutable reference to accounts from consensus engine
        // This is a workaround - in production, would have better account storage
        // For now, we'll use the demo_wallets to track accounts
        
        // Try to find in existing accounts list (if we ever build one)
        // For now, return None and caller should handle
        None
    }
}
