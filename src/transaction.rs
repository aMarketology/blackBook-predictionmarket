use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;
use chrono::{DateTime, Utc};

/// Simple transaction record for audit trail
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SimpleTransaction {
    pub id: String,
    pub action: String,        // "bet", "transfer", "add_balance" 
    pub account: String,       // Who did the action
    pub market: Option<String>, // Which market (if applicable)
    pub amount: u64,
    pub details: String,       // Human readable description
    pub timestamp: DateTime<Utc>,
    pub success: bool,
}

/// Transaction types for the prediction market
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum TransactionType {
    #[serde(rename = "deposit")]
    Deposit,
    #[serde(rename = "bet")]
    Bet,
    #[serde(rename = "payout")]
    Payout,
    #[serde(rename = "refund")]
    Refund,
    #[serde(rename = "withdrawal")]
    Withdrawal,
}

/// Transaction status on the blockchain
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum TransactionStatus {
    #[serde(rename = "pending")]
    Pending,
    #[serde(rename = "confirmed")]
    Confirmed,
    #[serde(rename = "failed")]
    Failed,
}

/// Complete transaction record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Transaction {
    pub id: String,
    pub tx_type: TransactionType,
    pub from_account: String,
    pub to_account: String, // or escrow address
    pub amount: u64,
    pub status: TransactionStatus,
    pub blockchain_tx_hash: Option<String>, // Hash from Layer 1 blockchain
    pub market_id: Option<String>,
    pub bet_id: Option<String>,
    pub created_at: DateTime<Utc>,
    pub confirmed_at: Option<DateTime<Utc>>,
    pub metadata: HashMap<String, String>, // Additional data (odds, outcome, etc.)
}

/// Simple transaction ledger - just logs everything
#[derive(Debug)]
pub struct SimpleLedger {
    transactions: Vec<SimpleTransaction>,
    account_history: HashMap<String, Vec<String>>, // account -> [tx_ids]
}

impl SimpleLedger {
    pub fn new() -> Self {
        Self {
            transactions: Vec::new(),
            account_history: HashMap::new(),
        }
    }

    /// Log a bet transaction
    pub fn log_bet(
        &mut self,
        account: &str,
        market: &str,
        outcome: usize,
        amount: u64,
        success: bool,
    ) -> String {
        let tx_id = Uuid::new_v4().to_string();
        let details = if success {
            format!("Bet {} BB on outcome {} in market '{}'", amount, outcome, market)
        } else {
            format!("FAILED bet {} BB on outcome {} in market '{}'", amount, outcome, market)
        };

        let tx = SimpleTransaction {
            id: tx_id.clone(),
            action: "bet".to_string(),
            account: account.to_string(),
            market: Some(market.to_string()),
            amount,
            details,
            timestamp: Utc::now(),
            success,
        };

        self.transactions.push(tx);
        
        // Index by account
        self.account_history
            .entry(account.to_string())
            .or_insert_with(Vec::new)
            .push(tx_id.clone());

        tx_id
    }

    /// Log a balance transfer
    pub fn log_transfer(
        &mut self,
        from: &str,
        to: &str,
        amount: u64,
        success: bool,
    ) -> String {
        let tx_id = Uuid::new_v4().to_string();
        let details = if success {
            format!("Transfer {} BB from {} to {}", amount, from, to)
        } else {
            format!("FAILED transfer {} BB from {} to {}", amount, from, to)
        };

        let tx = SimpleTransaction {
            id: tx_id.clone(),
            action: "transfer".to_string(),
            account: from.to_string(),
            market: None,
            amount,
            details,
            timestamp: Utc::now(),
            success,
        };

        self.transactions.push(tx);
        
        // Index by both accounts
        self.account_history
            .entry(from.to_string())
            .or_insert_with(Vec::new)
            .push(tx_id.clone());
        
        self.account_history
            .entry(to.to_string())
            .or_insert_with(Vec::new)
            .push(tx_id.clone());

        tx_id
    }

    /// Log adding balance to account (god mode)
    pub fn log_add_balance(
        &mut self,
        account: &str,
        amount: u64,
        success: bool,
    ) -> String {
        let tx_id = Uuid::new_v4().to_string();
        let details = if success {
            format!("God mode: Added {} BB to {}", amount, account)
        } else {
            format!("FAILED god mode: Add {} BB to {}", amount, account)
        };

        let tx = SimpleTransaction {
            id: tx_id.clone(),
            action: "add_balance".to_string(),
            account: account.to_string(),
            market: None,
            amount,
            details,
            timestamp: Utc::now(),
            success,
        };

        self.transactions.push(tx);
        
        self.account_history
            .entry(account.to_string())
            .or_insert_with(Vec::new)
            .push(tx_id.clone());

        tx_id
    }

