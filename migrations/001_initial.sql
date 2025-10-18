-- Create markets table
CREATE TABLE IF NOT EXISTS markets (
    id TEXT PRIMARY KEY NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    creator TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('Open', 'Closed', 'Resolved', 'Cancelled')),
    outcomes TEXT NOT NULL, -- JSON serialized outcomes
    total_volume DECIMAL NOT NULL DEFAULT 0,
    liquidity_pool DECIMAL NOT NULL DEFAULT 0,
    resolution_source TEXT,
    resolved_outcome TEXT,
    created_at DATETIME NOT NULL,
    closes_at DATETIME NOT NULL,
    resolves_at DATETIME
);

-- Create bets table
CREATE TABLE IF NOT EXISTS bets (
    id TEXT PRIMARY KEY NOT NULL,
    market_id TEXT NOT NULL,
    user_address TEXT NOT NULL,
    outcome_id TEXT NOT NULL,
    amount DECIMAL NOT NULL,
    shares_bought DECIMAL NOT NULL,
    price_per_share DECIMAL NOT NULL,
    transaction_hash TEXT,
    placed_at DATETIME NOT NULL,
    FOREIGN KEY (market_id) REFERENCES markets (id) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_markets_category ON markets(category);
CREATE INDEX IF NOT EXISTS idx_markets_state ON markets(state);
CREATE INDEX IF NOT EXISTS idx_markets_created_at ON markets(created_at);
CREATE INDEX IF NOT EXISTS idx_markets_closes_at ON markets(closes_at);

CREATE INDEX IF NOT EXISTS idx_bets_market_id ON bets(market_id);
CREATE INDEX IF NOT EXISTS idx_bets_user_address ON bets(user_address);
CREATE INDEX IF NOT EXISTS idx_bets_placed_at ON bets(placed_at);
CREATE INDEX IF NOT EXISTS idx_bets_market_user ON bets(market_id, user_address);

-- Create blockchain_transactions table for tracking on-chain activity
CREATE TABLE IF NOT EXISTS blockchain_transactions (
    id TEXT PRIMARY KEY NOT NULL,
    transaction_hash TEXT UNIQUE NOT NULL,
    market_id TEXT,
    bet_id TEXT,
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('CREATE_MARKET', 'PLACE_BET', 'RESOLVE_MARKET', 'WITHDRAW')),
    from_address TEXT NOT NULL,
    to_address TEXT,
    amount DECIMAL,
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'CONFIRMED', 'FAILED')) DEFAULT 'PENDING',
    block_number INTEGER,
    gas_used INTEGER,
    gas_price DECIMAL,
    created_at DATETIME NOT NULL,
    confirmed_at DATETIME,
    FOREIGN KEY (market_id) REFERENCES markets (id) ON DELETE SET NULL,
    FOREIGN KEY (bet_id) REFERENCES bets (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_blockchain_tx_hash ON blockchain_transactions(transaction_hash);
CREATE INDEX IF NOT EXISTS idx_blockchain_tx_status ON blockchain_transactions(status);
CREATE INDEX IF NOT EXISTS idx_blockchain_tx_market ON blockchain_transactions(market_id);