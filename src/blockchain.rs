use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;
use chrono::{Utc, Duration};

// Import ObjectWire parser for automatic market generation
use crate::objectwire_parser::{ObjectWireParser, PredictableClaim};

// Import real blockchain components
use crate::blockchain_core::*;
use crate::blockchain_core::crypto::*;
use crate::consensus::*;

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

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PricePoint {
    pub price: f64,
    pub timestamp: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LiveMarket {
    pub id: String,
    pub asset: String, // "BTC" or "SOL"
    pub entry_price: f64,
    pub entry_time: i64,
    pub duration_seconds: i64, // How long until market resolves
    pub created_at: i64,
    pub status: String, // "active", "expired", "resolved"
    pub winning_outcome: Option<u8>, // 0 = higher, 1 = lower, None = unresolved
    pub price_history: Vec<PricePoint>,
    pub total_bets_higher: u64,
    pub total_bets_lower: u64,
    pub total_volume: u64,
}

#[derive(Debug)]
pub struct PredictionMarketBlockchain {
    // Real blockchain engine
    pub consensus_engine: ConsensusEngine,
    
    // Prediction market specific data
    pub markets: HashMap<String, Market>,
    pub bets: Vec<Bet>,
    pub objectwire_parser: ObjectWireParser,
    pub pending_claims: Vec<PredictableClaim>,
    
    // Live price prediction markets
    pub live_markets: Vec<LiveMarket>,
    pub live_market_bets: HashMap<String, Vec<(String, u8, u64)>>, // market_id -> [(account, outcome, amount)]
    
    // Wallet management for demo
    pub demo_wallets: HashMap<String, (secp256k1::SecretKey, secp256k1::PublicKey)>,
    
    // Real-time price cache
    pub cached_btc_price: f64,
    pub cached_sol_price: f64,
    pub last_price_update: chrono::DateTime<chrono::Utc>,
}

impl PredictionMarketBlockchain {
    pub fn new() -> Self {
        // Initialize real blockchain with consensus
        let consensus_params = ConsensusParams::default();
        let consensus_engine = ConsensusEngine::new(consensus_params);
        
        let mut blockchain = PredictionMarketBlockchain {
            consensus_engine,
            markets: HashMap::new(),
            bets: Vec::new(),
            live_markets: Vec::new(),
            live_market_bets: HashMap::new(),
            objectwire_parser: ObjectWireParser::new(),
            pending_claims: Vec::new(),
            demo_wallets: HashMap::new(),
            cached_btc_price: 107000.0, // Real price from CoinGecko
            cached_sol_price: 245.0,     // Real price from CoinGecko
            last_price_update: chrono::Utc::now(),
        };

        // Create demo wallets for testing
        let wallet_names = vec![
            "alice", "bob", "charlie", "diana", 
            "eve", "frank", "grace", "henry"
        ];

        for name in wallet_names {
            let (secret_key, public_key) = generate_keypair();
            blockchain.demo_wallets.insert(name.to_string(), (secret_key, public_key));
            
            // Fund demo wallets by mining blocks to their addresses
            let address = public_key_to_address(&public_key);
            println!("Created demo wallet '{}' with address: {}", name, address);
        }

        // Create sample tech markets
        blockchain.create_sample_markets();
        
        // Mine some initial blocks to fund demo wallets
        blockchain.mine_initial_blocks();
        
        blockchain
    }
    
    /// Mine initial blocks to fund demo wallets
    fn mine_initial_blocks(&mut self) {
        println!("Mining initial blocks to fund demo wallets...");
        
        for (wallet_name, (_, public_key)) in &self.demo_wallets {
            let address = public_key_to_address(public_key);
            match self.consensus_engine.mine_block(address) {
                Ok(block) => println!("Mined block for {}: {}", wallet_name, block),
                Err(e) => println!("Failed to mine block for {}: {}", wallet_name, e),
            }
        }
    }
    
    /// Create a new market on the blockchain
    pub fn create_market(&mut self, title: String, description: String, outcomes: Vec<String>) -> Result<String, String> {
        let market_id = Uuid::new_v4().to_string();
        
        // Create market data
        let market_data = MarketData {
            market_id: market_id.clone(),
            title: title.clone(),
            description: description.clone(),
            outcomes: outcomes.clone(),
            end_time: Utc::now() + Duration::days(30), // 30 days from now
            creator: "system".to_string(), // TODO: Use actual creator address
            resolution_source: "manual".to_string(),
        };
        
        // Create blockchain transaction for market creation
        let market_tx = Transaction::new(
            TransactionType::CreateMarket(market_data),
            1000, // Market creation fee
        );
        
        // Add transaction to pending pool
        self.consensus_engine.add_transaction(market_tx)?;
        
        // Create market in our prediction market state
        let market = Market {
            id: market_id.clone(),
            title,
            description,
            outcomes,
            odds: vec![2.0; 2], // Default odds
            total_volume: 0,
            is_active: true,
        };
        
        self.markets.insert(market_id.clone(), market);
        
        Ok(market_id)
    }
    
    /// Place a bet on a market
    pub fn place_bet(&mut self, account_name: &str, market_id: &str, outcome_index: usize, amount: u64) -> Result<String, String> {
        // Get wallet for account
        let (secret_key, public_key) = self.demo_wallets.get(account_name)
            .ok_or_else(|| format!("Account '{}' not found", account_name))?
            .clone();
        
        let address = public_key_to_address(&public_key);
        
        // Check balance
        let balance = self.consensus_engine.get_balance(&address);
        if balance < amount {
            return Err(format!("Insufficient balance. Has: {}, Needs: {}", balance, amount));
        }
        
        // Verify market exists
        if !self.markets.contains_key(market_id) {
            return Err("Market not found".to_string());
        }
        
        // Create bet data
        let bet_data = BetData {
            market_id: market_id.to_string(),
            outcome_index,
            amount,
            odds: 2.0, // TODO: Calculate real odds
        };
        
        // Create bet transaction
        let mut bet_tx = Transaction::new(
            TransactionType::PlaceBet(bet_data),
            100, // Betting fee
        );
        
        // Sign the transaction
        bet_tx.sign(&secret_key, &public_key)
            .map_err(|e| format!("Failed to sign transaction: {}", e))?;
        
        // Add to pending transactions
        self.consensus_engine.add_transaction(bet_tx.clone())?;
        
        // Create bet record
        let bet = Bet {
            id: hash_to_hex(&bet_tx.id),
            market_id: market_id.to_string(),
            account: account_name.to_string(),
            outcome_index,
            amount,
            potential_payout: amount * 2,
            timestamp: Utc::now().format("%Y-%m-%d %H:%M:%S UTC").to_string(),
        };
        
        self.bets.push(bet);
        
        // Update market volume
        if let Some(market) = self.markets.get_mut(market_id) {
            market.total_volume += amount;
        }
        
        Ok(hash_to_hex(&bet_tx.id))
    }
    
    /// Get account balance from blockchain
    pub fn get_balance(&self, account_name: &str) -> u64 {
        if let Some((_, public_key)) = self.demo_wallets.get(account_name) {
            let address = public_key_to_address(public_key);
            self.consensus_engine.get_balance(&address)
        } else {
            0
        }
    }
    
    /// Get all accounts with their blockchain balances
    pub fn get_accounts(&self) -> Vec<Account> {
        self.demo_wallets
            .iter()
            .map(|(name, (_, public_key))| {
                let address = public_key_to_address(public_key);
                let balance = self.consensus_engine.get_balance(&address);
                Account {
                    name: name.clone(),
                    address,
                    balance,
                    private_key: "hidden".to_string(), // Don't expose private keys
                }
            })
            .collect()
    }
    
    /// Mine a new block
    pub fn mine_block(&mut self, miner_account: &str) -> Result<String, String> {
        if let Some((_, public_key)) = self.demo_wallets.get(miner_account) {
            let address = public_key_to_address(public_key);
            match self.consensus_engine.mine_block(address) {
                Ok(block) => Ok(hash_to_hex(&block.hash)),
                Err(e) => Err(e),
            }
        } else {
            Err(format!("Miner account '{}' not found", miner_account))
        }
    }
    
    /// Get blockchain information
    pub fn get_blockchain_info(&self) -> BlockchainInfo {
        self.consensus_engine.get_info()
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
            // LIVE CRYPTO PRICE BETTING (Updates every minute!)
            (
                "btc_15min_above_current",
                "₿ LIVE: Bitcoin ABOVE current price in 15 minutes",
                "Will Bitcoin (BTC) price be HIGHER than current price in exactly 15 minutes? (Live betting market!)",
                vec!["📈 Price ABOVE".to_string(), "📉 Price BELOW/Same".to_string()],
                vec![1.95, 1.85],
            ),
            (
                "btc_hourly_direction",
                "₿ LIVE: Bitcoin direction next hour",
                "Will Bitcoin (BTC) price move UP or DOWN in the next hour? (Hourly betting market)",
                vec!["🚀 UP Next Hour".to_string(), "📉 DOWN Next Hour".to_string()],
                vec![1.9, 1.9],
            ),
            (
                "btc_daily_100k",
                "₿ LIVE: Bitcoin hits $100K today",
                "Will Bitcoin (BTC) price reach or exceed $100,000 USD at any point today?",
                vec!["🎯 Hits $100K".to_string(), "❌ Stays below $100K".to_string()],
                vec![8.5, 1.1],
            ),
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
            
            // === OBJECTWIRE-STYLE PREDICTION MARKETS ===
            // Policy & Regulation Markets
            (
                "us_fed_rate_december_2025",
                "📊 U.S. Federal Reserve raises rates in December 2025",
                "Will the Federal Reserve raise interest rates at their December 2025 meeting? (ObjectWire Policy Analysis)",
                vec!["🔺 Rates Raised".to_string(), "➡️ Rates Hold/Cut".to_string()],
                vec![2.8, 1.4],
            ),
            (
                "china_ai_export_controls_2026",
                "🌐 China implements new AI export controls by Q1 2026",
                "Will China announce new AI technology export controls by March 31, 2026? (ObjectWire Geopolitical Intelligence)",
                vec!["✅ New Controls".to_string(), "❌ No New Controls".to_string()],
                vec![3.2, 1.3],
            ),
            (
                "eu_digital_services_enforcement",
                "⚖️ EU issues first major Digital Services Act penalty",
                "Will the EU issue its first major penalty (>€100M) under the Digital Services Act by end of 2025?",
                vec!["💰 Major Penalty Issued".to_string(), "📝 No Major Penalty".to_string()],
                vec![2.1, 1.8],
            ),
            
            // Economic Intelligence Markets
            (
                "global_recession_q2_2026",
                "📉 Global economic recession declared by Q2 2026",
                "Will a major economic institution declare a global recession by June 30, 2026? (ObjectWire Economic Analysis)",
                vec!["📊 Recession Declared".to_string(), "📈 No Recession".to_string()],
                vec![4.5, 1.2],
            ),
            (
                "bitcoin_strategic_reserve_2026",
                "🏛️ Nation announces Bitcoin strategic reserve in 2026",
                "Will any G20 nation officially announce Bitcoin as a strategic reserve asset in 2026?",
                vec!["🪙 Strategic Reserve".to_string(), "🚫 No Adoption".to_string()],
                vec![3.8, 1.25],
            ),
            (
                "dollar_dominance_challenge_2027",
                "💱 Alternative to USD emerges for international trade by 2027",
                "Will a viable alternative to USD for major international trade emerge by December 31, 2027?",
                vec!["🌍 USD Alternative".to_string(), "💵 USD Remains Dominant".to_string()],
                vec![6.2, 1.14],
            ),
            
            // Corporate & Technology Intelligence
            (
                "openai_ipo_2026",
                "🚀 OpenAI announces IPO plans in 2026",
                "Will OpenAI officially announce plans for an initial public offering in 2026? (ObjectWire Corporate Intelligence)",
                vec!["📈 IPO Announced".to_string(), "🔒 Stays Private".to_string()],
                vec![2.9, 1.38],
            ),
            (
                "tesla_robotaxi_commercial_2026",
                "🚗 Tesla launches commercial robotaxi service in 2026",
                "Will Tesla launch a commercial robotaxi service in any major city by December 31, 2026?",
                vec!["🤖 Robotaxi Launch".to_string(), "⏰ Launch Delayed".to_string()],
                vec![5.1, 1.16],
            ),
            (
                "nvidia_china_license_revoked",
                "🇨🇳 NVIDIA's China AI chip licenses revoked in 2025",
                "Will the U.S. government revoke NVIDIA's licenses to sell AI chips to China by December 31, 2025?",
                vec!["🚫 Licenses Revoked".to_string(), "✅ Licenses Maintained".to_string()],
                vec![3.4, 1.32],
            ),
            
            // Geopolitical Intelligence Markets
            (
                "ukraine_nato_membership_2026",
                "🛡️ Ukraine receives NATO membership invitation by 2026",
                "Will Ukraine receive an official NATO membership invitation by December 31, 2026? (ObjectWire Geopolitical Analysis)",
                vec!["🤝 NATO Invitation".to_string(), "⏳ No Invitation".to_string()],
                vec![7.8, 1.11],
            ),
            (
                "taiwan_semiconductor_facility_us",
                "🏭 Taiwan moves major semiconductor production to U.S. in 2025-2026",
                "Will Taiwan announce relocation of a major semiconductor facility to the U.S. by end of 2026?",
                vec!["🇺🇸 Facility Relocated".to_string(), "🇹🇼 Stays in Taiwan".to_string()],
                vec![2.6, 1.45],
            ),
            (
                "middle_east_oil_production_cut",
                "🛢️ Major Middle East oil production cut announced in 2025",
                "Will OPEC+ announce a production cut of >1M barrels/day before December 31, 2025?",
                vec!["📉 Production Cut".to_string(), "📊 Production Stable".to_string()],
                vec![3.7, 1.26],
            ),
            
            // Climate & Energy Intelligence
            (
                "cop30_loss_damage_fund_operational",
                "🌱 COP30 Loss & Damage Fund becomes operational in 2025",
                "Will the Loss & Damage Fund established at COP28 become operational with >$10B by COP30 2025?",
                vec!["💰 Fund Operational".to_string(), "📋 Still Planning".to_string()],
                vec![2.3, 1.65],
            ),
            (
                "carbon_border_adjustment_expansion",
                "🌍 EU expands Carbon Border Adjustment to new sectors in 2026",
                "Will the EU announce expansion of CBAM to agriculture or shipping by December 31, 2026?",
                vec!["📈 CBAM Expansion".to_string(), "🔄 Current Scope".to_string()],
                vec![1.9, 1.95],
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

    pub fn get_account(&self, name: &str) -> Option<Account> {
        if let Some((_, public_key)) = self.demo_wallets.get(name) {
            let address = public_key_to_address(public_key);
            let balance = self.consensus_engine.get_balance(&address);
            Some(Account {
                name: name.to_string(),
                address,
                balance,
                private_key: "hidden".to_string(),
            })
        } else {
            None
        }
    }

    pub fn get_market(&self, id: &str) -> Option<&Market> {
        self.markets.get(id)
    }

    pub fn list_accounts(&self) -> Vec<Account> {
        self.get_accounts()
    }

    pub fn list_markets(&self) -> Vec<&Market> {
        self.markets.values().collect()
    }

    pub fn get_bets_for_account(&self, account_name: &str) -> Vec<&Bet> {
        self.bets.iter().filter(|bet| bet.account == account_name).collect()
    }

    pub fn add_balance(&mut self, account_name: &str, amount: u64) -> Result<String, String> {
        // In admin mode, directly add balance to account
        // Get the account's address
        if let Some((_, public_key)) = self.demo_wallets.get(account_name) {
            let address = public_key_to_address(public_key);
            let current_balance = self.consensus_engine.get_balance(&address);
            
            // Directly add to UTXO set in admin mode
            self.consensus_engine.add_balance_direct(&address, amount * 100_000_000);
            
            let new_balance = self.consensus_engine.get_balance(&address);
            Ok(format!("✅ Added {} BB to {}. Balance: {} BB -> {} BB", 
                      amount, account_name, current_balance / 100_000_000, new_balance / 100_000_000))
        } else {
            Err(format!("Account '{}' not found", account_name))
        }
    }

    pub fn transfer(&mut self, from: &str, to: &str, amount: u64) -> Result<String, String> {
        // Check if both wallets exist
        let (from_secret, from_public) = self.demo_wallets.get(from)
            .ok_or_else(|| format!("Account '{}' not found", from))?
            .clone();
        let (_, to_public) = self.demo_wallets.get(to)
            .ok_or_else(|| format!("Account '{}' not found", to))?
            .clone();

        let from_address = public_key_to_address(&from_public);
        let to_address = public_key_to_address(&to_public);

        // Check balance
        let from_balance = self.consensus_engine.get_balance(&from_address);
        if from_balance < amount {
            return Err(format!("Insufficient balance. {} has {} BB, needs {} BB", from, from_balance, amount));
        }

        // Create transfer transaction
        let mut transfer_tx = Transaction::new(
            TransactionType::Transfer {
                inputs: vec![], // TODO: Implement proper UTXO inputs
                outputs: vec![
                    TransactionOutput {
                        value: amount,
                        script_pubkey: vec![],
                        address: to_address.clone(),
                    }
                ],
            },
            100, // Transfer fee
        );

        // Sign the transaction
        transfer_tx.sign(&from_secret, &from_public)
            .map_err(|e| format!("Failed to sign transaction: {}", e))?;

        // Add to pending transactions
        self.consensus_engine.add_transaction(transfer_tx)?;

        let _new_from_balance = self.consensus_engine.get_balance(&from_address);
        let _new_to_balance = self.consensus_engine.get_balance(&to_address);

        Ok(format!("✅ Transfer transaction created: {} BB from {} to {}. Pending confirmation.", 
                  amount, from, to))
    }

    // Live crypto price - REAL PRICES from CoinGecko
    pub fn get_live_bitcoin_price(&self) -> f64 {
        // Return real Bitcoin price: $107,000 (as of Oct 2025)
        self.cached_btc_price
    }

    // Method to update Bitcoin price from CoinGecko API
    pub async fn update_bitcoin_price(&mut self) -> Result<f64, Box<dyn std::error::Error>> {
        let url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd";
        match reqwest::get(url).await {
            Ok(response) => {
                match response.json::<serde_json::Value>().await {
                    Ok(data) => {
                        if let Some(price) = data["bitcoin"]["usd"].as_f64() {
                            self.cached_btc_price = price;
                            self.last_price_update = chrono::Utc::now();
                            println!("Updated BTC price: ${}", price);
                            Ok(price)
                        } else {
                            Err("Failed to parse Bitcoin price from CoinGecko".into())
                        }
                    }
                    Err(e) => Err(Box::new(e))
                }
            }
            Err(e) => Err(Box::new(e))
        }
    }

    pub fn get_live_solana_price(&self) -> f64 {
        // Return real Solana price: $245 (as of Oct 2025)
        self.cached_sol_price
    }

    // Method to update Solana price from CoinGecko API
    pub async fn update_solana_price(&mut self) -> Result<f64, Box<dyn std::error::Error>> {
        let url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd";
        match reqwest::get(url).await {
            Ok(response) => {
                match response.json::<serde_json::Value>().await {
                    Ok(data) => {
                        if let Some(price) = data["solana"]["usd"].as_f64() {
                            self.cached_sol_price = price;
                            self.last_price_update = chrono::Utc::now();
                            println!("Updated SOL price: ${}", price);
                            Ok(price)
                        } else {
                            Err("Failed to parse Solana price from CoinGecko".into())
                        }
                    }
                    Err(e) => Err(Box::new(e))
                }
            }
            Err(e) => Err(Box::new(e))
        }
    }

    pub fn get_live_market_info(&self, market_id: &str) -> Option<String> {
        match market_id {
            "btc_15min_above_current" => {
                let current_price = self.get_live_bitcoin_price();
                let minutes_remaining = 15 - ((chrono::Utc::now().timestamp() / 60) % 15);
                Some(format!("₿ Current BTC Price: ${:.0} | {} min until 15min settlement", 
                           current_price, minutes_remaining))
            },
            "btc_hourly_direction" => {
                let current_price = self.get_live_bitcoin_price();
                let minutes_remaining = 60 - ((chrono::Utc::now().timestamp() / 60) % 60);
                Some(format!("₿ Current BTC Price: ${:.0} | {} min until hourly settlement", 
                           current_price, minutes_remaining))
            },
            "btc_daily_100k" => {
                let current_price = self.get_live_bitcoin_price();
                let distance_to_100k = 100000.0 - current_price;
                Some(format!("₿ Current BTC Price: ${:.0} | ${:.0} away from $100K breakout", 
                           current_price, distance_to_100k))
            },
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

    // === OBJECTWIRE INTEGRATION METHODS ===
    
    pub async fn sync_objectwire_articles(&mut self) -> Result<usize, String> {
        let articles = self.objectwire_parser
            .fetch_objectwire_articles()
            .await
            .map_err(|e| format!("Failed to fetch ObjectWire articles: {}", e))?;

        let mut new_markets = 0;
        
        for article in articles {
            let claims = self.objectwire_parser.extract_claims(&article);
            
            for claim in claims {
                // Only create markets for high-confidence claims
                if claim.confidence_score >= 0.7 {
                    if let Some(market) = self.objectwire_parser.generate_market_from_claim(&claim) {
                        // Check if market doesn't already exist
                        if !self.markets.contains_key(&market.id) {
                            self.markets.insert(market.id.clone(), market);
                            new_markets += 1;
                        }
                    }
                }
                
                // Store claim for potential future market creation
                self.pending_claims.push(claim);
            }
        }

        Ok(new_markets)
    }

    pub fn get_objectwire_claims(&self) -> &Vec<PredictableClaim> {
        &self.pending_claims
    }

    pub fn get_objectwire_markets(&self) -> Vec<&Market> {
        self.markets.values()
            .filter(|market| market.id.starts_with("ow_"))
            .collect()
    }

    pub fn create_market_from_claim(&mut self, claim_id: &str) -> Result<String, String> {
        let claim = self.pending_claims
            .iter()
            .find(|c| c.article_id == claim_id)
            .ok_or_else(|| format!("Claim '{}' not found", claim_id))?;

        if let Some(market) = self.objectwire_parser.generate_market_from_claim(claim) {
            let market_id = market.id.clone();
            self.markets.insert(market_id.clone(), market);
            Ok(format!("✅ Created market '{}' from ObjectWire claim", market_id))
        } else {
            Err("Failed to generate market from claim (confidence too low)".to_string())
        }
    }

    pub fn get_article_betting_summary(&self, article_id: &str) -> Option<String> {
        let related_markets: Vec<_> = self.markets.values()
            .filter(|market| market.id.contains(article_id))
            .collect();

        if related_markets.is_empty() {
            return None;
        }

        let total_volume: u64 = related_markets.iter()
            .map(|market| market.total_volume)
            .sum();

        let active_markets = related_markets.len();

        Some(format!(
            "📊 Article Betting Activity: {} active markets, {} BB total volume",
            active_markets, total_volume
        ))
    }
}
impl PredictionMarketBlockchain {
    /// Create a new live Bitcoin price market
    pub fn create_live_btc_market_2(&mut self, current_price: f64) -> String {
        let market_id = format!("live_btc_{}", Uuid::new_v4());
        let now = Utc::now().timestamp();
        
        let live_market = LiveMarket {
            id: market_id.clone(),
            asset: "BTC".to_string(),
            entry_price: current_price,
            entry_time: now,
            duration_seconds: 900,
            created_at: now,
            status: "active".to_string(),
            winning_outcome: None,
            price_history: vec![PricePoint { price: current_price, timestamp: now }],
            total_bets_higher: 0,
            total_bets_lower: 0,
            total_volume: 0,
        };
        
        self.live_markets.push(live_market);
        self.live_market_bets.insert(market_id.clone(), Vec::new());
        market_id
    }

    /// Place a bet on a live market
    pub fn place_live_bet_2(&mut self, market_id: &str, account: &str, amount: u64, outcome: u8) -> Result<String, String> {
        if outcome > 1 {
            return Err("Invalid outcome".to_string());
        }

        let market = self.live_markets.iter_mut()
            .find(|m| m.id == market_id)
            .ok_or("Market not found")?;

        let elapsed = Utc::now().timestamp() - market.entry_time;
        if elapsed > market.duration_seconds {
            market.status = "expired".to_string();
            return Err("Market expired".to_string());
        }

        if outcome == 0 {
            market.total_bets_higher = market.total_bets_higher.saturating_add(amount);
        } else {
            market.total_bets_lower = market.total_bets_lower.saturating_add(amount);
        }
        market.total_volume = market.total_volume.saturating_add(amount);

        if let Some(bets) = self.live_market_bets.get_mut(market_id) {
            bets.push((account.to_string(), outcome, amount));
        }

        Ok(Uuid::new_v4().to_string())
    }

    /// Get active live markets
    pub fn get_live_markets_2(&self) -> Vec<&LiveMarket> {
        self.live_markets.iter().filter(|m| m.status == "active").collect()
    }

    /// Get specific live market
    pub fn get_live_market_2(&self, market_id: &str) -> Option<&LiveMarket> {
        self.live_markets.iter().find(|m| m.id == market_id)
    }
}
