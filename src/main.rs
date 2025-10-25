use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use serde::Deserialize;
use serde_json::{json, Value};
use std::{net::SocketAddr, sync::{Arc, Mutex}, collections::HashMap};
use tower_http::cors::{Any, CorsLayer};

mod ledger;
use ledger::Ledger;

// Simple prediction market struct
#[derive(Debug, serde::Serialize)]
pub struct PredictionMarket {
    pub id: String,
    pub title: String,
    pub description: String,
    pub options: Vec<String>,
    pub is_resolved: bool,
    pub winning_option: Option<usize>,
    pub escrow_address: String, // The market's escrow account
    pub created_at: u64,
}

// Application state - just a ledger and markets
#[derive(Debug)]
pub struct AppState {
    pub ledger: Ledger,
    pub markets: HashMap<String, PredictionMarket>,
}

impl AppState {
    pub fn new() -> Self {
        let mut state = Self {
            ledger: Ledger::new(),
            markets: HashMap::new(),
        };
        
        // Initialize with some demo accounts
        state.ledger.deposit("alice", 1000.0, "Initial demo balance");
        state.ledger.deposit("bob", 500.0, "Initial demo balance");
        state.ledger.deposit("charlie", 750.0, "Initial demo balance");
        
        // Create some sample prediction markets
        state.create_sample_markets();
        
        state
    }
    
    fn create_sample_markets(&mut self) {
        // Tech prediction market
        let market_id = "tech_ai_breakthrough_2025".to_string();
        self.markets.insert(market_id.clone(), PredictionMarket {
            id: market_id.clone(),
            title: "Major AI Breakthrough in 2025".to_string(),
            description: "Will there be a major AI breakthrough (AGI, solved alignment, etc.) announced by a major tech company in 2025?".to_string(),
            options: vec!["Yes".to_string(), "No".to_string()],
            is_resolved: false,
            winning_option: None,
            escrow_address: format!("MARKET_{}", market_id),
            created_at: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs(),
        });
        
        // Business prediction market
        let market_id = "business_recession_2025".to_string();
        self.markets.insert(market_id.clone(), PredictionMarket {
            id: market_id.clone(),
            title: "US Recession in 2025".to_string(),
            description: "Will the United States officially enter a recession in 2025?".to_string(),
            options: vec!["Yes".to_string(), "No".to_string()],
            is_resolved: false,
            winning_option: None,
            escrow_address: format!("MARKET_{}", market_id),
            created_at: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs(),
        });
        
        // Crypto prediction market
        let market_id = "crypto_bitcoin_100k".to_string();
        self.markets.insert(market_id.clone(), PredictionMarket {
            id: market_id.clone(),
            title: "Bitcoin reaches $100K in 2025".to_string(),
            description: "Will Bitcoin (BTC) reach $100,000 USD at any point during 2025?".to_string(),
            options: vec!["Yes".to_string(), "No".to_string()],
            is_resolved: false,
            winning_option: None,
            escrow_address: format!("MARKET_{}", market_id),
            created_at: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs(),
        });
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
struct BetRequest {
    user_address: String,
    market_id: String,
    option_index: usize,
    amount: f64,
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
        .route("/markets/:id", get(get_market))
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

async fn get_markets(
    State(state): State<SharedState>
) -> Json<Value> {
    let app_state = state.lock().unwrap();
    let markets: Vec<&PredictionMarket> = app_state.markets.values().collect();
    
    Json(json!({
        "markets": markets,
        "count": markets.len()
    }))
}

async fn get_market(
    State(state): State<SharedState>,
    Path(market_id): Path<String>
) -> Result<Json<Value>, StatusCode> {
    let app_state = state.lock().unwrap();
    
    match app_state.markets.get(&market_id) {
        Some(market) => {
            let escrow_balance = app_state.ledger.get_balance(&market.escrow_address);
            
            Ok(Json(json!({
                "market": market,
                "escrow_balance": escrow_balance
            })))
        },
        None => Err(StatusCode::NOT_FOUND)
    }
}

async fn place_bet(
    State(state): State<SharedState>,
    Json(payload): Json<BetRequest>
) -> Result<Json<Value>, StatusCode> {
    // First, get the market info without borrowing mutably
    let (escrow_address, market_title, market_option, is_resolved, valid_option) = {
        let app_state = state.lock().unwrap();
        
        let market = match app_state.markets.get(&payload.market_id) {
            Some(m) => m,
            None => return Err(StatusCode::NOT_FOUND)
        };
        
        let valid_option = payload.option_index < market.options.len();
        let market_option = if valid_option { 
            market.options[payload.option_index].clone() 
        } else { 
            String::new() 
        };
        
        (market.escrow_address.clone(), market.title.clone(), market_option, market.is_resolved, valid_option)
    };
    
    // Check if market is resolved
    if is_resolved {
        return Ok(Json(json!({
            "success": false,
            "error": "Market is already resolved"
        })));
    }
    
    // Check if option index is valid
    if !valid_option {
        return Ok(Json(json!({
            "success": false,
            "error": "Invalid option index"
        })));
    }
    
    // Now place the bet with mutable access
    let mut app_state = state.lock().unwrap();
    match app_state.ledger.place_bet(&payload.user_address, &escrow_address, payload.amount) {
        Ok(tx_id) => {
            let user_balance = app_state.ledger.get_balance(&payload.user_address);
            let market_escrow = app_state.ledger.get_balance(&escrow_address);
            
            Ok(Json(json!({
                "success": true,
                "transaction_id": tx_id,
                "message": format!("Bet placed on '{}' for option: {}", market_title, market_option),
                "user_balance": user_balance,
                "market_escrow": market_escrow
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