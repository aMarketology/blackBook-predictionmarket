use axum::{
    extract::Path,
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use serde::Deserialize;
use serde_json::{json, Value};
use std::{net::SocketAddr, sync::Arc};
use tokio::sync::RwLock;
use tower_http::cors::{Any, CorsLayer};

mod blockchain;
use blockchain::Blockchain;

#[derive(Debug, Deserialize)]
struct BetRequest {
    account: String,
    market: String,
    outcome: usize,
    amount: u64,
}

#[derive(Debug, Deserialize)]
struct TransferRequest {
    from: String,
    to: String,
    amount: u64,
}

#[derive(Debug, Deserialize)]
struct AddBalanceRequest {
    account: String,
    amount: u64,
}

type AppState = Arc<RwLock<Blockchain>>;

// Health check
async fn health() -> Json<Value> {
    Json(json!({
        "status": "healthy",
        "service": "BlackBook God Mode Blockchain",
        "version": "1.0.0",
        "total_bb_tokens": 21000,
        "accounts": 8
    }))
}

// Get all accounts
async fn get_accounts(state: axum::extract::State<AppState>) -> Json<Value> {
    let blockchain = state.read().await;
    let accounts: Vec<_> = blockchain.list_accounts().into_iter().map(|acc| {
        json!({
            "name": acc.name,
            "address": acc.address,
            "balance": acc.balance
        })
    }).collect();
    
    Json(json!({
        "accounts": accounts,
        "total_accounts": accounts.len()
    }))
}

// Get specific account
async fn get_account(
    Path(name): Path<String>,
    state: axum::extract::State<AppState>
) -> Result<Json<Value>, StatusCode> {
    let blockchain = state.read().await;
    match blockchain.get_account(&name) {
        Some(account) => {
            let bets: Vec<_> = blockchain.get_bets_for_account(&name).into_iter().map(|bet| {
                json!({
                    "id": bet.id,
                    "market_id": bet.market_id,
                    "outcome_index": bet.outcome_index,
                    "amount": bet.amount,
                    "potential_payout": bet.potential_payout,
                    "timestamp": bet.timestamp
                })
            }).collect();

            Ok(Json(json!({
                "name": account.name,
                "address": account.address,
                "balance": account.balance,
                "bets": bets,
                "total_bets": bets.len()
            })))
        }
        None => Err(StatusCode::NOT_FOUND)
    }
}

// Get all markets
async fn get_markets(state: axum::extract::State<AppState>) -> Json<Value> {
    let blockchain = state.read().await;
    let markets: Vec<_> = blockchain.list_markets().into_iter().map(|market| {
        json!({
            "id": market.id,
            "title": market.title,
            "description": market.description,
            "outcomes": market.outcomes,
            "odds": market.odds,
            "total_volume": market.total_volume,
            "is_active": market.is_active
        })
    }).collect();
    
    Json(json!({
        "markets": markets,
        "total_markets": markets.len()
    }))
}

// Get specific market with live info
async fn get_market(
    Path(id): Path<String>,
    state: axum::extract::State<AppState>
) -> Result<Json<Value>, StatusCode> {
    let blockchain = state.read().await;
    match blockchain.get_market(&id) {
        Some(market) => {
            let mut response = json!({
                "id": market.id,
                "title": market.title,
                "description": market.description,
                "outcomes": market.outcomes,
                "odds": market.odds,
                "total_volume": market.total_volume,
                "is_active": market.is_active
            });

            // Add live info for Solana markets
            if let Some(live_info) = blockchain.get_live_market_info(&id) {
                response["live_info"] = json!(live_info);
                response["is_live"] = json!(true);
                if id.contains("solana") {
                    response["current_price"] = json!(blockchain.get_live_solana_price());
                }
            }

            Ok(Json(response))
        },
        None => Err(StatusCode::NOT_FOUND)
    }
}

// Place a bet
async fn place_bet(
    state: axum::extract::State<AppState>,
    Json(payload): Json<BetRequest>
) -> Result<Json<Value>, StatusCode> {
    let mut blockchain = state.write().await;
    match blockchain.place_bet(&payload.account, &payload.market, payload.outcome, payload.amount) {
        Ok(message) => Ok(Json(json!({
            "success": true,
            "message": message,
            "bet": {
                "account": payload.account,
                "market": payload.market,
                "outcome": payload.outcome,
                "amount": payload.amount
            }
        }))),
        Err(error) => Ok(Json(json!({
            "success": false,
            "error": error
        })))
    }
}

// Add balance to account
async fn add_balance(
    state: axum::extract::State<AppState>,
    Json(payload): Json<AddBalanceRequest>
) -> Result<Json<Value>, StatusCode> {
    let mut blockchain = state.write().await;
    match blockchain.add_balance(&payload.account, payload.amount) {
        Ok(message) => Ok(Json(json!({
            "success": true,
            "message": message
        }))),
        Err(error) => Ok(Json(json!({
            "success": false,
            "error": error
        })))
    }
}

// Transfer between accounts
async fn transfer(
    state: axum::extract::State<AppState>,
    Json(payload): Json<TransferRequest>
) -> Result<Json<Value>, StatusCode> {
    let mut blockchain = state.write().await;
    match blockchain.transfer(&payload.from, &payload.to, payload.amount) {
        Ok(message) => Ok(Json(json!({
            "success": true,
            "message": message
        }))),
        Err(error) => Ok(Json(json!({
            "success": false,
            "error": error
        })))
    }
}

// Get live Solana price
async fn get_solana_price(state: axum::extract::State<AppState>) -> Json<Value> {
    let blockchain = state.read().await;
    let current_price = blockchain.get_live_solana_price();
    let timestamp = chrono::Utc::now();
    
    Json(json!({
        "symbol": "SOL",
        "price": current_price,
        "currency": "USD",
        "timestamp": timestamp.to_rfc3339(),
        "next_update_in_seconds": 60 - (timestamp.timestamp() % 60),
        "live_markets": [
            {
                "id": "solana_price_1min_up",
                "title": "SOL Price UP in 1 minute",
                "current_price": current_price,
                "next_settlement": "60 seconds"
            },
            {
                "id": "solana_price_5min_up", 
                "title": "SOL Price UP in 5 minutes",
                "current_price": current_price,
                "next_settlement": "5 minutes"
            },
            {
                "id": "solana_price_breakout",
                "title": "SOL breaks $200 today",
                "current_price": current_price,
                "target": 200.0,
                "distance_to_target": 200.0 - current_price
            }
        ]
    }))
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize tracing
    tracing_subscriber::fmt::init();

    // Create blockchain with god mode
    let blockchain = Arc::new(RwLock::new(Blockchain::new()));

    // Build router
    let app = Router::new()
        .route("/", get(|| async { 
            Json(json!({
                "service": "BlackBook God Mode Blockchain",
                "version": "1.0.0",
                "description": "Terminal-controlled prediction market blockchain",
                "god_mode": true,
                "total_bb_tokens": 21000,
                "commands": {
                    "GET": {
                        "/health": "Health check",
                        "/accounts": "List all accounts",
                        "/accounts/{name}": "Get account details",
                        "/markets": "List all markets",
                        "/markets/{id}": "Get market details"
                    },
                    "POST": {
                        "/bet": "Place bet - {\"account\": \"alice\", \"market\": \"nvidia_200\", \"outcome\": 0, \"amount\": 100}",
                        "/add-balance": "Add balance - {\"account\": \"alice\", \"amount\": 1000}",
                        "/transfer": "Transfer tokens - {\"from\": \"alice\", \"to\": \"bob\", \"amount\": 100}"
                    }
                },
                "example_commands": [
                    "curl -X POST http://localhost:3000/bet -H \"Content-Type: application/json\" -d \"{\\\"account\\\": \\\"alice\\\", \\\"market\\\": \\\"nvidia_200\\\", \\\"outcome\\\": 0, \\\"amount\\\": 100}\"",
                    "curl -X POST http://localhost:3000/add-balance -H \"Content-Type: application/json\" -d \"{\\\"account\\\": \\\"alice\\\", \\\"amount\\\": 1000}\"",
                    "curl http://localhost:3000/accounts/alice"
                ]
            }))
        }))
        .route("/health", get(health))
        .route("/accounts", get(get_accounts))
        .route("/accounts/:name", get(get_account))
        .route("/markets", get(get_markets))
        .route("/markets/:id", get(get_market))
        .route("/bet", post(place_bet))
        .route("/add-balance", post(add_balance))
        .route("/transfer", post(transfer))
        .route("/solana-price", get(get_solana_price))
        .layer(CorsLayer::new().allow_origin(Any).allow_methods(Any).allow_headers(Any))
        .with_state(blockchain);

    // Start server
    let addr = SocketAddr::from(([127, 0, 0, 1], 3000));
    
    println!("🏆 BlackBook God Mode Blockchain Starting!");
    println!("===============================================");
    println!("🌐 Server: http://localhost:3000");
    println!("💰 Total BB Tokens: 21,000");
    println!("👥 Accounts: 8 (alice, bob, charlie, diana, eve, frank, grace, henry)");
    println!("📊 Markets: 23 REAL events + 🚀 LIVE Solana price betting!");
    println!("");
    println!("🎯 Example Commands (23 Markets + LIVE Solana Betting!):");
    println!("# 🚀 LIVE SOLANA BETTING (Updates every minute!)");
    println!("curl -X POST http://localhost:3000/bet -H \"Content-Type: application/json\" \\");
    println!("  -d '{{\"account\": \"alice\", \"market\": \"solana_price_1min_up\", \"outcome\": 0, \"amount\": 50}}'");
    println!("");
    println!("# Samsung XR Headset (Oct 21, 2025)");
    println!("curl -X POST http://localhost:3000/bet -H \"Content-Type: application/json\" \\");
    println!("  -d '{{\"account\": \"bob\", \"market\": \"samsung_xr_4k\", \"outcome\": 0, \"amount\": 100}}'");
    println!("");
    println!("# Check account status");
    println!("curl http://localhost:3000/accounts/alice");
    println!("");
    println!("# List all 20 real tech event markets");
    println!("curl http://localhost:3000/markets");
    println!("");
    println!("🚀 Ready for god mode commands!");

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}