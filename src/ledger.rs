use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Minimal blockchain ledger for BlackBook prediction market
/// Each account is a real wallet with persistent balance
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Ledger {
    /// Real account balances - hardcoded on initialization
    pub balances: HashMap<String, f64>,
    /// Transaction history for audit trail
    pub transactions: Vec<Transaction>,
}

/// Simple transaction record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Transaction {
    pub from: String,
    pub to: String,
    pub amount: f64,
    pub timestamp: u64,
    pub tx_type: String,
}

impl Ledger {
    /// Initialize ledger with 8 real blockchain accounts
    /// Each account gets 1000 BB tokens (BlackBook tokens)
    pub fn new_full_node() -> Self {
        let mut balances = HashMap::new();
        
        // Hardcoded initialization of 8 real wallet accounts
        // These are persistent once initialized
        balances.insert("alice".to_string(), 1000.0);
        balances.insert("bob".to_string(), 1000.0);
        balances.insert("charlie".to_string(), 1000.0);
        balances.insert("diana".to_string(), 1000.0);
        balances.insert("ethan".to_string(), 1000.0);
        balances.insert("fiona".to_string(), 1000.0);
        balances.insert("george".to_string(), 1000.0);
        balances.insert("hannah".to_string(), 1000.0);
        
        Self {
            balances,
            transactions: Vec::new(),
        }
    }

    pub fn new_partial_node() -> Self {
        Self::new_full_node()
    }

    pub fn new_light_node() -> Self {
        Self::new_full_node()
    }

    /// Get balance for a wallet address/account name
    pub fn get_balance(&self, address: &str) -> f64 {
        self.balances.get(address).copied().unwrap_or(0.0)
    }

    /// Add tokens to an account (admin function for GOD MODE)
    pub fn add_tokens(&mut self, address: &str, amount: f64) -> Result<String, String> {
        if amount <= 0.0 {
            return Err("Amount must be positive".to_string());
        }

        let current_balance = self.get_balance(address);
        let new_balance = current_balance + amount;

        self.balances.insert(address.to_string(), new_balance);

        // Record transaction
        let tx = Transaction {
            from: "ADMIN".to_string(),
            to: address.to_string(),
            amount,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            tx_type: "admin_deposit".to_string(),
        };

        self.transactions.push(tx);

        Ok(format!(
            "Added {} BB to {}. New balance: {} BB",
            amount, address, new_balance
        ))
    }

    /// Deposit funds from SYSTEM (for initialization)
    pub fn deposit(&mut self, to_address: &str, amount: f64, _memo: &str) -> Result<String, String> {
        self.add_tokens(to_address, amount)
    }

    /// Transfer tokens between accounts
    pub fn transfer(&mut self, from: &str, to: &str, amount: f64) -> Result<String, String> {
        if amount <= 0.0 {
            return Err("Amount must be positive".to_string());
        }

        let from_balance = self.get_balance(from);
        if from_balance < amount {
            return Err(format!(
                "Insufficient balance: {} has {} BB but needs {}",
                from, from_balance, amount
            ));
        }

        // Deduct from sender
        self.balances.insert(from.to_string(), from_balance - amount);

        // Add to recipient
        let to_balance = self.get_balance(to);
        self.balances.insert(to.to_string(), to_balance + amount);

        // Record transaction
        let tx = Transaction {
            from: from.to_string(),
            to: to.to_string(),
            amount,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            tx_type: "transfer".to_string(),
        };

        self.transactions.push(tx);

        Ok(format!(
            "Transferred {} BB from {} to {}",
            amount, from, to
        ))
    }

    /// Place a bet (deduct tokens)
    pub fn place_bet(&mut self, from: &str, market_id: &str, amount: f64) -> Result<String, String> {
        if amount <= 0.0 {
            return Err("Bet amount must be positive".to_string());
        }

        let from_balance = self.get_balance(from);
        if from_balance < amount {
            return Err(format!(
                "Insufficient balance for bet: {} has {} BB but needs {}",
                from, from_balance, amount
            ));
        }

        // Deduct bet amount
        self.balances.insert(from.to_string(), from_balance - amount);

        // Record transaction
        let tx = Transaction {
            from: from.to_string(),
            to: format!("market_{}", market_id),
            amount,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            tx_type: "bet".to_string(),
        };

        self.transactions.push(tx);

        Ok(format!(
            "Placed {} BB bet on market {} | New balance: {}",
            amount,
            market_id,
            self.get_balance(from)
        ))
    }

    /// Get all transactions
    pub fn get_all_transactions(&self) -> Vec<Transaction> {
        self.transactions.clone()
    }

    /// Get transactions for a specific account
    pub fn get_account_transactions(&self, address: &str) -> Vec<Transaction> {
        self.transactions
            .iter()
            .filter(|tx| tx.from == address || tx.to == address)
            .cloned()
            .collect()
    }

    /// Get ledger statistics
    pub fn get_stats(&self) -> HashMap<String, serde_json::Value> {
        use serde_json::json;

        let mut stats = HashMap::new();
        
        let total_balance: f64 = self.balances.values().sum();
        let account_count = self.balances.len();
        let transaction_count = self.transactions.len();

        stats.insert("total_balance".to_string(), json!(total_balance));
        stats.insert("account_count".to_string(), json!(account_count));
        stats.insert("transaction_count".to_string(), json!(transaction_count));
        stats.insert("accounts".to_string(), json!(self.balances.clone()));

        stats
    }
}