    /// Get all transactions
    pub fn get_all_transactions(&self) -> &Vec<SimpleTransaction> {
        &self.transactions
    }

    /// Get transactions for a specific account
    pub fn get_account_transactions(&self, account: &str) -> Vec<&SimpleTransaction> {
        if let Some(tx_ids) = self.account_history.get(account) {
            tx_ids
                .iter()
                .filter_map(|id| self.transactions.iter().find(|tx| &tx.id == id))
                .collect()
        } else {
            Vec::new()
        }
    }

    /// Get recent transactions (last N)
    pub fn get_recent_transactions(&self, limit: usize) -> Vec<&SimpleTransaction> {
        self.transactions
            .iter()
            .rev()
            .take(limit)
            .collect()
    }

    /// Get transaction stats
    pub fn get_stats(&self) -> serde_json::Value {
        let total = self.transactions.len();
        let successful = self.transactions.iter().filter(|tx| tx.success).count();
        let failed = total - successful;

        let by_action: HashMap<String, usize> = {
            let mut map = HashMap::new();
            for tx in &self.transactions {
                *map.entry(tx.action.clone()).or_insert(0) += 1;
            }
            map
        };

        serde_json::json!({
            "total_transactions": total,
            "successful": successful,
            "failed": failed,
            "by_action": by_action,
            "total_volume": self.transactions.iter().map(|tx| tx.amount).sum::<u64>(),
            "unique_accounts": self.account_history.len()
        })
    }
}

/// Transaction ledger for auditing
#[derive(Debug)]
pub struct TransactionLedger {
    transactions: Vec<Transaction>,
    account_history: HashMap<String, Vec<String>>, // account -> [tx_ids]
    market_transactions: HashMap<String, Vec<String>>, // market_id -> [tx_ids]
}

impl TransactionLedger {
    pub fn new() -> Self {
        Self {
            transactions: Vec::new(),
            account_history: HashMap::new(),
            market_transactions: HashMap::new(),
        }
    }

    /// Record a new transaction
    pub fn record(
        &mut self,
        tx_type: TransactionType,
        from_account: &str,
        to_account: &str,
        amount: u64,
        market_id: Option<&str>,
    ) -> Transaction {
        let tx = Transaction {
            id: Uuid::new_v4().to_string(),
            tx_type,
            from_account: from_account.to_string(),
            to_account: to_account.to_string(),
            amount,
            status: TransactionStatus::Pending,
            blockchain_tx_hash: None,
            market_id: market_id.map(|m| m.to_string()),
            bet_id: None,
            created_at: Utc::now(),
            confirmed_at: None,
            metadata: HashMap::new(),
        };

        self.transactions.push(tx.clone());

        // Index by account
        self.account_history
            .entry(from_account.to_string())
            .or_insert_with(Vec::new)
            .push(tx.id.clone());

        self.account_history
            .entry(to_account.to_string())
            .or_insert_with(Vec::new)
            .push(tx.id.clone());

        // Index by market
        if let Some(mid) = market_id {
            self.market_transactions
                .entry(mid.to_string())
                .or_insert_with(Vec::new)
                .push(tx.id.clone());
        }

        tx
    }

    /// Confirm a transaction with blockchain hash
    pub fn confirm(
        &mut self,
        tx_id: &str,
        blockchain_tx_hash: &str,
    ) -> Result<Transaction, String> {
        let tx = self
            .transactions
            .iter_mut()
            .find(|t| t.id == tx_id)
            .ok_or("Transaction not found".to_string())?;

        tx.status = TransactionStatus::Confirmed;
        tx.blockchain_tx_hash = Some(blockchain_tx_hash.to_string());
        tx.confirmed_at = Some(Utc::now());

        Ok(tx.clone())
    }

    /// Mark transaction as failed
    pub fn fail(&mut self, tx_id: &str) -> Result<(), String> {
        let tx = self
            .transactions
            .iter_mut()
            .find(|t| t.id == tx_id)
            .ok_or("Transaction not found".to_string())?;

        tx.status = TransactionStatus::Failed;
        Ok(())
    }

    /// Get transaction details
    pub fn get(&self, tx_id: &str) -> Option<Transaction> {
        self.transactions.iter().find(|t| t.id == tx_id).cloned()
    }

