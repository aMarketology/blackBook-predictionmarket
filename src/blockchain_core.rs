use serde::{Deserialize, Serialize};
use sha2::{Sha256, Digest};
use std::fmt;
use chrono::{DateTime, Utc};

/// Core cryptographic utilities for the blockchain
pub mod crypto {
    use super::*;
    use secp256k1::{Secp256k1, SecretKey, PublicKey, Message, ecdsa::Signature};
    use rand::rngs::OsRng;
    use ripemd::Ripemd160;
    
    pub type Hash = [u8; 32];
    pub type Address = String;
    
    /// Generate a cryptographic hash of data
    pub fn hash(data: &[u8]) -> Hash {
        let mut hasher = Sha256::new();
        hasher.update(data);
        hasher.finalize().into()
    }
    
    /// Generate double SHA256 hash (Bitcoin-style)
    pub fn double_hash(data: &[u8]) -> Hash {
        hash(&hash(data))
    }
    
    /// Convert hash to hex string
    pub fn hash_to_hex(hash: &Hash) -> String {
        hex::encode(hash)
    }
    
    /// Generate a new keypair
    pub fn generate_keypair() -> (SecretKey, PublicKey) {
        let secp = Secp256k1::new();
        let (secret_key, public_key) = secp.generate_keypair(&mut OsRng);
        (secret_key, public_key)
    }
    
    /// Generate address from public key
    pub fn public_key_to_address(public_key: &PublicKey) -> Address {
        let serialized = public_key.serialize();
        let sha256_hash = hash(&serialized);
        let mut ripemd = Ripemd160::new();
        ripemd.update(&sha256_hash);
        let ripemd_hash = ripemd.finalize();
        format!("bb{}", hex::encode(&ripemd_hash[..20]))
    }
    
    /// Sign data with private key
    pub fn sign(secret_key: &SecretKey, data: &[u8]) -> Result<Signature, secp256k1::Error> {
        let secp = Secp256k1::new();
        let hash = hash(data);
        let message = Message::from_digest(hash);
        Ok(secp.sign_ecdsa(&message, secret_key))
    }
    
    /// Verify signature
    pub fn verify(public_key: &PublicKey, signature: &Signature, data: &[u8]) -> bool {
        let secp = Secp256k1::new();
        let hash = hash(data);
        let message = Message::from_digest(hash);
        secp.verify_ecdsa(&message, signature, public_key).is_ok()
    }
}

// Import Hash type for use in this module
use crypto::Hash;

/// Transaction input referencing previous outputs
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TransactionInput {
    pub previous_output: Hash,
    pub output_index: u32,
    pub script_sig: Vec<u8>, // Signature script
    pub sequence: u32,
}

/// Transaction output defining new ownership
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TransactionOutput {
    pub value: u64,
    pub script_pubkey: Vec<u8>, // Public key script
    pub address: crypto::Address,
}

/// Prediction market specific data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketData {
    pub market_id: String,
    pub title: String,
    pub description: String,
    pub outcomes: Vec<String>,
    pub end_time: DateTime<Utc>,
    pub creator: crypto::Address,
    pub resolution_source: String,
}

/// Betting transaction data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BetData {
    pub market_id: String,
    pub outcome_index: usize,
    pub amount: u64,
    pub odds: f64,
}

/// Transaction types specific to prediction markets
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TransactionType {
    Transfer {
        inputs: Vec<TransactionInput>,
        outputs: Vec<TransactionOutput>,
    },
    CreateMarket(MarketData),
    PlaceBet(BetData),
    ResolveMarket {
        market_id: String,
        winning_outcome: usize,
        proof: Vec<u8>,
    },
    ClaimWinnings {
        market_id: String,
        bet_ids: Vec<Hash>,
    },
}

/// Core transaction structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Transaction {
    pub id: Hash,
    pub version: u32,
    pub transaction_type: TransactionType,
    pub timestamp: DateTime<Utc>,
    pub fee: u64,
    pub signature: Option<Vec<u8>>,
    pub public_key: Option<Vec<u8>>,
}

impl Transaction {
    /// Create a new transaction
    pub fn new(transaction_type: TransactionType, fee: u64) -> Self {
        let mut tx = Self {
            id: [0; 32],
            version: 1,
            transaction_type,
            timestamp: Utc::now(),
            fee,
            signature: None,
            public_key: None,
        };
        tx.id = tx.calculate_hash();
        tx
    }
    
    /// Calculate transaction hash
    pub fn calculate_hash(&self) -> Hash {
        let mut tx_for_hash = self.clone();
        tx_for_hash.id = [0; 32];
        tx_for_hash.signature = None;
        
        let serialized = bincode::serialize(&tx_for_hash).unwrap_or_default();
        crypto::hash(&serialized)
    }
    
    /// Sign the transaction
    pub fn sign(&mut self, secret_key: &secp256k1::SecretKey, public_key: &secp256k1::PublicKey) -> Result<(), secp256k1::Error> {
        let tx_data = bincode::serialize(&self.transaction_type).unwrap_or_default();
        let signature = crypto::sign(secret_key, &tx_data)?;
        self.signature = Some(signature.serialize_compact().to_vec());
        self.public_key = Some(public_key.serialize().to_vec());
        self.id = self.calculate_hash();
        Ok(())
    }
    
