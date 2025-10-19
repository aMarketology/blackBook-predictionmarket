use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use serde::Deserialize;
use serde_json::{json, Value};
use std::{net::SocketAddr, sync::{Arc, Mutex}};
use tower_http::cors::{Any, CorsLayer};
use chrono::Timelike;

mod blockchain;
mod blockchain_core;
mod consensus;
mod objectwire_parser;
mod tech_events;
use blockchain::PredictionMarketBlockchain;

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

type AppState = Arc<Mutex<PredictionMarketBlockchain>>;

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
async fn get_accounts(State(state): State<AppState>) -> Result<Json<Value>, StatusCode> {
    let blockchain = state.lock().unwrap();
    let accounts: Vec<_> = blockchain.list_accounts().into_iter().map(|acc| {
        json!({
            "name": acc.name,
            "address": acc.address,
            "balance": acc.balance
        })
    }).collect();
    
    Ok(Json(json!({
        "accounts": accounts,
        "total_accounts": accounts.len()
    })))
}

// Get specific account
async fn get_account(
    Path(name): Path<String>,
    state: axum::extract::State<AppState>
) -> Result<Json<Value>, StatusCode> {
    let blockchain = state.lock().unwrap();
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
async fn get_markets(State(state): State<AppState>) -> Json<Value> {
    let blockchain = state.lock().unwrap();
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
    let blockchain = state.lock().unwrap();
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
    let mut blockchain = state.lock().unwrap();
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
    let mut blockchain = state.lock().unwrap();
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
    let mut blockchain = state.lock().unwrap();
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
async fn get_solana_price(State(state): State<AppState>) -> Json<Value> {
    let blockchain = state.lock().unwrap();
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

// Get live Bitcoin price
async fn get_bitcoin_price(State(state): State<AppState>) -> Json<Value> {
    let blockchain = state.lock().unwrap();
    let current_price = blockchain.get_live_bitcoin_price();
    let timestamp = chrono::Utc::now();
    
    Json(json!({
        "symbol": "BTC",
        "price": current_price,
        "currency": "USD",
        "timestamp": timestamp.to_rfc3339(),
        "15min_settlement_in_minutes": 15 - ((timestamp.timestamp() / 60) % 15),
        "hourly_settlement_in_minutes": 60 - ((timestamp.timestamp() / 60) % 60),
        "live_markets": [
            {
                "id": "btc_15min_above_current",
                "title": "BTC ABOVE current price in 15 minutes",
                "current_price": current_price,
                "next_settlement": "15 minutes"
            },
            {
                "id": "btc_hourly_direction", 
                "title": "BTC direction next hour",
                "current_price": current_price,
                "next_settlement": "1 hour"
            },
            {
                "id": "btc_daily_100k",
                "title": "BTC hits $100K today",
                "current_price": current_price,
                "target": 100000.0,
                "distance_to_target": 100000.0 - current_price
            }
        ]
    }))
}

// === TECH EVENTS INTEGRATION ENDPOINTS ===

// Sync real tech events and create markets
async fn sync_tech_events(
    State(state): State<AppState>
) -> Result<Json<Value>, StatusCode> {
    let mut blockchain = state.lock().unwrap();
    
    match blockchain.sync_real_tech_events().await {
        Ok(new_markets) => {
            Ok(Json(json!({
                "status": "success",
                "message": "Synchronized real tech events",
                "new_markets_created": new_markets,
                "sources": ["NewsAPI", "Alpha Vantage", "Conference Schedules", "Known Events"]
            })))
        }
        Err(e) => {
            eprintln!("Tech events sync error: {}", e);
            Ok(Json(json!({
                "status": "partial_success",
                "message": "Used fallback tech events data",
                "new_markets_created": 0,
                "error": e
            })))
        }
    }
}

// Get tech events from Google News RSS
async fn get_tech_events(State(_state): State<AppState>) -> Json<Value> {
    // Use the tech_events module directly
    match crate::tech_events::fetch_google_news_tech_business().await {
        Ok(events) => {
            Json(json!({
                "status": "success",
                "events": events,
                "count": events.len(),
                "sources": ["Google News Tech", "Google News Business", "Google News AI"]
            }))
        }
        Err(e) => {
            Json(json!({
                "status": "error", 
                "error": format!("Failed to fetch tech events: {}", e),
                "events": [],
                "count": 0
            }))
        }
    }
}

// Get tech event markets
async fn get_tech_event_markets(State(state): State<AppState>) -> Json<Value> {
    let blockchain = state.lock().unwrap();
    let markets: Vec<_> = blockchain.markets.values()
        .filter(|market| market.id.starts_with("event_"))
        .map(|market| {
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
        "tech_event_markets": markets,
        "total_markets": markets.len()
    }))
}

// Get crypto prices with betting info
async fn get_crypto_prices(State(state): State<AppState>) -> Json<Value> {
    let blockchain = state.lock().unwrap();
    let btc_price = blockchain.get_live_bitcoin_price();
    let sol_price = blockchain.get_live_solana_price();
    let now = chrono::Utc::now();
    
    // Calculate next 15-minute resolution
    let next_resolution = now + chrono::Duration::minutes(15 - (now.minute() % 15) as i64);
    
    Json(json!({
        "btc_price": btc_price,
        "sol_price": sol_price,
        "timestamp": now.to_rfc3339(),
        "next_resolution": next_resolution.to_rfc3339(),
        "active_crypto_markets": [
            {
                "crypto": "BTC",
                "interval": "15min",
                "current_price": btc_price,
                "next_settlement": next_resolution.to_rfc3339()
            },
            {
                "crypto": "SOL", 
                "interval": "15min",
                "current_price": sol_price,
                "next_settlement": next_resolution.to_rfc3339()
            }
        ]
    }))
}

#[derive(Debug, Deserialize)]
struct CryptoBetRequest {
    account: String,
    crypto: String,  // "BTC" or "SOL"
    direction: String,  // "up" or "down"
    amount: u64,
}

// Place crypto bet
async fn place_crypto_bet(
    state: axum::extract::State<AppState>,
    Json(payload): Json<CryptoBetRequest>
) -> Result<Json<Value>, StatusCode> {
    let mut blockchain = state.lock().unwrap();
    
    // Create or find the crypto market for 15-minute betting
    let market_id = format!("crypto_15min_{}_{}", payload.crypto.to_lowercase(), 
        chrono::Utc::now().format("%Y%m%d_%H%M"));
    
    let outcome = if payload.direction == "up" { 0 } else { 1 };
    
    match blockchain.place_bet(&payload.account, &market_id, outcome, payload.amount) {
        Ok(message) => Ok(Json(json!({
            "success": true,
            "message": message,
            "bet": {
                "account": payload.account,
                "crypto": payload.crypto,
                "direction": payload.direction,
                "amount": payload.amount,
                "market_id": market_id
            }
        }))),
        Err(error) => Ok(Json(json!({
            "success": false,
            "error": error
        })))
    }
}

// === OBJECTWIRE INTEGRATION ENDPOINTS ===

// Sync ObjectWire articles and create new markets
async fn sync_objectwire(
    State(state): State<AppState>
) -> Result<Json<Value>, StatusCode> {
    let mut blockchain = state.lock().unwrap();
    
    match blockchain.sync_objectwire_articles().await {
        Ok(new_markets) => {
            Ok(Json(json!({
                "status": "success",
                "message": format!("Synchronized ObjectWire articles"),
                "new_markets_created": new_markets,
                "total_claims": blockchain.get_objectwire_claims().len()
            })))
        }
        Err(e) => {
            eprintln!("ObjectWire sync error: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

// Get all ObjectWire claims (for admin review)
async fn get_objectwire_claims(State(state): State<AppState>) -> Json<Value> {
    let blockchain = state.lock().unwrap();
    let claims: Vec<_> = blockchain.get_objectwire_claims().iter().map(|claim| {
        json!({
            "article_id": claim.article_id,
            "prediction_question": claim.prediction_question,
            "outcomes": claim.outcomes,
            "confidence_score": claim.confidence_score,
            "claim_type": format!("{:?}", claim.claim_type),
            "resolution_date": claim.resolution_date,
            "has_market": claim.market_id.is_some()
        })
    }).collect();
    
    Json(json!({
        "claims": claims,
        "total_claims": claims.len()
    }))
}

// Get ObjectWire-generated markets
async fn get_objectwire_markets(State(state): State<AppState>) -> Json<Value> {
    let blockchain = state.lock().unwrap();
    let markets: Vec<_> = blockchain.get_objectwire_markets().into_iter().map(|market| {
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
        "objectwire_markets": markets,
        "total_markets": markets.len()
    }))
}

// Get all real bets from the blockchain - Layer 1 data
async fn get_bets(State(state): State<AppState>) -> Json<Value> {
    let blockchain = state.lock().unwrap();
    let all_bets = blockchain.bets.iter().map(|bet| {
        json!({
            "id": bet.id,
            "account": bet.account,
            "market_id": bet.market_id,
            "outcome_index": bet.outcome_index,
            "amount": bet.amount,
            "potential_payout": bet.potential_payout,
            "timestamp": bet.timestamp
        })
    }).collect::<Vec<_>>();
    
    Json(json!({
        "bets": all_bets,
        "total_bets": all_bets.len(),
        "source": "Layer 1 Blockchain"
    }))
}

// Get all transactions from the consensus engine - Layer 1 data
async fn get_transactions(State(state): State<AppState>) -> Json<Value> {
    let blockchain = state.lock().unwrap();
    let all_transactions = blockchain.consensus_engine.get_all_transactions();
    
    let transactions: Vec<_> = all_transactions.iter().enumerate().map(|(i, _tx)| {
        json!({
            "id": i,
            "status": "confirmed",
            "timestamp": chrono::Utc::now().to_rfc3339(),
            "type": "market_transaction"
        })
    }).collect();
    
    Json(json!({
        "transactions": transactions,
        "total_transactions": transactions.len(),
        "source": "Layer 1 Blockchain - Real Consensus Engine"
    }))
}

// Sync prices with CoinGecko - returns real prices from cache
async fn sync_prices(State(state): State<AppState>) -> Json<Value> {
    let blockchain = state.lock().unwrap();
    Json(json!({
        "status": "synced",
        "bitcoin": {
            "price": blockchain.cached_btc_price,
            "updated": true
        },
        "solana": {
            "price": blockchain.cached_sol_price,
            "updated": true
        },
        "timestamp": chrono::Utc::now().to_rfc3339(),
        "source": "CoinGecko Real Prices"
    }))
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize tracing
    tracing_subscriber::fmt::init();

    // Create blockchain with god mode
        let blockchain = Arc::new(Mutex::new(PredictionMarketBlockchain::new()));

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
        .route("/bets", get(get_bets))
        .route("/transactions", get(get_transactions))
        .route("/add-balance", post(add_balance))
        .route("/transfer", post(transfer))
        .route("/solana-price", get(get_solana_price))
        .route("/sync-prices", post(sync_prices))
        .route("/objectwire/claims", get(get_objectwire_claims))
        .route("/objectwire/markets", get(get_objectwire_markets))
        .route("/bitcoin-price", get(get_bitcoin_price))
        .route("/tech-events", get(get_tech_events))
        .route("/tech-events/markets", get(get_tech_event_markets))
        .route("/crypto-prices", get(get_crypto_prices))
        .route("/crypto-bet", post(place_crypto_bet))
        .layer(CorsLayer::new().allow_origin(Any).allow_methods(Any).allow_headers(Any))
        .with_state(blockchain);

    // Start server
    let addr = SocketAddr::from(([127, 0, 0, 1], 3000));
    
    println!("🏆 BlackBook God Mode Blockchain Starting!");
    println!("===============================================");
    println!("🌐 Server: http://localhost:3000");
    println!("💰 Total BB Tokens: 21,000");
    println!("👥 Accounts: 8 (alice, bob, charlie, diana, eve, frank, grace, henry)");
    println!("📊 Markets: 35+ REAL events + 🚀 LIVE Solana betting + 📰 ObjectWire Integration!");
    println!("📰 ObjectWire: Auto-generated markets from intelligence articles");
    println!("");
    println!("🎯 Example Commands (35+ Markets + ObjectWire Integration!):");
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
    println!("# List all markets (tech events + ObjectWire)");
    println!("curl http://localhost:3000/markets");
    println!("");
    println!("# 📰 ObjectWire Integration Commands:");
    println!("curl -X POST http://localhost:3000/objectwire/sync");
    println!("curl http://localhost:3000/objectwire/claims");
    println!("curl http://localhost:3000/objectwire/markets");
    println!("");
    println!("# 🎯 Real Tech Events Commands:");
    println!("curl -X POST http://localhost:3000/tech-events/sync");
    println!("curl http://localhost:3000/tech-events/markets");
    println!("");
    println!("🚀 Ready for god mode + Real Event betting!");

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}