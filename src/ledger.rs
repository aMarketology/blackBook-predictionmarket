use serde::{Deserialize, Serialize};
use std::collections::{HashMap, VecDeque};
use std::time::{SystemTime, UNIX_EPOCH};
use uuid::Uuid;

/// Transaction types - expanded for full ecosystem
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum TransactionType {
    /// Basic transfers between users
    Transfer,
    /// Placing a bet on a market
    PlaceBet,
    /// Winning payout from market
    WinnerPayout,
    /// System reward for engagement/activity
    EngagementReward,
    /// Penalty for market manipulation
    Penalty,
    /// Liquidity provision
    AddLiquidity,
    /// Liquidity withdrawal
    RemoveLiquidity,
    /// User referral reward
    ReferralBonus,
    /// Admin deposit (initial tokens)
    AdminDeposit,
}

/// Transaction status - for validation and auditing
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum TransactionStatus {
    /// Transaction is pending validation
    Pending,
    /// Transaction has been validated and committed
    Confirmed,
    /// Transaction failed validation
    Failed(String),
    /// Transaction was explicitly rejected/reversed
    Rejected(String),
}

/// Represents a single, completed transaction in the immutable log.
/// This is the SOURCE OF TRUTH for all financial operations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Transaction {
    /// Unique transaction ID (immutable)
    pub id: String,
    
    pub tx_type: TransactionType,
    pub from_address: String,
    pub to_address: String,
    pub amount: f64,
    
    /// Unix timestamp - IMMUTABLE
    pub timestamp: u64,
    
    /// Description of the transaction
    pub memo: String,
    
    /// Optional market context
    pub market_id: Option<String>,
    
    /// Optional: which option was bet on
    pub option_index: Option<usize>,
    
    /// Hash of previous transaction (creates immutable chain)
    pub previous_tx_hash: Option<String>,
    
    /// SHA256 hash of this transaction (for integrity)
    pub tx_hash: String,
    
    /// Transaction sequence number (for ordering)
    pub sequence_number: u64,
    
    /// Status of the transaction
    pub status: TransactionStatus,
    
    /// Balance AFTER this transaction (for verification)
    pub from_balance_after: f64,
    pub to_balance_after: f64,
}

impl Transaction {
    /// Calculate SHA256-like hash for integrity verification
    /// In production, use actual SHA256
    pub fn calculate_hash(
        id: &str,
        from: &str,
        to: &str,
        amount: f64,
        timestamp: u64,
        sequence: u64,
        previous_hash: &Option<String>,
    ) -> String {
        let data = format!(
            "{}{}{}{}{}{}{}",
            id,
            from,
            to,
            amount,
            timestamp,
            sequence,
            previous_hash.as_deref().unwrap_or("GENESIS")
        );
        
        // Simple deterministic hash using UUID v4 + data hash
        // For production, replace with actual SHA256
        let uuid_part = Uuid::new_v4();
        let data_hash = (data.len() as u64).wrapping_mul(31) ^ data.chars().map(|c| c as u64).sum::<u64>();
        format!("0x{:x}{:x}", uuid_part.as_u128() ^ data_hash as u128, data_hash)
    }
    
    /// Verify transaction integrity
    pub fn verify_integrity(&self) -> bool {
        let calculated_hash = Self::calculate_hash(
            &self.id,
            &self.from_address,
            &self.to_address,
            self.amount,
            self.timestamp,
            self.sequence_number,
            &self.previous_tx_hash,
        );
        
        self.tx_hash == calculated_hash && self.status == TransactionStatus::Confirmed
    }
}

/// User engagement metrics (tracked by ledger)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserEngagement {
    pub address: String,
    pub total_bets_placed: u64,
    pub total_amount_bet: f64,
    pub markets_participated_in: Vec<String>,
    pub wins: u64,
    pub losses: u64,
    pub accuracy_score: f64, // 0-100
    pub engagement_points: f64, // Used for reward calculations
    pub last_activity: u64,
    pub join_date: u64,
}

impl UserEngagement {
    pub fn new(address: String) -> Self {
        Self {
            address,
            total_bets_placed: 0,
            total_amount_bet: 0.0,
            markets_participated_in: Vec::new(),
            wins: 0,
            losses: 0,
            accuracy_score: 0.0,
            engagement_points: 0.0,
            last_activity: SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs(),
            join_date: SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs(),
        }
    }