    /// Verify transaction signature
    pub fn verify_signature(&self) -> bool {
        if let (Some(sig_bytes), Some(pub_key_bytes)) = (&self.signature, &self.public_key) {
            if let (Ok(signature), Ok(public_key)) = (
                secp256k1::ecdsa::Signature::from_compact(sig_bytes),
                secp256k1::PublicKey::from_slice(pub_key_bytes)
            ) {
                let tx_data = bincode::serialize(&self.transaction_type).unwrap_or_default();
                return crypto::verify(&public_key, &signature, &tx_data);
            }
        }
        false
    }
}

/// Merkle tree for efficient transaction verification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MerkleTree {
    pub root: Hash,
    pub leaves: Vec<Hash>,
}

impl MerkleTree {
    /// Build Merkle tree from transaction hashes
    pub fn build(transaction_hashes: Vec<Hash>) -> Self {
        if transaction_hashes.is_empty() {
            return Self {
                root: [0; 32],
                leaves: vec![],
            };
        }
        
        let mut current_level = transaction_hashes.clone();
        
        while current_level.len() > 1 {
            let mut next_level = Vec::new();
            
            for chunk in current_level.chunks(2) {
                let combined = if chunk.len() == 2 {
                    [chunk[0], chunk[1]].concat()
                } else {
                    [chunk[0], chunk[0]].concat() // Duplicate if odd number
                };
                next_level.push(crypto::hash(&combined));
            }
            
            current_level = next_level;
        }
        
        Self {
            root: current_level[0],
            leaves: transaction_hashes,
        }
    }
}

/// Block header containing metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BlockHeader {
    pub version: u32,
    pub previous_block_hash: Hash,
    pub merkle_root: Hash,
    pub timestamp: DateTime<Utc>,
    pub difficulty_target: u32,
    pub nonce: u64,
    pub block_height: u64,
}

/// Complete block with header and transactions
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Block {
    pub header: BlockHeader,
    pub transactions: Vec<Transaction>,
    pub hash: Hash,
}

impl Block {
    /// Create a new block
    pub fn new(
        previous_block_hash: Hash,
        transactions: Vec<Transaction>,
        difficulty_target: u32,
        block_height: u64,
    ) -> Self {
        let transaction_hashes: Vec<Hash> = transactions.iter().map(|tx| tx.id).collect();
        let merkle_tree = MerkleTree::build(transaction_hashes);
        
        let header = BlockHeader {
            version: 1,
            previous_block_hash,
            merkle_root: merkle_tree.root,
            timestamp: Utc::now(),
            difficulty_target,
            nonce: 0,
            block_height,
        };
        
        let mut block = Self {
            header,
            transactions,
            hash: [0; 32],
        };
        
        block.hash = block.calculate_hash();
        block
    }
    
    /// Calculate block hash
    pub fn calculate_hash(&self) -> Hash {
        let serialized = bincode::serialize(&self.header).unwrap_or_default();
        crypto::double_hash(&serialized)
    }
    
    /// Mine the block by finding a valid nonce
    pub fn mine(&mut self) -> bool {
        // Use a much simpler target calculation to avoid overflow
        // Difficulty target represents number of leading zeros required
        let required_zeros = self.header.difficulty_target.min(16); // Cap at 16 for u64
        let target = u64::MAX >> required_zeros;
        
        for nonce in 0..u64::MAX {
            self.header.nonce = nonce;
            self.hash = self.calculate_hash();
            
            let hash_as_number = u64::from_be_bytes([
                self.hash[0], self.hash[1], self.hash[2], self.hash[3],
                self.hash[4], self.hash[5], self.hash[6], self.hash[7],
            ]);
            
            if hash_as_number < target {
                println!("Block mined! Nonce: {}, Hash: {}", nonce, crypto::hash_to_hex(&self.hash));
                return true;
            }
            
            // Print progress every 100,000 attempts
            if nonce % 100_000 == 0 {
                println!("Mining... tried {} nonces", nonce);
            }
        }
        
        false
    }
    
    /// Validate block structure and transactions
    pub fn validate(&self) -> bool {
        // Verify block hash
        if self.hash != self.calculate_hash() {
            println!("Invalid block hash");
            return false;
        }
        
        // Verify merkle root
        let transaction_hashes: Vec<Hash> = self.transactions.iter().map(|tx| tx.id).collect();
        let merkle_tree = MerkleTree::build(transaction_hashes);
        if self.header.merkle_root != merkle_tree.root {
            println!("Invalid merkle root");
            return false;
        }
        
        // Verify all transactions
        for transaction in &self.transactions {
            if !transaction.verify_signature() {
                println!("Invalid transaction signature: {}", crypto::hash_to_hex(&transaction.id));
                return false;
            }
        }
        
        true
    }
}

impl fmt::Display for Block {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "Block #{} - Hash: {} - Transactions: {} - Timestamp: {}",
            self.header.block_height,
            crypto::hash_to_hex(&self.hash),
            self.transactions.len(),
            self.header.timestamp.format("%Y-%m-%d %H:%M:%S UTC")
        )
    }
}