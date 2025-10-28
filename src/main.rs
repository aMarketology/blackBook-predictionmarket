use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{net::SocketAddr, sync::{Arc, Mutex}, collections::HashMap};
use tower_http::cors::{Any, CorsLayer};
use uuid::Uuid;

mod ledger;
use ledger::Ledger;

mod scraper;
use scraper::ScrapedEvent;

mod coindesk;
use coindesk::CoinGeckoClient;

// Prediction market struct - now tracks bettors for leaderboard
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PredictionMarket {
    pub id: String,
    pub title: String,
    pub description: String,
    pub category: String, // tech, sports, crypto, politics, business
    pub options: Vec<String>,
    pub is_resolved: bool,
    pub winning_option: Option<usize>,
    pub escrow_address: String,
    pub created_at: u64,
    
    // NEW: Tracking for leaderboard
    pub total_volume: f64,           // Total amount bet
    pub unique_bettors: Vec<String>, // Track unique bettors
    pub bet_count: u64,              // Total number of bets
    pub on_leaderboard: bool,        // Promoted when 10+ bettors
}

impl PredictionMarket {
    pub fn new(
        id: String,
        title: String,
        description: String,
        category: String,
        options: Vec<String>,
    ) -> Self {
        Self {
            id,
            title,
            description,
            category,
            options,
            is_resolved: false,
            winning_option: None,
            escrow_address: format!("MARKET_{}", Uuid::new_v4().simple()),
            created_at: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            total_volume: 0.0,
            unique_bettors: Vec::new(),
            bet_count: 0,
            on_leaderboard: false,
        }
    }
    
    /// Record a bet and check if should be promoted to leaderboard
    pub fn record_bet(&mut self, bettor: &str, amount: f64) {
        self.bet_count += 1;
        self.total_volume += amount;
        
        // Add unique bettor if new
        if !self.unique_bettors.contains(&bettor.to_string()) {
            self.unique_bettors.push(bettor.to_string());
        }
        
        // Promote to leaderboard when 10+ unique bettors
        if self.unique_bettors.len() >= 10 && !self.on_leaderboard {
            self.on_leaderboard = true;
        }
    }
}

// Application state - simple prediction market storage
#[derive(Debug)]
pub struct AppState {
    pub ledger: Ledger,
    pub markets: HashMap<String, PredictionMarket>,
    pub coindesk: CoinGeckoClient,
}

impl AppState {
    pub fn new() -> Self {
        let mut state = Self {
            ledger: Ledger::new_full_node(),
            markets: HashMap::new(),
            coindesk: CoinGeckoClient::new(),
        };

        // Initialize with demo accounts
        state.ledger.deposit("alice", 1000.0, "Initial demo balance");
        state.ledger.deposit("bob", 500.0, "Initial demo balance");
        state.ledger.deposit("charlie", 750.0, "Initial demo balance");

        // Create sample markets
        state.create_sample_markets();

        state
    }
    
