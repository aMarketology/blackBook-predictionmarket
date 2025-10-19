use crate::blockchain_core::*;
use crate::blockchain_core::crypto::*;
use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc, Duration};

/// Consensus parameters for the blockchain
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConsensusParams {
    pub target_block_time: Duration,        // Target time between blocks (e.g., 10 minutes)
    pub difficulty_adjustment_interval: u64, // Blocks between difficulty adjustments
    pub initial_difficulty: u32,            // Starting difficulty
    pub max_difficulty_change: f64,         // Maximum difficulty change per adjustment (e.g., 4x)
    pub block_reward: u64,                  // Mining reward per block
    pub halving_interval: u64,              // Blocks between reward halvings
}

impl Default for ConsensusParams {
    fn default() -> Self {
        Self {
            target_block_time: Duration::minutes(2),  // 2 minute blocks for faster testing
            difficulty_adjustment_interval: 144,       // Adjust every 144 blocks (~5 hours)
            initial_difficulty: 4,                   // Start with easy difficulty for testing
            max_difficulty_change: 4.0,
            block_reward: 5000_000_000, // 50 BB tokens (with 8 decimal places)
            halving_interval: 210_000,   // Halve rewards every 210k blocks
        }
    }
}

/// Mining statistics and state
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MiningStats {
    pub blocks_mined: u64,
    pub total_hash_rate: u64,
    pub current_difficulty: u32,
    pub last_block_time: DateTime<Utc>,
    pub average_block_time: Duration,
}

/// Consensus engine implementing Proof of Work
#[derive(Debug)]
pub struct ConsensusEngine {
    pub params: ConsensusParams,
    pub chain: Vec<Block>,
    pub pending_transactions: Vec<Transaction>,
    pub mining_stats: MiningStats,
    pub utxo_set: HashMap<Hash, TransactionOutput>, // Unspent transaction outputs
}

impl ConsensusEngine {
    /// Create a new consensus engine with genesis block
    pub fn new(params: ConsensusParams) -> Self {
        let mut engine = Self {
            params: params.clone(),
            chain: Vec::new(),
            pending_transactions: Vec::new(),
            mining_stats: MiningStats {
                blocks_mined: 0,
                total_hash_rate: 0,
                current_difficulty: params.initial_difficulty,
                last_block_time: Utc::now(),
                average_block_time: params.target_block_time,
            },
            utxo_set: HashMap::new(),
        };
        
        // Create and mine genesis block
        engine.create_genesis_block();
        engine
    }
    
    /// Create the genesis block
    fn create_genesis_block(&mut self) {
        // Genesis block has no previous hash
        let genesis_hash = [0; 32];
        
        // Create coinbase transaction for initial supply
        let coinbase_tx = Transaction::new(
            TransactionType::Transfer {
                inputs: vec![], // Genesis has no inputs
                outputs: vec![TransactionOutput {
                    value: 21_000_000 * 100_000_000, // 21M BB tokens initial supply
                    script_pubkey: vec![],
                    address: "bb_genesis_address".to_string(),
                }],
            },
            0, // No fee for genesis
        );
        
        let mut genesis_block = Block::new(
            genesis_hash,
            vec![coinbase_tx.clone()],
            self.params.initial_difficulty,
            0,
        );
        
        // Mine the genesis block
        println!("Mining genesis block...");
        genesis_block.mine();
        
        // Update UTXO set with genesis output
        self.utxo_set.insert(
            coinbase_tx.id,
            coinbase_tx.transaction_type.get_outputs()[0].clone(),
        );
        
        self.chain.push(genesis_block);
        self.mining_stats.blocks_mined = 1;
        println!("Genesis block created: {}", self.chain[0]);
    }
    
    /// Add a transaction to the pending pool
    pub fn add_transaction(&mut self, transaction: Transaction) -> Result<(), String> {
        // Validate transaction
        if !transaction.verify_signature() {
            return Err("Invalid transaction signature".to_string());
        }
        
        // Check for double spending
        if let TransactionType::Transfer { inputs, .. } = &transaction.transaction_type {
            for input in inputs {
                if !self.utxo_set.contains_key(&input.previous_output) {
                    return Err("Referenced output does not exist or already spent".to_string());
                }
            }
        }
        
        self.pending_transactions.push(transaction);
        Ok(())
    }
    
