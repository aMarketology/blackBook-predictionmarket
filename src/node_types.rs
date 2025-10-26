use std::collections::HashMap;
use crate::ledger::Ledger;
use crate::market::PredictionMarket;

/// Different types of nodes in the network
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NodeType {
    /// Full node - stores complete ledger history, validates everything
    /// Storage: ~500 MB - 1 GB (grows with network)
    /// Validation: All transactions
    Full,
    
    /// Partial node - stores recent ledger history only
    /// Storage: ~50-100 MB (stays constant)
    /// Validation: Recent transactions + checkpoint validation
    Partial,
    
    /// Light node - minimal storage, for mobile
    /// Storage: ~5-10 MB
    /// Validation: Headers only, trusts full nodes
    Light,
}

/// Full node - stores and validates everything
pub struct FullNode {
    pub id: String,
    pub ledger: Ledger,
    pub markets: HashMap<String, PredictionMarket>,
    pub peers: Vec<String>,
    pub listen_port: u16,
}

impl FullNode {
    pub fn new(port: u16) -> Self {
        Self {
            id: uuid::Uuid::new_v4().to_string(),
            ledger: Ledger::new(),
            markets: HashMap::new(),
            peers: Vec::new(),
            listen_port: port,
        }
    }

    pub fn add_peer(&mut self, peer_address: String) {
        self.peers.push(peer_address);
    }

    pub fn get_node_info(&self) -> serde_json::Value {
        serde_json::json!({
            "node_type": "full",
            "node_id": self.id,
            "port": self.listen_port,
            "peers_count": self.peers.len(),
            "transactions_count": self.ledger.get_all_transactions().len(),
            "markets_count": self.markets.len(),
            "storage_size_mb": self.estimate_storage_mb(),
        })
    }

    fn estimate_storage_mb(&self) -> f64 {
        // Rough estimation: ~100 bytes per transaction, 1 KB per market
        let tx_size = (self.ledger.get_all_transactions().len() as f64) * 0.0001;
        let market_size = (self.markets.len() as f64) * 0.001;
        tx_size + market_size
    }
}

/// Partial node - stores recent history for efficiency
pub struct PartialNode {
    pub id: String,
    pub ledger: Ledger,
    pub markets: HashMap<String, PredictionMarket>,
    pub peers: Vec<String>,
    pub listen_port: u16,
    pub checkpoint: BlockCheckpoint,
    pub max_transactions: usize, // Keep only recent transactions
}

#[derive(Debug, Clone)]
pub struct BlockCheckpoint {
    pub block_height: u64,
    pub block_hash: String,
    pub timestamp: u64,
}

impl PartialNode {
    pub fn new(port: u16, max_transactions: usize) -> Self {
        Self {
            id: uuid::Uuid::new_v4().to_string(),
            ledger: Ledger::new(),
            markets: HashMap::new(),
            peers: Vec::new(),
            listen_port: port,
            checkpoint: BlockCheckpoint {
                block_height: 0,
                block_hash: "genesis".to_string(),
                timestamp: 0,
            },
            max_transactions,
        }
    }

    pub fn add_peer(&mut self, peer_address: String) {
        self.peers.push(peer_address);
    }

    /// Prune old transactions to maintain max_transactions limit
    pub fn prune_old_transactions(&mut self) {
        let tx_count = self.ledger.get_all_transactions().len();
        if tx_count > self.max_transactions {
            // In a real implementation, you'd remove the oldest transactions
            // For now, this is a placeholder
            println!("⚠️  Reached max transactions: {} > {}", tx_count, self.max_transactions);
        }
    }

    pub fn get_node_info(&self) -> serde_json::Value {
        serde_json::json!({
            "node_type": "partial",
            "node_id": self.id,
            "port": self.listen_port,
            "peers_count": self.peers.len(),
            "transactions_count": self.ledger.get_all_transactions().len(),
            "max_transactions": self.max_transactions,
            "markets_count": self.markets.len(),
            "checkpoint_block": self.checkpoint.block_height,
            "storage_size_mb": self.estimate_storage_mb(),
        })
    }

    fn estimate_storage_mb(&self) -> f64 {
        let tx_size = (self.ledger.get_all_transactions().len() as f64) * 0.0001;
        let market_size = (self.markets.len() as f64) * 0.001;
        tx_size + market_size
    }
}

/// Light node - minimal storage for mobile devices
pub struct LightNode {
    pub id: String,
    pub address: String,            // User's account address
    pub balance: f64,               // User's current balance
    pub private_key: String,        // User's private key (encrypted)
    pub peers: Vec<String>,
    pub listen_port: u16,
}

impl LightNode {
    pub fn new(address: String, port: u16) -> Self {
        Self {
            id: uuid::Uuid::new_v4().to_string(),
            address,
            balance: 0.0,
            private_key: String::new(), // Should be encrypted in real app
            peers: Vec::new(),
            listen_port: port,
        }
    }

    pub fn add_peer(&mut self, peer_address: String) {
        self.peers.push(peer_address);
    }

    pub fn get_node_info(&self) -> serde_json::Value {
        serde_json::json!({
            "node_type": "light",
            "node_id": self.id,
            "address": self.address,
            "balance": self.balance,
            "peers_count": self.peers.len(),
            "storage_size_mb": 0.01, // ~10 MB max
        })
    }
}
