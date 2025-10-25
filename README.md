# 🏆 BlackBook Prediction Market - Layer 1 Integration

A sophisticated prediction market platform for business and technology events, integrated with BlackBook Layer 1 blockchain and 21,000 BB tokens.

## 🚀 Quick Start

### Option 1: Auto-Start (Recommended)
```bash
# Double-click start_blackbook.bat or run:
start_blackbook.bat
```

### Option 2: Manual Start
```bash
# Terminal 1: Start API Server
cargo run

# Terminal 2: Start Frontend Server  
python serve_frontend.py
```

## 📋 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Layer 1 Interface** | http://localhost:8080/blackbook-layer1.html | Advanced blockchain integration |
| **Basic Interface** | http://localhost:8080/index.html | Simple testing interface |
| **API Server** | http://localhost:3000 | Backend REST API |
| **API Documentation** | http://localhost:3000/ | API endpoints and features |

## 🎯 Testing Features

### 👥 8 Test Accounts
Control 8 different accounts simultaneously for comprehensive testing:

1. **Tech Analyst** - Focused on technology predictions
2. **Crypto Trader** - Cryptocurrency market expert  
3. **AI Researcher** - Artificial intelligence developments
4. **VC Investor** - Venture capital and startup funding
5. **Startup Founder** - Product launches and business events
6. **Market Maker** - Provides liquidity to markets
7. **News Editor** - Creates markets from news events
8. **Whale Trader** - Large volume trading (extra BB tokens)

### 💰 BlackBook Token Distribution
- **Total Supply**: 21,000 BB tokens
- **Per Account**: ~2,625 BB tokens (with variation)
- **Whale Account**: Extra 2,000 BB tokens for large bets
- **Admin Controls**: Redistribute, fund, and reset balances

## 📊 Sample Prediction Markets

### Stock & Market Predictions
- **NVIDIA $200 Target**: Will NVDA hit $200 by end of 2025?
- **Apple Vision Pro 2**: New product announcement in 2025?
- **S&P 500 Milestone**: Index above 6000 by year end?
- **$4T Market Cap Race**: First company to reach $4 trillion?

### Cryptocurrency Events  
- **Bitcoin $150k**: BTC crossing major milestone in 2025?
- **Regulatory Changes**: US crypto regulation passage?
- **DeFi Adoption**: Major institutional DeFi integration?

### Technology Milestones
- **OpenAI GPT-5**: Release before July 2025?
- **Tesla FSD**: Full self-driving achievement by Q3?
- **AGI Timeline**: Artificial General Intelligence by 2030?

### Business Events
- **Microsoft-Discord**: Major acquisition in 2025?
- **Stripe IPO**: Public offering timeline?
- **Apple-Tesla Partnership**: Strategic alliance announcement?

## 🛠️ Platform Features

### Advanced Trading
- **Order Types**: Market, Limit, Stop-Loss orders
- **Live Odds**: Real-time probability updates
- **Cash Out**: Early position closing
- **Portfolio Tracking**: P&L monitoring across accounts

### Risk Management  
- **Position Limits**: Maximum exposure per user
- **Circuit Breakers**: Automatic market suspension
- **Balance Verification**: Blockchain balance checks
- **Transaction History**: Complete audit trail

### Blockchain Integration
- **Layer 1 Connection**: Direct BlackBook blockchain integration
- **Wallet Management**: Switch between 8 test accounts
- **Transaction Verification**: All bets recorded on-chain
- **Smart Contracts**: Automated settlement and payouts

## 🔧 Admin Controls

### Market Management
- **Create Sample Markets**: Generate test prediction markets
- **Fund All Accounts**: Distribute BB tokens to all accounts
- **Check Balances**: Verify current token distribution
- **Reset Blockchain**: Clear all transactions and restart

### Development Tools
- **Deploy Test Contract**: Initialize smart contracts
- **Export Test Data**: Download complete test session
- **Monitor Transactions**: Track all blockchain activity
- **Debug Mode**: Detailed logging and error reporting

## 🎮 How to Test

### 1. Basic Setup
1. Run `start_blackbook.bat` to start both servers
2. Open http://localhost:8080/blackbook-layer1.html
3. Click "Connect to BlackBook Layer 1"
4. Verify connection status (API, Blockchain, Wallet all green)

### 2. Create Markets
1. Click "Create Sample Markets" in admin panel
2. Wait for markets to be created (watch console for progress)
3. Refresh to see new markets appear