    /// Mine a new block
    pub fn mine_block(&mut self, miner_address: String) -> Result<Block, String> {
        if self.chain.is_empty() {
            return Err("No genesis block found".to_string());
        }
        
        let (previous_block_hash, block_height) = {
            let previous_block = self.chain.last().unwrap();
            (previous_block.hash, previous_block.header.block_height + 1)
        };
        
        // Create coinbase transaction (mining reward)
        let current_reward = self.calculate_block_reward(block_height);
        let coinbase_tx = Transaction::new(
            TransactionType::Transfer {
                inputs: vec![],
                outputs: vec![TransactionOutput {
                    value: current_reward,
                    script_pubkey: vec![],
                    address: miner_address,
                }],
            },
            0,
        );
        
        // Select transactions from pending pool
        let mut selected_transactions = vec![coinbase_tx];
        
        // Add pending transactions (simple selection for now)
        let max_transactions = 1000; // Block size limit
        for tx in self.pending_transactions.iter().take(max_transactions) {
            selected_transactions.push(tx.clone());
        }
        
        // Adjust difficulty if needed
        let current_difficulty = self.calculate_difficulty(block_height);
        
        // Create and mine the block
        let mut new_block = Block::new(
            previous_block_hash,
            selected_transactions,
            current_difficulty,
            block_height,
        );
        
        println!("Mining block #{} with difficulty {}...", block_height, current_difficulty);
        let mining_start = Utc::now();
        
        if new_block.mine() {
            let mining_time = Utc::now().signed_duration_since(mining_start);
            println!("Block mined in {:.2} seconds!", mining_time.num_milliseconds() as f64 / 1000.0);
            
            // Validate the new block
            if !new_block.validate() {
                return Err("Mined block failed validation".to_string());
            }
            
            // Update blockchain state
            self.add_block_to_chain(new_block.clone())?;
            
            // Remove mined transactions from pending pool
            self.pending_transactions.retain(|tx| {
                !new_block.transactions.iter().any(|block_tx| block_tx.id == tx.id)
            });
            
            // Update mining stats
            self.update_mining_stats(&new_block, mining_time);
            
            println!("Block #{} added to chain: {}", block_height, new_block);
            Ok(new_block)
        } else {
            Err("Failed to mine block".to_string())
        }
    }
    
    /// Add a mined block to the chain
    fn add_block_to_chain(&mut self, block: Block) -> Result<(), String> {
        // Validate block connects to chain
        if let Some(last_block) = self.chain.last() {
            if block.header.previous_block_hash != last_block.hash {
                return Err("Block does not connect to chain".to_string());
            }
        }
        
        // Update UTXO set
        for tx in &block.transactions {
            match &tx.transaction_type {
                TransactionType::Transfer { inputs, outputs } => {
                    // Remove spent outputs
                    for input in inputs {
                        self.utxo_set.remove(&input.previous_output);
                    }
                    
                    // Add new outputs
                    for (index, output) in outputs.iter().enumerate() {
                        self.utxo_set.insert(
                            hash(&[&tx.id[..], &(index as u32).to_be_bytes()].concat()),
                            output.clone(),
                        );
                    }
                }
                _ => {
                    // Handle other transaction types
                }
            }
        }
        
        self.chain.push(block);
        self.mining_stats.blocks_mined += 1;
        Ok(())
    }
    
    /// Calculate block reward with halving
    fn calculate_block_reward(&self, block_height: u64) -> u64 {
        let halvings = block_height / self.params.halving_interval;
        if halvings >= 64 {
            return 0; // No more rewards after 64 halvings
        }
        
        self.params.block_reward >> halvings
    }
    