    fn create_sample_markets(&mut self) {
        // Sample Markets
        let events = vec![
            // Original 3
            ("tech_ai_breakthrough_2025", "Major AI Breakthrough in 2025", "Will there be a major AI breakthrough (AGI, solved alignment, etc.) announced by a major tech company in 2025?", "tech"),
            ("business_recession_2025", "US Recession in 2025", "Will the United States officially enter a recession in 2025?", "business"),
            ("crypto_bitcoin_100k", "Bitcoin reaches $100K in 2025", "Will Bitcoin (BTC) reach $100,000 USD at any point during 2025?", "crypto"),
            
            // Sports Events (50 total)
            ("sports_australian_open_2026", "Australian Open 2026 Tennis", "Will Novak Djokovic win the Australian Open 2026?", "sports"),
            ("sports_dakar_rally_2026", "Dakar Rally 2026", "Will a driver from South America win the 2026 Dakar Rally?", "sports"),
            ("sports_six_nations_2026", "Six Nations Rugby 2026", "Will France win the 2026 Six Nations Championship?", "sports"),
            ("sports_milano_cortina_2026", "Winter Olympics Milano Cortina 2026", "Will Italy win more than 10 medals at Milano Cortina 2026?", "sports"),
            ("sports_daytona_500_2026", "Daytona 500 2026", "Will a NASCAR rookie finish in top 3 at Daytona 500 2026?", "sports"),
            ("sports_masters_2026", "The Masters Golf 2026", "Will an international player win The Masters 2026?", "sports"),
            ("sports_boston_marathon_2026", "Boston Marathon 2026", "Will a world record be broken at Boston Marathon 2026?", "sports"),
            ("sports_kentucky_derby_2026", "Kentucky Derby 2026", "Will a female jockey win the Kentucky Derby 2026?", "sports"),
            ("sports_french_open_2026", "French Open 2026", "Will Serena Williams's record be broken at French Open 2026?", "sports"),
            ("sports_monaco_gp_2026", "F1 Monaco Grand Prix 2026", "Will the 2026 Monaco GP be won by a driver 25 or younger?", "sports"),
            ("sports_us_open_golf_2026", "US Open Golf 2026", "Will an American golfer win the 2026 US Open?", "sports"),
            ("sports_wimbledon_2026", "Wimbledon Tennis 2026", "Will a top-5 seed win the Wimbledon 2026 singles title?", "sports"),
            ("sports_tour_france_femmes_2026", "Tour de France Femmes 2026", "Will a European cyclist win Tour de France Femmes 2026?", "sports"),
            ("sports_us_open_tennis_2026", "US Open Tennis 2026", "Will a player ranked outside top 10 win US Open 2026?", "sports"),
            ("sports_ryder_cup_2027", "Ryder Cup 2027", "Will Europe win the 2027 Ryder Cup?", "sports"),
            ("sports_pdc_world_darts_2026", "PDC World Darts 2025/2026", "Will a player from outside UK/Europe win PDC World Championship?", "sports"),
            ("sports_world_handball_2025", "World Handball Championship 2025", "Will France win the 2025 Men's Handball Championship?", "sports"),
            ("sports_figure_skating_2026", "European Figure Skating 2026", "Will Russia be allowed to compete at European Championships 2026?", "sports"),
            ("sports_formula_e_mexico_2026", "Formula E Mexico City 2026", "Will a new driver win Formula E Mexico City ePrix 2026?", "sports"),
            ("sports_ncaa_hockey_2026", "NCAA Hockey Championship 2026", "Will a new team win NCAA Men's Ice Hockey Championship?", "sports"),
            ("sports_snooker_2026", "World Snooker Championship 2026", "Will Ronnie O'Sullivan win World Championship 2026?", "sports"),
            ("sports_f1_spain_2026", "F1 Spanish Grand Prix 2026", "Will Max Verstappen lead the championship after Spain 2026?", "sports"),
            ("sports_iihf_2026", "IIHF World Championship 2026", "Will Canada win the 2026 Men's Ice Hockey World Championship?", "sports"),
            ("sports_cheltenham_2026", "Cheltenham Festival 2026", "Will a 50-1 longshot win the Gold Cup at Cheltenham 2026?", "sports"),
            ("sports_f1_britain_2026", "F1 British Grand Prix 2026", "Will a British driver finish on podium at Silverstone 2026?", "sports"),
            ("sports_world_aquatics_2026", "World Aquatics Championships 2026", "Will a swimming world record be broken in 2026?", "sports"),
            ("sports_open_golf_2026", "The Open Championship 2026", "Will an American golfer win The Open 2026?", "sports"),
            ("sports_commonwealth_2026", "Commonwealth Games 2026", "Will Australia win more medals than England?", "sports"),
            ("sports_world_athletics_2027", "World Athletics Championships 2027", "Will Eliud Kipchoge win a medal at World Championships 2027?", "sports"),
            ("sports_f1_canada_2026", "F1 Canadian Grand Prix 2026", "Will a rookie finish top 5 at Montreal 2026?", "sports"),
            ("sports_singapore_gp_2026", "F1 Singapore Grand Prix 2026", "Will Lewis Hamilton finish top 3 at Singapore 2026?", "sports"),
            ("sports_tokyo_marathon_2026", "Tokyo Marathon 2026", "Will a female runner win the Tokyo Marathon 2026?", "sports"),
            ("sports_london_marathon_2026", "London Marathon 2026", "Will the marathon record be broken at London 2026?", "sports"),
            ("sports_uefa_champions_2026", "UEFA Champions League Final 2026", "Will a Spanish team win Champions League 2026?", "sports"),
            ("sports_uefa_europa_2026", "UEFA Europa League Final 2026", "Will an Italian team win Europa League 2026?", "sports"),
            ("sports_pga_championship_2026", "PGA Championship 2026", "Will a European golfer win PGA Championship 2026?", "sports"),
            ("sports_indy_500_2026", "Indianapolis 500 2026", "Will a new driver win the Indy 500 in their debut year?", "sports"),
            ("sports_nfl_super_bowl_2026", "NFL Super Bowl LX 2026", "Will the underdog win Super Bowl LX?", "sports"),
            ("sports_nba_finals_2026", "NBA Finals 2026", "Will a team from Eastern Conference win NBA Finals 2026?", "sports"),
            ("sports_world_cup_2026", "FIFA World Cup 2026", "Will South America win World Cup 2026?", "sports"),
            
            // Arts & Culture
            ("culture_oscars_2026", "Academy Awards 2026", "Will a superhero movie win Best Picture at 2026 Oscars?", "politics"),
            ("culture_met_gala_2026", "Met Gala 2026", "Will the theme be science fiction related at Met Gala 2026?", "politics"),
            ("culture_cannes_2026", "Cannes Film Festival 2026", "Will an Asian filmmaker win Palme d'Or at Cannes 2026?", "politics"),
            ("culture_tony_awards_2026", "Tony Awards 2026", "Will a comedy musical win Best Play at Tony Awards 2026?", "politics"),
            ("culture_nobel_2026", "Nobel Prize Ceremonies 2026", "Will AI research win Nobel Prize in Physics 2026?", "politics"),
            ("culture_venice_2026", "Venice Biennale 2026", "Will contemporary digital art dominate Venice Biennale 2026?", "politics"),
            ("culture_sundance_2026", "Sundance Film Festival 2026", "Will an indie horror film premiere at Sundance 2026?", "politics"),
            ("culture_berlin_2026", "Berlin Film Festival 2026", "Will a documentary win the Golden Bear at Berlin 2026?", "politics"),
            ("culture_fashion_week_2027", "New York Fashion Week Fall 2027", "Will sustainable fashion dominate NYFW February 2026?", "politics"),
            
            // Business & Startup Conference Events
            ("business_sxsw_pitch_2026", "SXSW Pitch Competition 2026", "Will a health tech startup win the SXSW Pitch Competition in March 2026?", "business"),
            ("business_startup_grind_2026", "Startup Grind Global Conference 2026", "Will a European founder secure Series A funding at Startup Grind Global April 2026?", "business"),
            ("business_saastr_annual_2026", "SaaStr Annual Conference 2026", "Will a SaaS startup reach unicorn status post-SaaStr Annual May 2026?", "business"),
            ("business_techcrunch_disrupt_2026", "TechCrunch Disrupt 2026", "Will an AI startup win the TechCrunch Disrupt Battlefield in October 2026?", "business"),
            ("business_money20_20_2026", "Money20/20 USA Conference 2026", "Will a blockchain fintech startup secure major funding at Money20/20 October 2026?", "business"),
            ("business_south_summit_brasil_2026", "South Summit Brasil 2026", "Will a Latin American startup achieve Series B funding at South Summit Brasil March 2026?", "business"),
            ("business_eu_startups_summit_2026", "EU-Startups Summit 2026", "Will a European deep tech startup win the pitch competition at EU-Startups Summit May 2026?", "business"),
            ("business_superventure_2026", "SuperVenture Berlin 2026", "Will a German VC firm raise over €100M at SuperVenture June 2026?", "business"),
            ("business_south_summit_madrid_2026", "South Summit Madrid 2026", "Will a Spanish startup secure Series A at South Summit Madrid June 2026?", "business"),
            ("business_slush_2026", "Slush Conference Helsinki 2026", "Will a Nordic startup become a unicorn post-Slush November 2026?", "business"),
            ("business_web_summit_2026", "Web Summit Lisbon 2026", "Will Web Summit 2026 attract over 70,000 attendees in November?", "business"),
        ];

        for (id, title, description, category) in events {
            let market_id = id.to_string();
            self.markets.insert(market_id.clone(), PredictionMarket::new(
                market_id,
                title.to_string(),
                description.to_string(),
                category.to_string(),
                vec!["Yes".to_string(), "No".to_string()],
            ));
        }
    }
}