### 3. Switch Accounts
1. Click any of the 8 test accounts in the sidebar
2. Watch wallet address and balance update
3. Each account has different BB token amounts

### 4. Place Bets
1. Select a market and outcome
2. Enter bet amount (in BB tokens)
3. Preview shows potential payout and profit
4. Click "Place Bet" to execute blockchain transaction
5. Watch for transaction confirmation

### 5. Monitor Results
1. Check portfolio for open positions
2. Monitor market statistics and volume
3. Track P&L across different accounts
4. Export data for analysis

## 🏗️ Architecture

### Backend (Rust)
- **Axum Web Framework**: High-performance async API
- **Supabase Integration**: PostgreSQL database with real-time features
- **Blockchain Module**: Layer 1 transaction handling
- **CSMM Algorithm**: Constant Sum Market Maker for pricing

### Frontend (HTML/JS)
- **Ethers.js**: Blockchain interaction library
- **Real-time Updates**: WebSocket connections for live data
- **Responsive Design**: Works on desktop and mobile
- **Multi-account Support**: Simultaneous account management

### Blockchain Layer
- **BlackBook Layer 1**: Custom blockchain for BB tokens
- **Smart Contracts**: Market creation and settlement
- **Transaction Verification**: All bets recorded immutably
- **Token Economics**: 21,000 BB total supply

## 📈 Market Categories

| Category | Icon | Examples |
|----------|------|----------|
| **Earnings** | 📊 | Quarterly reports, revenue targets |
| **Product Launch** | 🚀 | iPhone releases, software launches |
| **Acquisition** | 🤝 | M&A announcements, buyouts |
| **Stock Movement** | 📈 | Price targets, market milestones |
| **Crypto** | ₿ | Bitcoin prices, regulatory events |
| **AI Milestone** | 🤖 | AGI timeline, breakthrough achievements |
| **Index Movement** | 📉 | S&P 500, NASDAQ targets |
| **Regulation** | ⚖️ | Government policy, legal changes |

## 🚨 Troubleshooting

### Common Issues

**API Server Not Starting**
```bash
# Check if port 3000 is available
netstat -an | findstr :3000

# Run with debug logging
set RUST_LOG=debug & cargo run
```

**Frontend Connection Errors**
```bash
# Verify API server is running
curl http://localhost:3000/health

# Check CORS settings in main.rs
```

**Blockchain Connection Failed**
```bash
# Verify BlackBook Layer 1 RPC is running
curl -X POST -H "Content-Type: application/json" --data "{\"jsonrpc\":\"2.0\",\"method\":\"eth_blockNumber\",\"params\":[],\"id\":1}" http://localhost:8545
```

**Transaction Failures**
- Check account has sufficient BB tokens
- Verify market is still open for betting
- Ensure outcome selection is valid
- Check blockchain connection status

### Development Mode

```bash
# Enable debug logging
set RUST_LOG=debug

# Run with hot reload
cargo watch -x run

# Monitor database
# Check Supabase dashboard for real-time updates
```

## 🎉 Success Indicators

When everything is working correctly, you should see:

✅ **Connection Status**: All three dots (API, Blockchain, Wallet) are green  
✅ **Account Switching**: Seamless switching between 8 test accounts  
✅ **Market Creation**: Sample markets appear after clicking "Create Sample Markets"  
✅ **Betting**: Successful bet placement with transaction hash  
✅ **Balance Updates**: BB token balances decrease after bets  
✅ **Real-time Updates**: Market statistics update after bets  

## 🔮 Next Steps

### Phase 1: Core Functionality ✅
- [x] Basic market creation and betting
- [x] 8-account testing interface  
- [x] BlackBook Layer 1 integration
- [x] BB token management

### Phase 2: Advanced Features 🚧
- [ ] Real-time price feeds
- [ ] Advanced order types
- [ ] Portfolio analytics
- [ ] Mobile responsive design

### Phase 3: Production Ready 📋
- [ ] ObjectWire.org integration
- [ ] Security audit
- [ ] Performance optimization
- [ ] User documentation

---

**🎯 Ready to test the future of business prediction markets!**

Start with `start_blackbook.bat` and begin placing bets on tech events with real BlackBook tokens!
  -d '{
    "title": "Will Bitcoin reach $100k by end of 2024?",
    "description": "Prediction on Bitcoin price reaching $100,000 USD",
    "category": "cryptocurrency",
    "creator": "0x1234567890123456789012345678901234567890",
    "outcomes": ["Yes", "No"],
    "closes_at": "2024-12-31T23:59:59Z",
    "initial_liquidity": 1000
  }'