    /// Calculate difficulty for next block
    fn calculate_difficulty(&mut self, block_height: u64) -> u32 {
        if block_height % self.params.difficulty_adjustment_interval != 0 {
            return self.mining_stats.current_difficulty;
        }
        
        if self.chain.len() < self.params.difficulty_adjustment_interval as usize {
            return self.mining_stats.current_difficulty;
        }
        
        // Calculate actual time for last difficulty period
        let blocks_back = self.params.difficulty_adjustment_interval as usize;
        let recent_block = &self.chain[self.chain.len() - 1];
        let old_block = &self.chain[self.chain.len() - blocks_back];
        
        let actual_time = recent_block.header.timestamp
            .signed_duration_since(old_block.header.timestamp);
        let target_time = self.params.target_block_time * blocks_back as i32;
        
        // Calculate difficulty adjustment
        let time_ratio = actual_time.num_seconds() as f64 / target_time.num_seconds() as f64;
        let difficulty_multiplier = 1.0 / time_ratio;
        
        // Clamp the adjustment to prevent extreme changes
        let clamped_multiplier = difficulty_multiplier
            .max(1.0 / self.params.max_difficulty_change)
            .min(self.params.max_difficulty_change);
        
        let new_difficulty = (self.mining_stats.current_difficulty as f64 * clamped_multiplier) as u32;
        let new_difficulty = new_difficulty.max(1).min(32); // Keep within reasonable bounds
        
        println!(
            "Difficulty adjustment: {} -> {} (time ratio: {:.2})",
            self.mining_stats.current_difficulty,
            new_difficulty,
            time_ratio
        );
        
        self.mining_stats.current_difficulty = new_difficulty;
        new_difficulty
    }
    
    /// Update mining statistics
    fn update_mining_stats(&mut self, block: &Block, mining_time: Duration) {
        self.mining_stats.last_block_time = block.header.timestamp;
        
        // Update average block time (simple moving average)
        let current_avg_ms = self.mining_stats.average_block_time.num_milliseconds();
        let new_time_ms = mining_time.num_milliseconds();
        let updated_avg_ms = (current_avg_ms * 9 + new_time_ms) / 10; // 10-block moving average
        self.mining_stats.average_block_time = Duration::milliseconds(updated_avg_ms);
    }
    
    /// Get blockchain info
    pub fn get_info(&self) -> BlockchainInfo {
        BlockchainInfo {
            chain_height: self.chain.len() as u64,
            best_block_hash: self.chain.last().map(|b| hash_to_hex(&b.hash)).unwrap_or_default(),
            difficulty: self.mining_stats.current_difficulty,
            pending_transactions: self.pending_transactions.len(),
            total_supply: self.calculate_total_supply(),
            average_block_time: self.mining_stats.average_block_time.num_seconds(),
        }
    }
    
    /// Get all transactions from the blockchain
    pub fn get_all_transactions(&self) -> Vec<&Transaction> {
        let mut all_txs = Vec::new();
        
        // Collect from all blocks
        for block in &self.chain {
            for tx in &block.transactions {
                all_txs.push(tx);
            }
        }
        
        // Add pending transactions
        for tx in &self.pending_transactions {
            all_txs.push(tx);
        }
        
        all_txs
    }
    
    /// Calculate total token supply
    fn calculate_total_supply(&self) -> u64 {
        self.utxo_set.values().map(|output| output.value).sum()
    }
    
    /// Get account balance
    pub fn get_balance(&self, address: &str) -> u64 {
        self.utxo_set
            .values()
            .filter(|output| output.address == address)
            .map(|output| output.value)
            .sum()
    }
}

/// Blockchain information summary
#[derive(Debug, Serialize, Deserialize)]
pub struct BlockchainInfo {
    pub chain_height: u64,
    pub best_block_hash: String,
    pub difficulty: u32,
    pub pending_transactions: usize,
    pub total_supply: u64,
    pub average_block_time: i64,
}

impl TransactionType {
    /// Get outputs from transaction type
    fn get_outputs(&self) -> Vec<TransactionOutput> {
        match self {
            TransactionType::Transfer { outputs, .. } => outputs.clone(),
            _ => vec![],
        }
    }
}