type SharedState = Arc<Mutex<AppState>>;

// Request structures
#[derive(Deserialize)]
struct DepositRequest {
    address: String,
    amount: f64,
    memo: String,
}

#[derive(Deserialize)]
struct TransferRequest {
    from: String,
    to: String,
    amount: f64,
    memo: String,
}

#[derive(Deserialize)]
struct CreateMarketRequest {
    title: String,
    description: String,
    category: String,  // tech, sports, crypto, politics, business
    options: Vec<String>,
}

#[derive(Deserialize)]
struct BetRequest {
    account: String,
    market: String,
    outcome: usize,
    amount: f64,
}

// Response for leaderboard
#[derive(Serialize)]
struct LeaderboardEntry {
    market_id: String,
    title: String,
    category: String,
    total_volume: f64,
    unique_bettors: usize,
    bet_count: u64,
}

// Simple request for scraping a URL
#[derive(Deserialize)]
struct ScrapeRequest {
    url: String,
    title: String,
    category: String,
}

#[tokio::main]
async fn main() {
    let state = Arc::new(Mutex::new(AppState::new()));

    let app = Router::new()
        // Ledger endpoints
        .route("/balance/:address", get(get_balance))
        .route("/deposit", post(deposit_funds))
        .route("/transfer", post(transfer_funds))
        .route("/transactions/:address", get(get_user_transactions))
        .route("/transactions", get(get_all_transactions))
        .route("/ledger/stats", get(get_ledger_stats))
        
        // Market endpoints
        .route("/markets", get(get_markets))
        .route("/markets", post(create_market))
        .route("/markets/:id", get(get_market))
        .route("/leaderboard", get(get_leaderboard))
        .route("/leaderboard/:category", get(get_leaderboard_by_category))
        
        // Scraper endpoint - simple URL scraping
        .route("/scrape", post(scrape_and_create_market))
        
        // Live crypto price endpoints (real-time from CoinGecko)
        .route("/bitcoin-price", get(get_bitcoin_price))
        .route("/solana-price", get(get_solana_price))
        
        // Live BTC market endpoint
        .route("/live-btc-market", get(get_live_btc_market))
        
        // Betting endpoints
        .route("/bet", post(place_bet))
        .route("/resolve/:market_id/:winning_option", post(resolve_market))
        
        // Health check
        .route("/health", get(health_check))
        
        .with_state(state)
        .layer(
            CorsLayer::new()
                .allow_origin(Any)
                .allow_methods(Any)
                .allow_headers(Any),
        );

    let addr = SocketAddr::from(([127, 0, 0, 1], 3000));
    println!("🚀 BlackBook Prediction Market starting on http://{}", addr);
    println!("📚 API Endpoints:");
    println!("   GET  /health - Health check");
    println!("   GET  /balance/:address - Get account balance");
    println!("   POST /deposit - Deposit funds");
    println!("   POST /transfer - Transfer between accounts");
    println!("   GET  /transactions/:address - Get user transactions");
    println!("   GET  /transactions - Get all transactions");
    println!("   GET  /ledger/stats - Get ledger statistics");
    println!("   GET  /markets - List all prediction markets");
    println!("   GET  /markets/:id - Get specific market");
    println!("   POST /bet - Place a bet on a market");
    println!("   POST /resolve/:market_id/:winning_option - Resolve market (admin)");
    
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

// Handler functions
async fn health_check() -> Json<Value> {
    Json(json!({
        "status": "healthy",
        "service": "BlackBook Prediction Market",
        "version": "1.0.0",
        "timestamp": chrono::Utc::now().to_rfc3339()
    }))
}

async fn get_balance(
    State(state): State<SharedState>,
    Path(address): Path<String>
) -> Json<Value> {
    let app_state = state.lock().unwrap();
    let balance = app_state.ledger.get_balance(&address);
    
    Json(json!({
        "address": address,
        "balance": balance
    }))
}

async fn deposit_funds(
    State(state): State<SharedState>,
    Json(payload): Json<DepositRequest>
) -> Result<Json<Value>, StatusCode> {
    let mut app_state = state.lock().unwrap();
    
    let tx_id = app_state.ledger.deposit(&payload.address, payload.amount, &payload.memo);
    
    Ok(Json(json!({
        "success": true,
        "transaction_id": tx_id,
        "new_balance": app_state.ledger.get_balance(&payload.address)
    })))
}

async fn transfer_funds(
    State(state): State<SharedState>,
    Json(payload): Json<TransferRequest>
) -> Result<Json<Value>, StatusCode> {
    let mut app_state = state.lock().unwrap();
    
    match app_state.ledger.transfer(&payload.from, &payload.to, payload.amount, &payload.memo) {
        Ok(tx_id) => {
            Ok(Json(json!({
                "success": true,
                "transaction_id": tx_id,
                "from_balance": app_state.ledger.get_balance(&payload.from),
                "to_balance": app_state.ledger.get_balance(&payload.to)
            })))
        },
        Err(error) => {
            Ok(Json(json!({
                "success": false,
                "error": error
            })))
        }
    }
}

async fn get_user_transactions(
    State(state): State<SharedState>,
    Path(address): Path<String>
) -> Json<Value> {
    let app_state = state.lock().unwrap();
    let transactions = app_state.ledger.get_transactions_for_user(&address);
    
    Json(json!({
        "address": address,
        "transactions": transactions,
        "count": transactions.len()
    }))
}

async fn get_all_transactions(
    State(state): State<SharedState>
) -> Json<Value> {
    let app_state = state.lock().unwrap();
    let transactions = app_state.ledger.get_all_transactions();
    
    Json(json!({
        "transactions": transactions,
        "count": transactions.len()
    }))
}

async fn get_ledger_stats(
    State(state): State<SharedState>
) -> Json<Value> {
    let app_state = state.lock().unwrap();
    let stats = app_state.ledger.get_stats();
    
    Json(json!({
        "ledger_stats": stats
    }))
}

async fn place_bet(
    State(state): State<SharedState>,
    Json(payload): Json<BetRequest>
) -> Result<Json<Value>, StatusCode> {
    // First, get the market info without borrowing mutably
    let (market_title, market_option, is_resolved, valid_option) = {
        let app_state = state.lock().unwrap();
        
        let market = match app_state.markets.get(&payload.market) {
            Some(m) => m,
            None => return Err(StatusCode::NOT_FOUND)
        };
        
        let valid_option = payload.outcome < market.options.len();
        let market_option = if valid_option { 
            market.options[payload.outcome].clone() 
        } else { 
            String::new() 
        };
        
        (market.title.clone(), market_option, market.is_resolved, valid_option)
    };
    
    // Check if market is resolved
    if is_resolved {
        return Ok(Json(json!({
            "success": false,
            "message": "Market is already resolved"
        })));
    }
    
    // Check if option index is valid
    if !valid_option {
        return Ok(Json(json!({
            "success": false,
            "message": "Invalid outcome index"
        })));
    }
    
    // Now place the bet with mutable access
    let mut app_state = state.lock().unwrap();
    match app_state.ledger.place_bet(&payload.account, &payload.market, payload.outcome, payload.amount) {
        Ok(tx_id) => {
            let user_balance = app_state.ledger.get_balance(&payload.account);
            
            // Track the bet and check for leaderboard promotion
            if let Some(market) = app_state.markets.get_mut(&payload.market) {
                market.record_bet(&payload.account, payload.amount);
                
                let on_leaderboard = market.on_leaderboard;
                let unique_bettors = market.unique_bettors.len();
                
                Ok(Json(json!({
                    "success": true,
                    "transaction_id": tx_id,
                    "bet": {
                        "market": market_title,
                        "outcome": market_option,
                        "amount": payload.amount
                    },
                    "new_balance": user_balance,
                    "market_progress": {
                        "unique_bettors": unique_bettors,
                        "bettors_needed_for_leaderboard": 10,
                        "on_leaderboard": on_leaderboard,
                        "promotion_message": if on_leaderboard && unique_bettors == 10 {
                            "🎉 Market promoted to leaderboard!".to_string()
                        } else if !on_leaderboard && unique_bettors >= 10 {
                            "".to_string()
                        } else {
                            format!("{} more bettors needed for leaderboard", 10 - unique_bettors)
                        }
                    }
                })))
            } else {
                Ok(Json(json!({
                    "success": false,
                    "message": "Market not found"
                })))
            }
        },
        Err(error) => {
            Ok(Json(json!({
                "success": false,
                "message": error
            })))
        }
    }
}

async fn resolve_market(
    State(state): State<SharedState>,
    Path((market_id, winning_option)): Path<(String, usize)>
) -> Result<Json<Value>, StatusCode> {
    // First get market info and escrow balance without mutable borrow
    let (market_title, winning_option_text, escrow_balance) = {
        let app_state = state.lock().unwrap();
        
        // Get the market
        let market = match app_state.markets.get(&market_id) {
            Some(m) => m,
            None => return Err(StatusCode::NOT_FOUND)
        };
        
        // Check if already resolved
        if market.is_resolved {
            return Ok(Json(json!({
                "success": false,
                "error": "Market is already resolved"
            })));
        }
        
        // Check if winning option is valid
        if winning_option >= market.options.len() {
            return Ok(Json(json!({
                "success": false,
                "error": "Invalid winning option index"
            })));
        }
        
        // Get data before mutation
        let escrow_balance = app_state.ledger.get_balance(&market.escrow_address);
        let market_title = market.title.clone();
        let winning_option_text = market.options[winning_option].clone();
        
        (market_title, winning_option_text, escrow_balance)
    };
    
    // Now get mutable access to mark as resolved
    {
        let mut app_state = state.lock().unwrap();
        let market = app_state.markets.get_mut(&market_id).unwrap(); // We already checked it exists
        market.is_resolved = true;
        market.winning_option = Some(winning_option);
    }
    
    // For demo purposes, we'll just resolve without actual payout logic
    // In a real system, you'd track individual bets and pay out winners
    
    Ok(Json(json!({
        "success": true,
        "message": format!("Market '{}' resolved with winning option: {}", market_title, winning_option_text),
        "winning_option": winning_option,
        "total_escrow": escrow_balance
    })))
}

/// Create a new prediction market - EASY market creation
async fn create_market(
    State(state): State<SharedState>,
    Json(payload): Json<CreateMarketRequest>
) -> Result<Json<Value>, StatusCode> {
    // Validate input
    if payload.title.is_empty() || payload.title.len() > 200 {
        return Ok(Json(json!({
            "success": false,
            "error": "Title must be 1-200 characters"
        })));
    }
    
    if payload.description.is_empty() || payload.description.len() > 1000 {
        return Ok(Json(json!({
            "success": false,
            "error": "Description must be 1-1000 characters"
        })));
    }
    
    if payload.options.len() < 2 || payload.options.len() > 5 {
        return Ok(Json(json!({
            "success": false,
            "error": "Must have 2-5 options"
        })));
    }
    
    // Generate unique market ID
    let market_id = format!(
        "market_{}_{}",
        payload.title.to_lowercase().replace(" ", "_").chars().take(30).collect::<String>(),
        Uuid::new_v4().simple()
    );
    
    let mut app_state = state.lock().unwrap();
    
    // Create new market
    let new_market = PredictionMarket::new(
        market_id.clone(),
        payload.title.clone(),
        payload.description.clone(),
        payload.category.clone(),
        payload.options.clone(),
    );
    
    app_state.markets.insert(market_id.clone(), new_market);
    
    Ok(Json(json!({
        "success": true,
        "market_id": market_id,
        "title": payload.title,
        "category": payload.category,
        "message": "✅ Market created! Start betting to reach the leaderboard."
    })))
}

/// Get markets (optionally filtered by category)
async fn get_markets(
    State(state): State<SharedState>
) -> Json<Value> {
    let app_state = state.lock().unwrap();
    
    let markets: Vec<_> = app_state.markets
        .values()
        .map(|m| json!({
            "id": m.id,
            "title": m.title,
            "category": m.category,
            "description": m.description,
            "options": m.options,
            "total_volume": m.total_volume,
            "unique_bettors": m.unique_bettors.len(),
            "bet_count": m.bet_count,
            "on_leaderboard": m.on_leaderboard,
            "is_resolved": m.is_resolved,
        }))
        .collect();
    
    Json(json!({
        "markets": markets,
        "count": markets.len()
    }))
}

/// Get a specific market by ID
async fn get_market(
    State(state): State<SharedState>,
    Path(market_id): Path<String>
) -> Result<Json<Value>, StatusCode> {
    let app_state = state.lock().unwrap();
    
    match app_state.markets.get(&market_id) {
        Some(market) => {
            Ok(Json(json!({
                "success": true,
                "market": {
                    "id": market.id,
                    "title": market.title,
                    "category": market.category,
                    "description": market.description,
                    "options": market.options,
                    "total_volume": market.total_volume,
                    "unique_bettors": market.unique_bettors.len(),
                    "bet_count": market.bet_count,
                    "on_leaderboard": market.on_leaderboard,
                    "is_resolved": market.is_resolved,
                    "winning_option": market.winning_option,
                    "created_at": market.created_at,
                }
            })))
        }
        None => Err(StatusCode::NOT_FOUND)
    }
}

/// Get leaderboard - Markets with 10+ bettors, sorted by volume
async fn get_leaderboard(
    State(state): State<SharedState>
) -> Json<Value> {
    let app_state = state.lock().unwrap();
    
    let mut featured: Vec<LeaderboardEntry> = app_state.markets
        .values()
        .filter(|m| m.on_leaderboard)  // Only markets with 10+ bettors
        .map(|m| LeaderboardEntry {
            market_id: m.id.clone(),
            title: m.title.clone(),
            category: m.category.clone(),
            total_volume: m.total_volume,
            unique_bettors: m.unique_bettors.len(),
            bet_count: m.bet_count,
        })
        .collect();
    
    // Sort by volume (descending)
    featured.sort_by(|a, b| b.total_volume.partial_cmp(&a.total_volume).unwrap());
    
    Json(json!({
        "leaderboard": featured,
        "count": featured.len(),
        "threshold": "Markets must have 10+ unique bettors to appear here"
    }))
}

/// Get leaderboard by category
async fn get_leaderboard_by_category(
    State(state): State<SharedState>,
    Path(category): Path<String>
) -> Json<Value> {
    let app_state = state.lock().unwrap();
    
    let mut featured: Vec<LeaderboardEntry> = app_state.markets
        .values()
        .filter(|m| m.on_leaderboard && m.category.to_lowercase() == category.to_lowercase())
        .map(|m| LeaderboardEntry {
            market_id: m.id.clone(),
            title: m.title.clone(),
            category: m.category.clone(),
            total_volume: m.total_volume,
            unique_bettors: m.unique_bettors.len(),
            bet_count: m.bet_count,
        })
        .collect();
    
    // Sort by volume (descending)
    featured.sort_by(|a, b| b.total_volume.partial_cmp(&a.total_volume).unwrap());
    
    Json(json!({
        "category": category,
        "leaderboard": featured,
        "count": featured.len(),
    }))
}

// ===== SIMPLE SCRAPER HANDLER =====

/// Scrape a URL and create a prediction market
async fn scrape_and_create_market(
    State(state): State<SharedState>,
    Json(payload): Json<ScrapeRequest>,
) -> Result<Json<Value>, StatusCode> {
    // Scrape the URL
    let event = scraper::scrape_url(&payload.url)
        .await
        .map_err(|e| {
            eprintln!("❌ Scraping failed: {}", e);
            StatusCode::BAD_REQUEST
        })?;

    // Create a market from the scraped event
    let market_id = format!(
        "market_{}_{}",
        payload.title.to_lowercase().replace(" ", "_").chars().take(30).collect::<String>(),
        Uuid::new_v4().simple()
    );

    let mut market = PredictionMarket::new(
        market_id.clone(),
        payload.title,
        format!("{}\n\nSource: {}", event.description, event.url),
        payload.category,
        vec!["Yes".to_string(), "No".to_string()],
    );

    let mut app_state = state.lock().unwrap();
    app_state.markets.insert(market_id.clone(), market);

    println!("✅ Created market from scraped event: {}", market_id);

    Ok(Json(json!({
        "success": true,
        "market_id": market_id,
        "scraped_event": {
            "title": event.title,
            "description": event.description,
            "date": event.date,
            "url": event.url
        },
        "message": "Market created! Users can now bet on this event."
    })))
}

/// Get live Bitcoin market from CoinDesk API
async fn get_live_btc_market(
    State(state): State<SharedState>,
) -> Json<Value> {
    let client = {
        let app_state = state.lock().unwrap();
        app_state.coindesk.clone()
    };

    match client.create_or_update_btc_market().await {
        Ok(market) => Json(json!({
            "success": true,
            "market": {
                "market_id": market.market_id,
                "asset": market.asset,
                "current_price": market.current_price,
                "entry_price": market.entry_price,
                "entry_time": market.entry_time,
                "remaining_seconds": market.remaining_seconds,
                "duration_seconds": market.duration_seconds,
                "odds": {
                    "higher": market.odds.higher,
                    "lower": market.odds.lower,
                },
                "total_bets_higher": market.total_bets_higher,
                "total_bets_lower": market.total_bets_lower,
                "total_volume": market.total_volume,
            }
        })),
        Err(e) => {
            eprintln!("❌ Failed to get live BTC market: {}", e);
            Json(json!({
                "success": false,
                "error": e
            }))
        }
    }
}

/// Get real-time Bitcoin price from CoinGecko
async fn get_bitcoin_price(
    State(state): State<SharedState>,
) -> Json<Value> {
    let client = {
        let app_state = state.lock().unwrap();
        app_state.coindesk.clone()
    };

    match client.get_bitcoin_price().await {
        Ok(price) => Json(json!({
            "success": true,
            "asset": "Bitcoin",
            "symbol": "BTC",
            "price": price
        })),
        Err(e) => {
            eprintln!("❌ Failed to get Bitcoin price: {}", e);
            Json(json!({
                "success": false,
                "error": e
            }))
        }
    }
}

/// Get real-time Solana price from CoinGecko
async fn get_solana_price(
    State(state): State<SharedState>,
) -> Json<Value> {
    let client = {
        let app_state = state.lock().unwrap();
        app_state.coindesk.clone()
    };

    match client.get_solana_price().await {
        Ok(price) => Json(json!({
            "success": true,
            "asset": "Solana",
            "symbol": "SOL",
            "price": price
        })),
        Err(e) => {
            eprintln!("❌ Failed to get Solana price: {}", e);
            Json(json!({
                "success": false,
                "error": e
            }))
        }
    }
}