```

#### Place a Bet
```bash
curl -X POST http://localhost:3000/api/v1/markets/{market_id}/bet \
  -H "Content-Type: application/json" \
  -d '{
    "user_address": "0x1234567890123456789012345678901234567890",
    "outcome_id": "outcome_0",
    "amount": 100
  }'
```

#### List Markets
```bash
curl "http://localhost:3000/api/v1/markets?category=cryptocurrency&limit=10"
```

## Market Mechanics

### Automated Market Maker (AMM)

The system uses a **Logarithmic Market Scoring Rule (LMSR)** for pricing:

- **Fair Pricing**: Prices automatically adjust based on supply and demand
- **Liquidity**: Always provides liquidity for trading
- **Incentive Compatible**: Rewards accurate predictions

### Market States

- **Open**: Market is accepting bets
- **Closed**: Market closed for betting, awaiting resolution
- **Resolved**: Market resolved with winning outcome
- **Cancelled**: Market cancelled (refunds issued)

### Betting Process

1. Users place bets on outcomes using the native token
2. AMM calculates share price based on current market state
3. Transaction is submitted to blockchain for verification
4. Shares are allocated to user's position
5. Market prices update automatically

## Blockchain Integration

### Local Blockchain Setup

For development, you can use:

**Ganache CLI:**
```bash
npm install -g ganache-cli
ganache-cli --port 8545 --networkId 1337
```

**Hardhat:**
```bash
npm install -g hardhat
npx hardhat node
```

### Transaction Types

- **CREATE_MARKET**: Create new prediction market
- **PLACE_BET**: Place bet on market outcome
- **RESOLVE_MARKET**: Resolve market with winning outcome
- **WITHDRAW**: Withdraw winnings

## ObjectWire.org Integration

This prediction market is designed to integrate with ObjectWire.org:

1. **Topic Integration**: Markets can be created for ObjectWire topics
2. **Outcome Resolution**: Integration with ObjectWire's verification system
3. **User Authentication**: Compatible with ObjectWire user accounts
4. **API Webhooks**: Real-time updates to ObjectWire platform

## Development

### Running Tests
```bash
cargo test
```

### Database Migrations
```bash
# Install sqlx-cli
cargo install sqlx-cli

# Run migrations manually
sqlx migrate run
```

### Adding New Features

1. **New Market Types**: Extend `MarketOutcome` enum in `market.rs`
2. **Custom AMM**: Modify pricing algorithms in `calculate_shares_for_bet`
3. **Additional APIs**: Add routes in `routes.rs`
4. **Blockchain Features**: Extend `blockchain/mod.rs`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLite database path | `sqlite:blackbook.db` |
| `BLOCKCHAIN_URL` | Blockchain RPC endpoint | `http://localhost:8545` |
| `BLOCKCHAIN_NETWORK_ID` | Network/Chain ID | `1337` |
| `SERVER_PORT` | Server port | `3000` |
| `MAX_BET_AMOUNT` | Maximum bet amount | `1000000` |
| `MIN_BET_AMOUNT` | Minimum bet amount | `1` |
| `AMM_LIQUIDITY_PARAMETER` | AMM liquidity parameter | `100` |

### Market Configuration

- **Default Duration**: 1 week
- **Minimum Duration**: 1 hour
- **Maximum Duration**: 1 year
- **Default Initial Liquidity**: 1000 tokens

## Security

- **Input Validation**: All API inputs are validated
- **SQL Injection Protection**: Using SQLx with prepared statements
- **CORS Configuration**: Configurable CORS for web integration
- **Transaction Verification**: All blockchain transactions are verified

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure SQLite permissions are correct
   - Check `DATABASE_URL` in `.env`

2. **Blockchain Connection Errors**
   - Verify local blockchain is running
   - Check `BLOCKCHAIN_URL` configuration
   - Ensure network ID matches

3. **API Errors**
   - Check server logs for detailed error messages
   - Verify request format matches API documentation

### Logs

Enable debug logging:
```bash
RUST_LOG=debug cargo run
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create GitHub issues for bugs
- Check ObjectWire.org documentation for integration questions
- Review API documentation in code comments

http://localhost:8082/marketplace.html