    /// Get all transactions for an account
    pub fn get_account_history(&self, account: &str) -> Vec<Transaction> {
        self.account_history
            .get(account)
            .map(|tx_ids| {
                tx_ids
                    .iter()
                    .filter_map(|id| self.get(id))
                    .collect()
            })
            .unwrap_or_default()
    }

    /// Get all transactions for a market
    pub fn get_market_transactions(&self, market_id: &str) -> Vec<Transaction> {
        self.market_transactions
            .get(market_id)
            .map(|tx_ids| {
                tx_ids
                    .iter()
                    .filter_map(|id| self.get(id))
                    .collect()
            })
            .unwrap_or_default()
    }

    /// Get balance changes for an account
    pub fn get_account_balance(&self, account: &str) -> i64 {
        let history = self.get_account_history(account);
        let mut balance: i64 = 0;

        for tx in history {
            if tx.status != TransactionStatus::Confirmed {
                continue; // Only count confirmed transactions
            }

            if tx.from_account == account {
                balance -= tx.amount as i64;
            } else if tx.to_account == account {
                balance += tx.amount as i64;
            }
        }

        balance
    }

    /// Get pending transactions for an account
    pub fn get_pending_transactions(&self, account: &str) -> Vec<Transaction> {
        self.get_account_history(account)
            .into_iter()
            .filter(|tx| tx.status == TransactionStatus::Pending)
            .collect()
    }

    /// Get all transactions
    pub fn list_all(&self) -> Vec<Transaction> {
        self.transactions.clone()
    }

    /// Get transactions by type
    pub fn get_by_type(&self, tx_type: TransactionType) -> Vec<Transaction> {
        self.transactions
            .iter()
            .filter(|t| t.tx_type == tx_type)
            .cloned()
            .collect()
    }

    /// Export full ledger as JSON
    pub fn export(&self) -> serde_json::Value {
        serde_json::json!({
            "total_transactions": self.transactions.len(),
            "total_volume": self.transactions.iter().map(|t| t.amount).sum::<u64>(),
            "transactions": self.transactions,
            "by_type": {
                "deposits": self.get_by_type(TransactionType::Deposit).len(),
                "bets": self.get_by_type(TransactionType::Bet).len(),
                "payouts": self.get_by_type(TransactionType::Payout).len(),
                "refunds": self.get_by_type(TransactionType::Refund).len(),
                "withdrawals": self.get_by_type(TransactionType::Withdrawal).len(),
            }
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_record_transaction() {
        let mut ledger = TransactionLedger::new();
        let tx = ledger.record(
            TransactionType::Deposit,
            "alice",
            "escrow_market1",
            1000,
            Some("market_123"),
        );

        assert_eq!(tx.from_account, "alice");
        assert_eq!(tx.amount, 1000);
        assert_eq!(tx.status, TransactionStatus::Pending);
    }

    #[test]
    fn test_confirm_transaction() {
        let mut ledger = TransactionLedger::new();
        let tx = ledger.record(
            TransactionType::Deposit,
            "alice",
            "escrow_market1",
            1000,
            None,
        );

        let result = ledger.confirm(&tx.id, "0xabc123");
        assert!(result.is_ok());

        let confirmed_tx = ledger.get(&tx.id).unwrap();
        assert_eq!(confirmed_tx.status, TransactionStatus::Confirmed);
        assert_eq!(confirmed_tx.blockchain_tx_hash, Some("0xabc123".to_string()));
    }

    #[test]
    fn test_account_history() {
        let mut ledger = TransactionLedger::new();
        ledger.record(TransactionType::Deposit, "alice", "escrow", 1000, None);
        ledger.record(TransactionType::Bet, "alice", "escrow", 500, Some("market_1"));

        let history = ledger.get_account_history("alice");
        assert_eq!(history.len(), 2);
    }

    #[test]
    fn test_account_balance() {
        let mut ledger = TransactionLedger::new();
        let tx1 = ledger.record(TransactionType::Deposit, "alice", "escrow", 1000, None);
        let tx2 = ledger.record(TransactionType::Payout, "escrow", "alice", 2000, None);

        ledger.confirm(&tx1.id, "0x111").unwrap();
        ledger.confirm(&tx2.id, "0x222").unwrap();

        let balance = ledger.get_account_balance("alice");
        assert_eq!(balance, 1000); // +1000 deposit, -1000 from confirmation, +2000 payout = 1000
    }
}
