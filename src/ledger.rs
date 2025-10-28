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

    /// Platform Activity Recipes - comprehensive record of all activities
    pub recipes: Vec<Recipe>,
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

/// Platform Activity Recipe - comprehensive record of all blockchain activities
/// Serves as a "receipt book" for the platform ledger
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Recipe {
    /// Unique recipe ID
    pub id: String,

    /// Recipe type: bet_placed, bet_win, bet_loss, transfer, deposit, withdrawal, admin_action
    pub recipe_type: String,

    /// Account that performed/affected by action
    pub account: String,

    /// Account address (L1_...)
    pub address: String,

    /// Amount involved (in BB tokens)
    pub amount: f64,

    /// Description of the activity
    pub description: String,

    /// Related market/bet ID if applicable
    pub related_id: Option<String>,

    /// Timestamp of activity
    pub timestamp: u64,

    /// Additional metadata
    pub metadata: HashMap<String, String>,
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
            recipes: Vec::new(),
        }
    }

    pub fn new_partial_node() -> Self {
        Self::new_full_node()
    }

    pub fn new_light_node() -> Self {
        Self::new_full_node()
    }

    /// Create a recipe record for platform activity
    fn create_recipe(
        &self,
        recipe_type: &str,
        account: &str,
        amount: f64,
        description: &str,
        related_id: Option<String>,
    ) -> Recipe {
        let addr = self.resolve_address(account);
        let recipe_id = format!("recipe_{}_{}_{}", recipe_type, account, uuid::Uuid::new_v4().simple());

        Recipe {
            id: recipe_id,
            recipe_type: recipe_type.to_string(),
            account: account.to_string(),
            address: addr,
            amount,
            description: description.to_string(),
            related_id,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            metadata: HashMap::new(),
        }
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

        // Record recipe
        let recipe = self.create_recipe(
            "admin_deposit",
            address_or_name,
            amount,
            &format!("Admin deposit of {} BB to {}", amount, address_or_name),
            None,
        );
        self.recipes.push(recipe);

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

        // Record recipe for sender
        let recipe_id = format!("transfer_{}_{}_{}", from_or_name, to_or_name, uuid::Uuid::new_v4().simple());
        let recipe = self.create_recipe(
            "transfer",
            from_or_name,
            amount,
            &format!("Transferred {} BB to {}", amount, to_or_name),
            Some(recipe_id.clone()),
        );
        self.recipes.push(recipe);

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

        // Record recipe
        let recipe = self.create_recipe(
            "bet_placed",
            from_or_name,
            amount,
            &format!("Placed {} BB bet on market {}", amount, market_id),
            Some(market_id.to_string()),
        );
        self.recipes.push(recipe);

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
        let recipe_count = self.recipes.len();

        stats.insert("total_balance".to_string(), json!(total_balance));
        stats.insert("account_count".to_string(), json!(account_count));
        stats.insert("transaction_count".to_string(), json!(transaction_count));
        stats.insert("recipe_count".to_string(), json!(recipe_count));
        stats.insert("accounts".to_string(), json!(self.accounts.clone()));
        stats.insert("balances".to_string(), json!(self.balances.clone()));

        stats
    }

    /// Get all platform activity recipes
    pub fn get_all_recipes(&self) -> Vec<Recipe> {
        self.recipes.clone()
    }

    /// Get recipes for a specific account (by name or address)
    pub fn get_account_recipes(&self, address_or_name: &str) -> Vec<Recipe> {
        let name_upper = address_or_name.to_uppercase();
        self.recipes
            .iter()
            .filter(|r| r.account.to_uppercase() == name_upper || r.address == address_or_name)
            .cloned()
            .collect()
    }

    /// Get recipes filtered by type (e.g., "bet_placed", "transfer", "admin_deposit")
    pub fn get_recipes_by_type(&self, recipe_type: &str) -> Vec<Recipe> {
        self.recipes
            .iter()
            .filter(|r| r.recipe_type == recipe_type)
            .cloned()
            .collect()
    }

    /// Get recipes for account filtered by type
    pub fn get_account_recipes_by_type(&self, address_or_name: &str, recipe_type: &str) -> Vec<Recipe> {
        let name_upper = address_or_name.to_uppercase();
        self.recipes
            .iter()
            .filter(|r| {
                (r.account.to_uppercase() == name_upper || r.address == address_or_name)
                    && r.recipe_type == recipe_type
            })
            .cloned()
            .collect()
    }

    /// Get all recipes sorted by timestamp (newest first)
    pub fn get_recipes_sorted(&self) -> Vec<Recipe> {
        let mut sorted = self.recipes.clone();
        sorted.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));
        sorted
    }

    /// Get recipes for account sorted by timestamp (newest first)
    pub fn get_account_recipes_sorted(&self, address_or_name: &str) -> Vec<Recipe> {
        let mut recipes = self.get_account_recipes(address_or_name);
        recipes.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));
        recipes
    }

    /// Record a bet win for an account
    pub fn record_bet_win(&mut self, address_or_name: &str, amount: f64, bet_id: &str) {
        let recipe = self.create_recipe(
            "bet_win",
            address_or_name,
            amount,
            &format!("Won {} BB on bet {}", amount, bet_id),
            Some(bet_id.to_string()),
        );
        self.recipes.push(recipe);
    }

    /// Record a bet loss for an account
    pub fn record_bet_loss(&mut self, address_or_name: &str, amount: f64, bet_id: &str) {
        let recipe = self.create_recipe(
            "bet_loss",
            address_or_name,
            amount,
            &format!("Lost {} BB on bet {}", amount, bet_id),
            Some(bet_id.to_string()),
        );
        self.recipes.push(recipe);
    }
}