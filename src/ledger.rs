use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Minimal blockchain ledger for BlackBook prediction market
/// Each account is a real wallet with persistent balance
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Ledger {
    /// Mapping from display name -> wallet address (L1_... uppercase)
    pub accounts: HashMap<String, String>,

    /// Balances keyed by wallet address
    pub balances: HashMap<String, f64>,

    /// Transaction history for audit trail (stores addresses)
    pub transactions: Vec<Transaction>,
}

/// Simple transaction record (stores addresses in `from` and `to`)
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
    /// Each account gets a dynamically generated L1_<UUID> address
    /// Each account gets 1000 BB tokens (BlackBook tokens)
    pub fn new_full_node() -> Self {
        let mut accounts = HashMap::new();
        let mut balances = HashMap::new();

        // Display names for the 8 accounts
        let names = vec![
            "ALICE", "BOB", "CHARLIE", "DIANA", 
            "ETHAN", "FIONA", "GEORGE", "HANNAH"
        ];

        // Generate a dynamic L1_<UUID> address for each account
        for name in names {
            let uuid = uuid::Uuid::new_v4();
            // Format: L1_<32 HEX UPPERCASE>
            // Take the UUID hex (without hyphens) and uppercase it
            let hex_uuid = uuid.simple().to_string().to_uppercase();
            let address = format!("L1_{}", hex_uuid);

            accounts.insert(name.to_string(), address.clone());

            // Initialize each address with 1000 BB
            balances.insert(address, 1000.0);

            println!("✅ Generated account: {} -> {}", name, accounts.get(name).unwrap());
        }

        Self {
            accounts,
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

    /// Resolve an identifier (either display name like "ALICE" or an address) into an address string.
    /// If input matches a display name, returns its mapped address.
    /// Otherwise, assumes input is already an address and returns it unchanged.
    fn resolve_address(&self, id: &str) -> String {
        // Allow name matching case-insensitive-ish by matching uppercase keys
        if let Some(addr) = self.accounts.get(&id.to_uppercase()) {
            return addr.clone();
        }

        // If id is already an address we know (exists in balances), return it
        if self.balances.contains_key(id) {
            return id.to_string();
        }

        // Otherwise return id as-is (caller should ensure correctness)
        id.to_string()
    }

    /// Get balance for a wallet address or account name
    pub fn get_balance(&self, address_or_name: &str) -> f64 {
        let addr = self.resolve_address(address_or_name);
        *self.balances.get(&addr).unwrap_or(&0.0)
    }

    /// Add tokens to an account (admin function for GOD MODE)
    pub fn add_tokens(&mut self, address_or_name: &str, amount: f64) -> Result<String, String> {
        if amount <= 0.0 {
            return Err("Amount must be positive".to_string());
        }

        let addr = self.resolve_address(address_or_name);
        let current_balance = *self.balances.get(&addr).unwrap_or(&0.0);
        let new_balance = current_balance + amount;

        self.balances.insert(addr.clone(), new_balance);

        // Record transaction (addresses used)
        let tx = Transaction {
            from: "ADMIN".to_string(),
            to: addr.clone(),
            amount,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            tx_type: "admin_deposit".to_string(),
        };

        self.transactions.push(tx);

        Ok(format!(
            "Added {} BB to {} ({}). New balance: {} BB",
            amount, address_or_name, addr, new_balance
        ))
    }

    /// Deposit funds from SYSTEM (for initialization)
    pub fn deposit(&mut self, to_address_or_name: &str, amount: f64, _memo: &str) -> Result<String, String> {
        self.add_tokens(to_address_or_name, amount)
    }

    /// Transfer tokens between accounts (accepts names or addresses)
    pub fn transfer(&mut self, from_or_name: &str, to_or_name: &str, amount: f64) -> Result<String, String> {
        if amount <= 0.0 {
            return Err("Amount must be positive".to_string());
        }

        let from_addr = self.resolve_address(from_or_name);
        let to_addr = self.resolve_address(to_or_name);

        let from_balance = *self.balances.get(&from_addr).unwrap_or(&0.0);
        if from_balance < amount {
            return Err(format!(
                "Insufficient balance: {} has {} BB but needs {}",
                from_or_name, from_balance, amount
            ));
        }

        // Deduct from sender
        self.balances.insert(from_addr.clone(), from_balance - amount);

        // Add to recipient
        let to_balance = *self.balances.get(&to_addr).unwrap_or(&0.0);
        self.balances.insert(to_addr.clone(), to_balance + amount);

        // Record transaction
        let tx = Transaction {
            from: from_addr.clone(),
            to: to_addr.clone(),
            amount,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            tx_type: "transfer".to_string(),
        };

        self.transactions.push(tx);

        Ok(format!(
            "Transferred {} BB from {} ({}) to {} ({})",
            amount, from_or_name, from_addr, to_or_name, to_addr
        ))
    }

    /// Place a bet (deduct tokens). `market_id` is stored as recipient address "market_<id>"
    pub fn place_bet(&mut self, from_or_name: &str, market_id: &str, amount: f64) -> Result<String, String> {
        if amount <= 0.0 {
            return Err("Bet amount must be positive".to_string());
        }

        let from_addr = self.resolve_address(from_or_name);
        let from_balance = *self.balances.get(&from_addr).unwrap_or(&0.0);
        if from_balance < amount {
            return Err(format!(
                "Insufficient balance for bet: {} has {} BB but needs {}",
                from_or_name, from_balance, amount
            ));
        }

        // Deduct bet amount
        self.balances.insert(from_addr.clone(), from_balance - amount);

        // Record transaction (to market pseudo-address)
        let tx = Transaction {
            from: from_addr.clone(),
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
            self.get_balance(&from_addr)
        ))
    }

    /// Get all transactions
    pub fn get_all_transactions(&self) -> Vec<Transaction> {
        self.transactions.clone()
    }

    /// Get transactions for a specific account (accepts name or address)
    pub fn get_account_transactions(&self, address_or_name: &str) -> Vec<Transaction> {
        let addr = self.resolve_address(address_or_name);
        self.transactions
            .iter()
            .filter(|tx| tx.from == addr || tx.to == addr)
            .cloned()
            .collect()
    }

    /// Get ledger statistics
    pub fn get_stats(&self) -> HashMap<String, serde_json::Value> {
        use serde_json::json;

        let mut stats = HashMap::new();

        let total_balance: f64 = self.balances.values().sum();
        let account_count = self.accounts.len();
        let transaction_count = self.transactions.len();

        stats.insert("total_balance".to_string(), json!(total_balance));
        stats.insert("account_count".to_string(), json!(account_count));
        stats.insert("transaction_count".to_string(), json!(transaction_count));
        stats.insert("accounts".to_string(), json!(self.accounts.clone()));
        stats.insert("balances".to_string(), json!(self.balances.clone()));

        stats
    }
}