use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};
use uuid::Uuid;

/// Represents a single, completed transaction in the immutable log.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Transaction {
    pub id: String, // Unique transaction ID (e.g., "TX_...")
    pub from_address: String, // Who sent it (or "SYSTEM" for rewards)
    pub to_address: String,   // Who received it
    pub amount: f64,
    pub timestamp: u64,
    pub memo: String, // "Proof of Engagement reward", "Bet on Market_XYZ", etc.
}

/// The main Ledger. This is the central source of truth for all balances.
/// Your main.rs will create ONE of these and hold onto it.
#[derive(Debug, Serialize, Deserialize)]
pub struct Ledger {
    /// The immutable, append-only log of all transactions.
    pub transactions: Vec<Transaction>,
    
    /// The "World State". A fast-lookup cache of current balances.
    /// This state is built by replaying all transactions.
    pub balances: HashMap<String, f64>,
}

impl Ledger {

    /// Creates a new, empty ledger.
    pub fn new() -> Self {
        Self {
            transactions: Vec::new(),
            balances: HashMap::new(),
        }
    }
    
    /// Helper to get the current time.
    fn current_timestamp() -> u64 {
        SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs()
    }

    /// Helper to create a unique transaction ID.
    fn generate_tx_id() -> String {
        format!("TX_{}", Uuid::new_v4().simple())
    }

    /// Gets the current balance for any address.
    pub fn get_balance(&self, address: &str) -> f64 {
        // .copied() gets the f64 value.
        // .unwrap_or(0.0) returns 0.0 if the address is not in the map.
        self.balances.get(address).copied().unwrap_or(0.0)
    }

    /// Gets all transactions for a specific user.
    pub fn get_transactions_for_user(&self, address: &str) -> Vec<&Transaction> {
        self.transactions
            .iter()
            .filter(|tx| tx.from_address == address || tx.to_address == address)
            .collect()
    }

    /// Gets all transactions (for audit trail).
    pub fn get_all_transactions(&self) -> &Vec<Transaction> {
        &self.transactions
    }

    /// Gets recent transactions (last N).
    pub fn get_recent_transactions(&self, limit: usize) -> Vec<&Transaction> {
        self.transactions
            .iter()
            .rev()
            .take(limit)
            .collect()
    }

    // --- Core Transaction Functions ---

    /// This is the function you asked for!
    /// It creates new tokens from nothing and gives them to a user.
    /// Used for "Proof of Engagement" rewards.
    pub fn deposit(&mut self, to_address: &str, amount: f64, memo: &str) -> String {
        let tx_id = Self::generate_tx_id();
        
        let tx = Transaction {
            id: tx_id.clone(),
            from_address: "SYSTEM".to_string(), // Rewards come from the "SYSTEM"
            to_address: to_address.to_string(),
            amount,
            timestamp: Self::current_timestamp(),
            memo: memo.to_string(),
        };

        // 1. Add to the immutable log
        self.transactions.push(tx);

        // 2. Update the current balance state
        let balance = self.balances.entry(to_address.to_string()).or_insert(0.0);
        *balance += amount;
        
        tx_id
    }

    /// Moves tokens from one user to another.
    /// This will be the main function for user-to-user payments.
    pub fn transfer(&mut self, from_address: &str, to_address: &str, amount: f64, memo: &str) -> Result<String, String> {
        // 1. Check if sender has enough funds
        let from_balance = self.get_balance(from_address);
        if from_balance < amount {
            return Err(format!("Insufficient funds: {} has {} but needs {}", from_address, from_balance, amount));
        }

        let tx_id = Self::generate_tx_id();
        let tx = Transaction {
            id: tx_id.clone(),
            from_address: from_address.to_string(),
            to_address: to_address.to_string(),
            amount,
            timestamp: Self::current_timestamp(),
            memo: memo.to_string(),
        };
        
        // 2. Add to the immutable log
        self.transactions.push(tx);

        // 3. Update the balances
        // We can safely .unwrap() here because we just checked the balance
        let from_balance_mut = self.balances.get_mut(from_address).unwrap();
        *from_balance_mut -= amount;
        
        let to_balance_mut = self.balances.entry(to_address.to_string()).or_insert(0.0);
        *to_balance_mut += amount;

        Ok(tx_id)
    }

    // --- Prediction Market Specific Functions ---

    /// A user places a bet by transferring funds to a market's escrow address.
    pub fn place_bet(&mut self, user_address: &str, market_address: &str, amount: f64) -> Result<String, String> {
        let memo = format!("Bet placed on market {}", market_address);
        self.transfer(user_address, market_address, amount, &memo)
    }

    /// The market pays out winnings from its escrow to a winner.
    pub fn payout_winnings(&mut self, market_address: &str, winner_address: &str, amount: f64) -> Result<String, String> {
        let memo = format!("Winnings paid from market {}", market_address);
        self.transfer(market_address, winner_address, amount, &memo)
    }

    /// Get ledger statistics for admin/debugging.
    pub fn get_stats(&self) -> HashMap<String, serde_json::Value> {
        let mut stats = HashMap::new();
        
        stats.insert("total_transactions".to_string(), 
            serde_json::Value::Number(serde_json::Number::from(self.transactions.len())));
        
        stats.insert("total_accounts".to_string(), 
            serde_json::Value::Number(serde_json::Number::from(self.balances.len())));
        
        let total_supply: f64 = self.balances.values().sum();
        stats.insert("total_supply".to_string(), 
            serde_json::Value::Number(serde_json::Number::from_f64(total_supply).unwrap_or(serde_json::Number::from(0))));
        
        stats
    }
}