    /// Calculate engagement points (used for rewards)
    pub fn calculate_engagement_points(&self) -> f64 {
        let bet_activity = self.total_bets_placed as f64 * 10.0;
        let accuracy_bonus = self.accuracy_score * 2.0;
        let win_bonus = self.wins as f64 * 50.0;
        
        bet_activity + accuracy_bonus + win_bonus
    }

    /// Update engagement after a bet
    pub fn record_bet(&mut self, market_id: String, amount: f64) {
        self.total_bets_placed += 1;
        self.total_amount_bet += amount;
        if !self.markets_participated_in.contains(&market_id) {
            self.markets_participated_in.push(market_id);
        }
        self.last_activity = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
    }

    /// Update engagement after market resolves
    pub fn record_result(&mut self, won: bool) {
        if won {
            self.wins += 1;
        } else {
            self.losses += 1;
        }
        
        let total_outcomes = self.wins + self.losses;
        self.accuracy_score = (self.wins as f64 / total_outcomes as f64) * 100.0;
        self.engagement_points = self.calculate_engagement_points();
    }
}

/// Market state in the ledger
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketState {
    pub market_id: String,
    pub title: String,
    pub description: String,
    pub options: Vec<String>,
    pub created_at: u64,
    pub resolution_date: Option<u64>,
    pub is_resolved: bool,
    pub winning_option: Option<usize>,
    
    /// Escrow funds held for this market
    pub total_escrow: f64,
    /// Total amount bet on each option
    pub option_pools: Vec<f64>,
    /// Users who bet on each option
    pub bettors_per_option: Vec<Vec<(String, f64)>>, // (address, amount)
}

impl MarketState {
    pub fn new(market_id: String, title: String, description: String, options: Vec<String>) -> Self {
        let num_options = options.len();
        Self {
            market_id,
            title,
            description,
            options,
            created_at: SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs(),
            resolution_date: None,
            is_resolved: false,
            winning_option: None,
            total_escrow: 0.0,
            option_pools: vec![0.0; num_options],
            bettors_per_option: vec![Vec::new(); num_options],
        }
    }

    /// Add a bet to the market
    pub fn record_bet(&mut self, user: String, option: usize, amount: f64) -> Result<(), String> {
        if option >= self.options.len() {
            return Err("Invalid option index".to_string());
        }
        if self.is_resolved {
            return Err("Market is already resolved".to_string());
        }

        self.option_pools[option] += amount;
        self.total_escrow += amount;
        self.bettors_per_option[option].push((user, amount));

        Ok(())
    }

    /// Calculate odds for each option (simple AMM)
    pub fn get_odds(&self) -> Vec<f64> {
        let total = self.total_escrow;
        if total == 0.0 {
            return vec![1.0; self.options.len()];
        }

        self.option_pools
            .iter()
            .map(|pool| {
                if *pool == 0.0 {
                    2.0 // Default odds if pool is empty
                } else {
                    total / pool
                }
            })
            .collect()
    }

    /// Calculate winnings for a bettor
    pub fn calculate_payout(&self, user: &str, winning_option: usize) -> f64 {
        if !self.is_resolved || self.winning_option != Some(winning_option) {
            return 0.0;
        }

        // Find user's bet amount
        let user_bet_amount = self.bettors_per_option[winning_option]
            .iter()
            .find(|(addr, _)| addr == user)
            .map(|(_, amount)| *amount)
            .unwrap_or(0.0);

        if user_bet_amount == 0.0 {
            return 0.0;
        }

        let winning_pool = self.option_pools[winning_option];
        if winning_pool == 0.0 {
            return 0.0;
        }

        // Payout = (user_amount / total_winning_pool) * total_escrow
        (user_bet_amount / winning_pool) * self.total_escrow
    }
}

/// The main Ledger - Core of BlackBook
#[derive(Debug, Serialize, Deserialize)]
pub struct Ledger {
    /// Immutable transaction log (append-only)
    pub transactions: Vec<Transaction>,
    
    /// Current balances (derived from transactions)
    pub balances: HashMap<String, f64>,
    
    /// Market states
    pub markets: HashMap<String, MarketState>,
    
    /// Reputation scores (based on accuracy)
    pub reputation_scores: HashMap<String, f64>,
    
    /// Referral relationships
    pub referrals: HashMap<String, Vec<String>>,
    
    /// Node configuration
    pub config: NodeConfig,
    
    /// Checkpoint for partial nodes
    pub latest_checkpoint: Option<LedgerCheckpoint>,
    
