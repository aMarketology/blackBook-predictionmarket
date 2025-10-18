use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Account {
    pub name: String,
    pub address: String,
    pub balance: u64,
    pub private_key: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Market {
    pub id: String,
    pub title: String,
    pub description: String,
    pub outcomes: Vec<String>,
    pub odds: Vec<f64>,
    pub total_volume: u64,
    pub is_active: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Bet {
    pub id: String,
    pub account: String,
    pub market_id: String,
    pub outcome_index: usize,
    pub amount: u64,
    pub potential_payout: u64,
    pub timestamp: String,
}

#[derive(Debug, Clone)]
pub struct Blockchain {
    pub accounts: HashMap<String, Account>,
    pub markets: HashMap<String, Market>,
    pub bets: Vec<Bet>,
    pub total_supply: u64,
}

impl Blockchain {
    pub fn new() -> Self {
        let mut blockchain = Blockchain {
            accounts: HashMap::new(),
            markets: HashMap::new(),
            bets: Vec::new(),
            total_supply: 21000,
        };

        // Initialize 8 test accounts
        let test_accounts = vec![
            ("alice", "0x1111111111111111111111111111111111111111", 2625),
            ("bob", "0x2222222222222222222222222222222222222222", 2800),
            ("charlie", "0x3333333333333333333333333333333333333333", 2500),
            ("diana", "0x4444444444444444444444444444444444444444", 3000),
            ("eve", "0x5555555555555555555555555555555555555555", 2400),
            ("frank", "0x6666666666666666666666666666666666666666", 2700),
            ("grace", "0x7777777777777777777777777777777777777777", 2300),
            ("henry", "0x8888888888888888888888888888888888888888", 4675),
        ];

        for (name, address, balance) in test_accounts {
            blockchain.accounts.insert(name.to_string(), Account {
                name: name.to_string(),
                address: address.to_string(),
                balance,
                private_key: format!("{}1111111111111111111111111111111111111111111111111111111111111111", &address[2..3]),
            });
        }

        // Create sample tech markets
        blockchain.create_sample_markets();
        blockchain
    }

    fn create_sample_markets(&mut self) {
        // 20 real upcoming tech event markets with exact dates and details
        let markets = vec![
            // Samsung XR Headset (Oct 21, 2025)
            (
                "samsung_xr_4k",
                "Samsung Project Moohan offers 4K micro-OLED per eye",
                "Will Samsung's XR headset 'Project Moohan' (revealed Oct 21, 2025) offer 4K micro-OLED per eye?",
                vec!["Yes - 4K per eye".to_string(), "No - Lower resolution".to_string()],
                vec![2.1, 1.8],
            ),
            (
                "samsung_xr_q1_ship",
                "Samsung XR headset ships in Q1 2026",
                "Will Samsung's Project Moohan XR headset ship to consumers in Q1 2026?",
                vec!["Yes - Q1 2026".to_string(), "No - Later/Never".to_string()],
                vec![3.2, 1.3],
            ),
            // Web Summit 2025 (Nov 10-13, Lisbon)
            (
                "web_summit_ai_arch",
                "Major AI architecture announced at Web Summit 2025",
                "Will a major new AI architecture be announced at Web Summit 2025 (Nov 10-13, Lisbon)?",
                vec!["Yes - New architecture".to_string(), "No - No major AI news".to_string()],
                vec![4.5, 1.2],
            ),
            (
                "web_summit_attendance",
                "Web Summit 2025 surpasses prior year attendance",
                "Will Web Summit 2025 surpass attendance records from previous years?",
                vec!["Yes - Record attendance".to_string(), "No - Same or lower".to_string()],
                vec![1.9, 1.9],
            ),
            // GITEX Global 2025 (Dubai)
            (
                "gitex_ai_regulation",
                "New country commits to national AI regulation at GITEX 2025",
                "Will a new country commit to national AI regulation at GITEX Global 2025 in Dubai?",
                vec!["Yes - New commitment".to_string(), "No - No new commitments".to_string()],
                vec![2.8, 1.4],
            ),
            (
                "gitex_flying_car",
                "Major flying car prototype unveiled at GITEX 2025",
                "Will a major 'flying car' or urban air mobility prototype be unveiled at GITEX 2025?",
                vec!["Yes - Flying car demo".to_string(), "No - No flying cars".to_string()],
                vec![5.2, 1.15],
            ),
            // Gartner IT Symposium 2025 (Oct 20-23, Orlando)
            (
                "gartner_ai_dead",
                "Gartner declares 'AI hype is dead' at Symposium 2025",
                "Will Gartner declare AI is no longer hype in keynote at IT Symposium 2025 (Oct 20-23, Orlando)?",
                vec!["Yes - AI hype dead".to_string(), "No - AI still hyped".to_string()],
                vec![8.5, 1.1],
            ),
            (
                "gartner_xai_category",
                "Gartner launches new 'X-AI' category at Symposium 2025",
                "Will Gartner launch a new 'X-AI' (eXplainable AI) category at IT Symposium 2025?",
                vec!["Yes - New X-AI category".to_string(), "No - No X-AI category".to_string()],
                vec![3.8, 1.25],
            ),
            // AI Regulation Timeline
            (
                "us_ai_regulation_2026",
                "U.S. Congress passes major AI regulation by end 2026",
                "Will the U.S. Congress pass comprehensive AI regulation legislation by December 31, 2026?",
                vec!["Yes - Passes by 2026".to_string(), "No - Delayed/Fails".to_string()],
                vec![2.2, 1.7],
            ),
            (
                "eu_ai_rules_mid2026",
                "EU adopts new AI foundation model rules by mid-2026",
                "Will the EU adopt new AI rules specifically for foundation models by June 30, 2026?",
                vec!["Yes - New rules adopted".to_string(), "No - No new rules".to_string()],
                vec![1.8, 2.0],
            ),
            // Apple WWDC 2026
            (
                "apple_wwdc_arvr_2026",
                "Apple announces new AR/VR headset at WWDC 2026",
                "Will Apple announce a new AR/VR headset (Vision Pro successor) at WWDC 2026?",
                vec!["Yes - New headset".to_string(), "No - No headset".to_string()],
                vec![2.5, 1.5],
            ),
            (
                "ios20_generative_ai",
                "iOS 20 includes built-in generative AI",
                "Will iOS 20 (announced at WWDC 2026) include built-in generative AI capabilities?",
                vec!["Yes - Built-in gen AI".to_string(), "No - No gen AI".to_string()],
                vec![1.4, 2.9],
            ),
            // AI Safety Summit
            (
                "ai_safety_audits",
                "Country commits to enforceable AI model audits at next summit",
                "Will at least one country commit to enforceable audits of large AI models at the next AI safety summit?",
                vec!["Yes - Audit commitment".to_string(), "No - No commitments".to_string()],
                vec![3.1, 1.35],
            ),
            // Fusion/Energy Breakthrough
            (
                "fusion_net_output_2030",
                "Commercial fusion pilot achieves net output by 2030",
                "Will a commercial fusion pilot plant achieve net energy output by December 31, 2030?",
                vec!["Yes - Net fusion by 2030".to_string(), "No - Not by 2030".to_string()],
                vec![4.8, 1.18],
            ),
            (
                "carbon_capture_50_2026",
                "Carbon capture breakthrough under $50/ton announced in 2026",
                "Will a breakthrough in carbon capture technology (cost < $50/ton) be announced in 2026?",
                vec!["Yes - Under $50/ton".to_string(), "No - Still expensive".to_string()],
                vec![6.2, 1.14],
            ),
            // Quantum Computing Milestones
            (
                "quantum_1000_qubits_2026",
                "Quantum computer with >1,000 logical qubits demonstrated by 2026",
                "Will a quantum computer with more than 1,000 logical qubits be demonstrated by December 31, 2026?",
                vec!["Yes - >1000 qubits".to_string(), "No - Fewer qubits".to_string()],
                vec![7.1, 1.12],
            ),
            (
                "quantum_chemistry_advantage",
                "Quantum advantage claimed in practical chemistry/materials domain",
                "Will 'quantum advantage' be claimed in a practical domain (chemistry, materials) by end of 2026?",
                vec!["Yes - Quantum advantage".to_string(), "No - No advantage yet".to_string()],
                vec![3.4, 1.32],
            ),
            // LLM Benchmarks & AI Progress
            (
                "llm_human_reasoning",
                "New LLM achieves human-level reasoning score",
                "Will OpenAI or competitor reveal a model with human-level reasoning score by end of 2026?",
                vec!["Yes - Human-level reasoning".to_string(), "No - Still below human".to_string()],
                vec![2.8, 1.4],
            ),
            // Tech Antitrust Cases
            (
                "doj_big_tech_antitrust_2027",
                "U.S. DOJ wins major antitrust case vs Big Tech by 2027",
                "Will the U.S. DOJ win its major antitrust case against a Big Tech company by December 31, 2027?",
                vec!["Yes - DOJ wins".to_string(), "No - Big Tech wins".to_string()],
                vec![2.6, 1.45],
            ),
            (
                "google_meta_forced_divestiture",
                "Google or Meta forced to divest major unit",
                "Will Google or Meta be legally forced to divest a major business unit by December 31, 2027?",
                vec!["Yes - Forced divestiture".to_string(), "No - Keep all units".to_string()],
                vec![4.2, 1.22],
            ),
            // LIVE SOLANA PRICE BETTING (Updates every minute!)
            (
                "solana_price_1min_up",
                "🚀 LIVE: Solana price UP in next 1 minute",
                "Will Solana (SOL) price be HIGHER than current price in exactly 1 minute? (Live betting market!)",
                vec!["📈 Price UP".to_string(), "📉 Price DOWN/Same".to_string()],
                vec![1.9, 1.9],
            ),
            (
                "solana_price_5min_up",
                "🚀 LIVE: Solana price UP in next 5 minutes",
                "Will Solana (SOL) price be HIGHER than current price in exactly 5 minutes? (Live betting market!)",
                vec!["📈 Price UP".to_string(), "📉 Price DOWN/Same".to_string()],
                vec![2.1, 1.8],
            ),
            (
                "solana_price_breakout",
                "🚀 LIVE: Solana breaks $200 today",
                "Will Solana (SOL) price reach or exceed $200 USD at any point today?",
                vec!["🎯 Breaks $200".to_string(), "❌ Stays below $200".to_string()],
                vec![5.5, 1.15],
            ),
        ];

        for (id, title, description, outcomes, odds) in markets {
            self.markets.insert(id.to_string(), Market {
                id: id.to_string(),
                title: title.to_string(),
                description: description.to_string(),
                outcomes,
                odds,
                total_volume: 0,
                is_active: true,
            });
        }
    }

    pub fn place_bet(&mut self, account_name: &str, market_id: &str, outcome_index: usize, amount: u64) -> Result<String, String> {
        // Check if account exists
        let account = self.accounts.get_mut(account_name)
            .ok_or_else(|| format!("Account '{}' not found", account_name))?;

        // Check if account has sufficient balance
        if account.balance < amount {
            return Err(format!("Insufficient balance. {} has {} BB, needs {} BB", account_name, account.balance, amount));
        }

        // Check if market exists
        let market = self.markets.get_mut(market_id)
            .ok_or_else(|| format!("Market '{}' not found", market_id))?;

        // Check if market is active
        if !market.is_active {
            return Err(format!("Market '{}' is not active", market_id));
        }

        // Check if outcome index is valid
        if outcome_index >= market.outcomes.len() {
            return Err(format!("Invalid outcome index {} for market '{}'", outcome_index, market_id));
        }

        // Calculate potential payout
        let odds = market.odds[outcome_index];
        let potential_payout = (amount as f64 * odds) as u64;

        // Deduct amount from account
        account.balance -= amount;

        // Add to market volume
        market.total_volume += amount;

        // Create bet record
        let bet_id = Uuid::new_v4().to_string();
        let bet = Bet {
            id: bet_id.clone(),
            account: account_name.to_string(),
            market_id: market_id.to_string(),
            outcome_index,
            amount,
            potential_payout,
            timestamp: chrono::Utc::now().to_rfc3339(),
        };

        self.bets.push(bet);

        Ok(format!("✅ Bet placed! {} bet {} BB on '{}' (outcome: {}) for potential payout of {} BB. Bet ID: {}", 
                  account_name, amount, market.outcomes[outcome_index], outcome_index, potential_payout, bet_id))
    }

    pub fn get_account(&self, name: &str) -> Option<&Account> {
        self.accounts.get(name)
    }

    pub fn get_market(&self, id: &str) -> Option<&Market> {
        self.markets.get(id)
    }

    pub fn list_accounts(&self) -> Vec<&Account> {
        self.accounts.values().collect()
    }

    pub fn list_markets(&self) -> Vec<&Market> {
        self.markets.values().collect()
    }

    pub fn get_bets_for_account(&self, account_name: &str) -> Vec<&Bet> {
        self.bets.iter().filter(|bet| bet.account == account_name).collect()
    }

    pub fn add_balance(&mut self, account_name: &str, amount: u64) -> Result<String, String> {
        let account = self.accounts.get_mut(account_name)
            .ok_or_else(|| format!("Account '{}' not found", account_name))?;
        
        account.balance += amount;
        Ok(format!("✅ Added {} BB to {}. New balance: {} BB", amount, account_name, account.balance))
    }

    pub fn transfer(&mut self, from: &str, to: &str, amount: u64) -> Result<String, String> {
        // Check if both accounts exist
        if !self.accounts.contains_key(from) {
            return Err(format!("Account '{}' not found", from));
        }
        if !self.accounts.contains_key(to) {
            return Err(format!("Account '{}' not found", to));
        }

        // Check balance
        let from_balance = self.accounts[from].balance;
        if from_balance < amount {
            return Err(format!("Insufficient balance. {} has {} BB, needs {} BB", from, from_balance, amount));
        }

        // Perform transfer
        self.accounts.get_mut(from).unwrap().balance -= amount;
        self.accounts.get_mut(to).unwrap().balance += amount;

        Ok(format!("✅ Transferred {} BB from {} to {}. {} balance: {} BB, {} balance: {} BB", 
                  amount, from, to, from, self.accounts[from].balance, to, self.accounts[to].balance))
    }

    // Live Solana price simulation (in a real system, this would connect to a price API)
    pub fn get_live_solana_price(&self) -> f64 {
        // Simulate Solana price around $150-200 with random fluctuations
        let base_price = 175.0;
        let timestamp = chrono::Utc::now().timestamp() as f64;
        let variation = (timestamp.sin() * 10.0) + (timestamp.cos() * 5.0);
        (base_price + variation).max(50.0).min(300.0)
    }

    pub fn get_live_market_info(&self, market_id: &str) -> Option<String> {
        match market_id {
            "solana_price_1min_up" => {
                let current_price = self.get_live_solana_price();
                Some(format!("💰 Current SOL Price: ${:.2} | Next update in ~{} seconds", 
                           current_price, 60 - (chrono::Utc::now().timestamp() % 60)))
            },
            "solana_price_5min_up" => {
                let current_price = self.get_live_solana_price();
                Some(format!("💰 Current SOL Price: ${:.2} | 5min target price betting", current_price))
            },
            "solana_price_breakout" => {
                let current_price = self.get_live_solana_price();
                let distance_to_200 = 200.0 - current_price;
                Some(format!("💰 Current SOL Price: ${:.2} | ${:.2} away from $200 breakout", 
                           current_price, distance_to_200))
            },
            _ => None
        }
    }
}