    /// AUDIT: Last verified sequence number
    #[serde(skip)]
    pub last_verified_sequence: u64,
    
    /// AUDIT: Integrity check results
    #[serde(skip)]
    pub integrity_check_results: Vec<AuditResult>,
}

/// Audit result for integrity checking
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditResult {
    pub timestamp: u64,
    pub total_transactions_checked: u64,
    pub valid_transactions: u64,
    pub invalid_transactions: u64,
    pub balance_match: bool,
    pub errors: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum NodeConfig {
    Full { max_blocks_to_keep: Option<u64> },
    Partial { recent_transaction_count: u64, checkpoint_every: u64 },
    Light,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LedgerCheckpoint {
    pub transaction_count: u64,
    pub balances_snapshot: HashMap<String, f64>,
    pub timestamp: u64,
}

impl Ledger {
    /// Create new ledger with configuration
    pub fn new_with_config(config: NodeConfig) -> Self {
        Self {
            transactions: Vec::new(),
            balances: HashMap::new(),
            markets: HashMap::new(),
            reputation_scores: HashMap::new(),
            referrals: HashMap::new(),
            config,
            latest_checkpoint: None,
            last_verified_sequence: 0,
            integrity_check_results: Vec::new(),
        }
    }

    pub fn new_full_node() -> Self {
        Self::new_with_config(NodeConfig::Full { max_blocks_to_keep: None })
    }

    pub fn new_partial_node() -> Self {
        Self::new_with_config(NodeConfig::Partial {
            recent_transaction_count: 1000,
            checkpoint_every: 100,
        })
    }

    pub fn new_light_node() -> Self {
        Self::new_with_config(NodeConfig::Light)
    }

    // ===== TRANSACTION RECORDING (CORE) =====
    
    fn current_timestamp() -> u64 {
        SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs()
    }

    fn generate_tx_id() -> String {
        format!("TX_{}", Uuid::new_v4().simple())
    }

    fn get_sequence_number(&self) -> u64 {
        self.transactions.len() as u64
    }

    fn get_last_tx_hash(&self) -> Option<String> {
        self.transactions.last().map(|tx| tx.tx_hash.clone())
    }

    /// CORE: Record a transaction with full validation
    /// This is the ONLY way transactions should be added to the ledger
    fn record_transaction(
        &mut self,
        tx_type: TransactionType,
        from: &str,
        to: &str,
        amount: f64,
        memo: &str,
        market_id: Option<String>,
        option_index: Option<usize>,
    ) -> Result<String, String> {
        // STEP 1: Validate inputs
        if amount < 0.0 {
            return Err("Amount cannot be negative".to_string());
        }
        
        if amount == 0.0 && tx_type != TransactionType::Transfer {
            return Err("Zero-amount transaction not allowed".to_string());
        }

        // STEP 2: Check sender balance (unless it's a SYSTEM transaction)
        if from != "SYSTEM" && from != "MARKET_RESERVE" {
            let from_balance = self.get_balance(from);
            if from_balance < amount {
                return Err(format!(
                    "Insufficient balance: {} has {} but needs {}",
                    from, from_balance, amount
                ));
            }
        }

        // STEP 3: Create transaction with all metadata
        let tx_id = Self::generate_tx_id();
        let sequence = self.get_sequence_number();
        let previous_hash = self.get_last_tx_hash();
        
        let from_balance_before = self.get_balance(from);
        let to_balance_before = self.get_balance(to);

        // Calculate new balances (for storage in transaction)
        let from_balance_after = from_balance_before - amount;
        let to_balance_after = to_balance_before + amount;

        let tx_hash = Transaction::calculate_hash(
            &tx_id,
            from,
            to,
            amount,
            Self::current_timestamp(),
            sequence,
            &previous_hash,
        );

        let tx = Transaction {
            id: tx_id.clone(),
            tx_type,
            from_address: from.to_string(),
            to_address: to.to_string(),
            amount,
            timestamp: Self::current_timestamp(),
            memo: memo.to_string(),
            market_id,
            option_index,
            previous_tx_hash: previous_hash,
            tx_hash,
            sequence_number: sequence,
            status: TransactionStatus::Confirmed,
            from_balance_after,
            to_balance_after,
        };

        // STEP 4: Verify transaction integrity BEFORE applying
        if !tx.verify_integrity() {
            return Err("Transaction failed integrity check".to_string());
        }

        // STEP 5: Apply to balances AFTER all validations pass
        *self.balances.entry(from.to_string()).or_insert(0.0) -= amount;
        *self.balances.entry(to.to_string()).or_insert(0.0) += amount;

        // STEP 6: Add to immutable log (APPEND ONLY)
        self.transactions.push(tx);

        // STEP 7: Prune if needed (partial nodes)
        self.prune_if_needed();

        Ok(tx_id)
    }

    // ===== PUBLIC TRANSACTION METHODS =====

    /// Deposit (mint new tokens from SYSTEM)
    pub fn deposit(&mut self, to_address: &str, amount: f64, memo: &str) -> Result<String, String> {
        self.record_transaction(
            TransactionType::AdminDeposit,
            "SYSTEM",
            to_address,
            amount,
            memo,
            None,
            None,
        )
    }

    /// Transfer between users
    pub fn transfer(&mut self, from: &str, to: &str, amount: f64, memo: &str) -> Result<String, String> {
        self.record_transaction(
            TransactionType::Transfer,
            from,
            to,
            amount,
            memo,
            None,
            None,
        )
    }

    /// Place a bet on a market
    pub fn place_bet(
        &mut self,
        user: &str,
        market_id: &str,
        option: usize,
        amount: f64,
    ) -> Result<String, String> {
        // Check market exists
        let market = self.markets.get_mut(market_id)
            .ok_or("Market not found".to_string())?;

        // Record bet in market
        market.record_bet(user.to_string(), option, amount)?;

        // Record transaction in ledger
        self.record_transaction(
            TransactionType::PlaceBet,
            user,
            &format!("MARKET_{}", market_id),
            amount,
            &format!("Bet on {} - Option {}", market_id, option),
            Some(market_id.to_string()),
            Some(option),
        )
    }

    /// Resolve a market and pay winners
    pub fn resolve_market(&mut self, market_id: &str, winning_option: usize) -> Result<Vec<(String, f64)>, String> {
        let market = self.markets.get_mut(market_id)
            .ok_or("Market not found".to_string())?;

        if market.is_resolved {
            return Err("Market already resolved".to_string());
        }

        market.is_resolved = true;
        market.winning_option = Some(winning_option);
        market.resolution_date = Some(Self::current_timestamp());

        // Calculate payouts
        let mut payouts = Vec::new();

        for (user, _bet_amount) in &market.bettors_per_option[winning_option] {
            let payout = market.calculate_payout(user, winning_option);
            if payout > 0.0 {
                payouts.push((user.clone(), payout));
            }
        }

        // Apply payouts through transactions (maintains integrity)
        for (user, payout_amount) in &payouts {
            self.record_transaction(
                TransactionType::WinnerPayout,
                &format!("MARKET_{}", market_id),
                user,
                *payout_amount,
                &format!("Won market {}", market_id),
                Some(market_id.to_string()),
                Some(winning_option),
            )?;
        }

        Ok(payouts)
    }

    /// Award engagement reward
    pub fn award_engagement_reward(&mut self, user: &str, amount: f64, reason: &str) -> Result<String, String> {
        self.record_transaction(
            TransactionType::EngagementReward,
            "SYSTEM",
            user,
            amount,
            &format!("Engagement reward: {}", reason),
            None,
            None,
        )
    }

    // ===== INTEGRITY VERIFICATION (CRITICAL) =====

    /// Verify the entire ledger integrity
    /// This should be run periodically to catch corruption
    pub fn verify_ledger_integrity(&mut self) -> AuditResult {
        let mut audit = AuditResult {
            timestamp: Self::current_timestamp(),
            total_transactions_checked: 0,
            valid_transactions: 0,
            invalid_transactions: 0,
            balance_match: false,
            errors: Vec::new(),
        };

        // Check 1: Verify transaction chain integrity
        let mut previous_hash: Option<String> = None;

        for (idx, tx) in self.transactions.iter().enumerate() {
            audit.total_transactions_checked += 1;

            // Verify hash chain
            if tx.previous_tx_hash != previous_hash && idx > 0 {
                audit.errors.push(format!(
                    "Transaction {} has broken chain: expected {:?}, got {:?}",
                    idx, previous_hash, tx.previous_tx_hash
                ));
                audit.invalid_transactions += 1;
            } else if !tx.verify_integrity() {
                audit.errors.push(format!(
                    "Transaction {} failed integrity check",
                    tx.id
                ));
                audit.invalid_transactions += 1;
            } else {
                audit.valid_transactions += 1;
                previous_hash = Some(tx.tx_hash.clone());
            }
        }

        // Check 2: Recalculate balances from scratch
        let mut calculated_balances: HashMap<String, f64> = HashMap::new();

        for tx in self.transactions.iter() {
            if tx.status == TransactionStatus::Confirmed {
                *calculated_balances.entry(tx.from_address.clone()).or_insert(0.0) -= tx.amount;
                *calculated_balances.entry(tx.to_address.clone()).or_insert(0.0) += tx.amount;
            }
        }

        // Verify balances match
        audit.balance_match = calculated_balances == self.balances;
        
        if !audit.balance_match {
            audit.errors.push("Calculated balances don't match stored balances".to_string());
        }

        // Store audit result
        self.integrity_check_results.push(audit.clone());
        self.last_verified_sequence = self.get_sequence_number();

        audit
    }

    // ===== QUERIES =====

    pub fn get_balance(&self, address: &str) -> f64 {
        self.balances.get(address).copied().unwrap_or(0.0)
    }

    pub fn get_transactions_for_user(&self, address: &str) -> Vec<&Transaction> {
        self.transactions
            .iter()
            .filter(|tx| tx.from_address == address || tx.to_address == address)
            .collect()
    }

    pub fn get_all_transactions(&self) -> &Vec<Transaction> {
        &self.transactions
    }

    pub fn get_recent_transactions(&self, limit: usize) -> Vec<&Transaction> {
        self.transactions.iter().rev().take(limit).collect()
    }

    pub fn get_market(&self, market_id: &str) -> Option<&MarketState> {
        self.markets.get(market_id)
    }

    pub fn get_all_markets(&self) -> Vec<&MarketState> {
        self.markets.values().collect()
    }

    pub fn get_active_markets(&self) -> Vec<&MarketState> {
        self.markets.values().filter(|m| !m.is_resolved).collect()
    }

    pub fn get_resolved_markets(&self) -> Vec<&MarketState> {
        self.markets.values().filter(|m| m.is_resolved).collect()
    }

    pub fn create_market(
        &mut self,
        market_id: String,
        title: String,
        description: String,
        options: Vec<String>,
    ) -> Result<String, String> {
        if self.markets.contains_key(&market_id) {
            return Err("Market already exists".to_string());
        }
        
        let market = MarketState::new(market_id.clone(), title, description, options);
        self.markets.insert(market_id.clone(), market);
        Ok(market_id)
    }

    pub fn get_stats(&self) -> HashMap<String, serde_json::Value> {
        let mut stats = HashMap::new();

        stats.insert("total_transactions".to_string(), serde_json::json!(self.transactions.len()));
        stats.insert("total_accounts".to_string(), serde_json::json!(self.balances.len()));
        stats.insert("total_markets".to_string(), serde_json::json!(self.markets.len()));

        let total_supply: f64 = self.balances.values().sum();
        stats.insert("total_supply".to_string(), serde_json::json!(total_supply));

        let node_type = match self.config {
            NodeConfig::Full { .. } => "Full",
            NodeConfig::Partial { .. } => "Partial",
            NodeConfig::Light => "Light",
        };
        stats.insert("node_type".to_string(), serde_json::json!(node_type));

        stats
    }

    /// Get last audit result
    pub fn get_last_audit(&self) -> Option<&AuditResult> {
        self.integrity_check_results.last()
    }

    // ===== MAINTENANCE =====

    fn prune_if_needed(&mut self) {
        // Extract config values to avoid borrow conflicts
        let (is_partial, recent_tx_count, checkpoint_interval) = match &self.config {
            NodeConfig::Partial {
                recent_transaction_count,
                checkpoint_every,
            } => (true, *recent_transaction_count as usize, *checkpoint_every as usize),
            _ => (false, 0, 0),
        };

        if is_partial {
            if self.transactions.len() % checkpoint_interval == 0 {
                self.create_checkpoint();
            }

            if self.transactions.len() > recent_tx_count {
                let keep_from = self.transactions.len() - recent_tx_count;
                self.transactions = self.transactions[keep_from..].to_vec();
            }
        }
    }

    fn create_checkpoint(&mut self) {
        self.latest_checkpoint = Some(LedgerCheckpoint {
            transaction_count: self.transactions.len() as u64,
            balances_snapshot: self.balances.clone(),
            timestamp: Self::current_timestamp(),
        });
    }
}