# ObjectWire CLI - Command Reference

## Philosophy: One-Stop Shop for Prediction Markets

The ObjectWire CLI is your **complete toolkit** for building prediction markets:
- 🔍 **Research**: Scrape, analyze, and validate events from any source
- ✍️ **Write**: Generate articles, threads, and market descriptions with AI
- 📊 **Markets**: Create, deploy, and manage prediction markets on L2
- 📈 **Monitor**: Real-time dashboards, analytics, and system health

---

## Command Structure

```
objectwire
├── research         # Article research & event discovery
│   ├── scrape       # Scrape URLs with AI extraction
│   ├── rss          # Process RSS feeds
│   ├── batch        # Batch process multiple sources
│   ├── analyze      # Deep analysis of scraped content
│   └── validate     # Validate event data quality
│
├── write            # Content generation
│   ├── article      # Generate full articles
│   ├── thread       # Generate Twitter/X threads
│   ├── description  # Market description generator
│   └── preview      # Preview generated content
│
├── markets          # Prediction market management
│   ├── generate     # Generate market from event
│   ├── deploy       # Deploy to Layer 2 blockchain
│   ├── list         # List all markets
│   ├── resolve      # Resolve market outcomes
│   └── stats        # Market statistics
│
├── monitor          # System monitoring
│   ├── dashboard    # Live monitoring dashboard
│   ├── logs         # Real-time log viewer
│   ├── stats        # System statistics
│   └── health       # Health check
│
└── config           # Configuration management
    ├── show         # Show current config
    ├── set          # Set config values
    └── reset        # Reset to defaults
```

---

## 🔍 RESEARCH COMMANDS

### `objectwire research scrape <url>`
**Purpose**: Scrape single URL and extract event data

**Options**:
```bash
--ai-filter          # Filter irrelevant content with AI
--preview            # Show preview before saving
--format json|xml    # Output format
--save               # Save to database (default: true)
--category <name>    # Override category detection
```

**Examples**:
```bash
# Basic scrape with AI extraction
objectwire research scrape https://espn.com/world-cup-2026

# Scrape with preview (don't save yet)
objectwire research scrape https://techcrunch.com/ai-news --preview

# Scrape and force category
objectwire research scrape https://news.com/article --category sports

# Output as JSON for piping
objectwire research scrape https://news.com/article --format json > event.json
```

---

### `objectwire research rss <feed_url>`
**Purpose**: Process RSS feed and extract multiple events

**Options**:
```bash
--limit <n>          # Max articles to process (default: 10)
--ai-filter          # Only save high-quality events
--min-confidence <n> # Minimum AI confidence (0.0-1.0)
--batch              # Process all at once (faster)
--watch              # Continuously monitor feed
```

**Examples**:
```bash
# Process latest 20 articles from ESPN RSS
objectwire research rss https://espn.com/rss --limit 20

# Only save high-confidence events
objectwire research rss https://techcrunch.com/feed --ai-filter --min-confidence 0.8

# Watch feed continuously (check every 30 min)
objectwire research rss https://news.com/feed --watch
```

---

### `objectwire research batch <file>`
**Purpose**: Batch process multiple URLs from file

**Options**:
```bash
--parallel <n>       # Number of concurrent workers (default: 5)
--ai-filter          # Filter low-quality events
--report             # Generate processing report
--resume             # Resume failed jobs
```

**File Format** (urls.txt):
```
https://espn.com/article-1
https://techcrunch.com/article-2
https://coindesk.com/article-3
```

**Examples**:
```bash
# Process 100 URLs with 10 workers
objectwire research batch urls.txt --parallel 10

# Only save filtered events + generate report
objectwire research batch urls.txt --ai-filter --report

# Resume previous batch that failed
objectwire research batch urls.txt --resume
```

---

### `objectwire research analyze <event_id>`
**Purpose**: Deep analysis of event with AI

**Features**:
- Probability refinement
- Source verification
- Sentiment analysis
- Risk assessment
- Related events detection

**Examples**:
```bash
# Analyze event and show insights
objectwire research analyze mexico-vs-south-africa-123abc

# Re-analyze with fresh data
objectwire research analyze mexico-vs-south-africa-123abc --refresh
```

---

### `objectwire research validate <event_id>`
**Purpose**: Validate event data quality

**Checks**:
- Date validity (freeze < resolution)
- Probability sum = 1.0
- Category accuracy
- Source credibility
- Market viability

**Examples**:
```bash
# Validate single event
objectwire research validate mexico-vs-south-africa-123abc

# Validate all pending events
objectwire research validate --all --status pending
```

---

## ✍️ WRITE COMMANDS

### `objectwire write article <event_id>`
**Purpose**: Generate full article about prediction market

**Options**:
```bash
--template <name>    # Template: analysis|news|profile|tutorial
--length <n>         # Word count (default: 750)
--style <name>       # Style: formal|casual|hype|technical
--seo                # Optimize for SEO
--preview            # Preview before saving
--publish            # Auto-publish to blog
```

**Examples**:
```bash
# Generate market analysis article
objectwire write article mexico-vs-south-africa-123abc --template analysis

# SEO-optimized article with preview
objectwire write article btc-100k-456def --seo --preview

# Short casual article (500 words)
objectwire write article mrbeast-100m-789ghi --length 500 --style casual
```

**Output**: Saves to `./articles/run_[timestamp]_[event_id].md`

---

### `objectwire write thread <event_id>`
**Purpose**: Generate Twitter/X thread about market

**Options**:
```bash
--tweets <n>         # Number of tweets (default: 5)
--style <name>       # Style: hype|informative|question|debate
--hashtags           # Include relevant hashtags
--preview            # Preview before saving
```

**Examples**:
```bash
# Generate 7-tweet thread with hype
objectwire write thread world-cup-final-abc123 --tweets 7 --style hype

# Informative thread with hashtags
objectwire write thread ai-agi-2026-def456 --style informative --hashtags
```

**Output**: Saves to `./threads/run_[timestamp]_[event_id].txt`

---

### `objectwire write description <event_id>`
**Purpose**: Generate market description for blockchain

**Options**:
```bash
--length <n>         # Character limit (default: 500)
--include-rules      # Include resolution rules
--formal             # Use formal tone
```

**Examples**:
```bash
# Generate description with resolution rules
objectwire write description mexico-vs-south-africa-123abc --include-rules

# Short description (200 chars)
objectwire write description btc-100k-456def --length 200
```

---

## 📊 MARKETS COMMANDS

### `objectwire markets generate <event_id>`
**Purpose**: Generate blockchain-ready market from event

**Options**:
```bash
--ai-suggest         # AI suggests probability adjustments
--liquidity <n>      # Initial liquidity (default: 1000)
--fee <n>            # Trading fee % (default: 2)
--preview            # Show preview before saving
```

**Examples**:
```bash
# Generate market with AI suggestions
objectwire markets generate mexico-vs-south-africa-123abc --ai-suggest

# High-liquidity market with preview
objectwire markets generate btc-100k-456def --liquidity 10000 --preview
```

---

### `objectwire markets deploy <event_id>`
**Purpose**: Deploy market to Layer 2 blockchain

**Options**:
```bash
--network <name>     # Network: optimism|arbitrum|base (default: base)
--gas-estimate       # Show gas estimate first
--confirm            # Require manual confirmation
--wait               # Wait for transaction confirmation
```

**Flow**:
1. Validate event data
2. Estimate gas costs
3. Show deployment preview
4. Deploy to L2
5. Update database with tx_id
6. Generate article (optional)

**Examples**:
```bash
# Deploy with gas estimate and confirmation
objectwire markets deploy mexico-vs-south-africa-123abc --gas-estimate --confirm

# Deploy to Arbitrum and wait for confirmation
objectwire markets deploy btc-100k-456def --network arbitrum --wait
```

---

### `objectwire markets list`
**Purpose**: List all markets with filters

**Options**:
```bash
--status <name>      # Filter: pending|deployed|resolved|cancelled
--category <name>    # Filter by category
--sort <field>       # Sort: date|liquidity|volume|popularity
--limit <n>          # Max results (default: 50)
--export             # Export to JSON/CSV
```

**Examples**:
```bash
# List all deployed sports markets
objectwire markets list --status deployed --category sports

# Top 10 markets by volume
objectwire markets list --sort volume --limit 10

# Export all markets to CSV
objectwire markets list --export markets.csv
```

---

### `objectwire markets resolve <market_id>`
**Purpose**: Resolve market outcome

**Options**:
```bash
--auto               # Auto-resolve using AI + data sources
--outcome <result>   # Manual: yes|no|no_change
--proof <url>        # Proof URL for manual resolution
--notify             # Notify all participants
```

**Examples**:
```bash
# Auto-resolve (AI checks sources)
objectwire markets resolve mexico-vs-south-africa-123abc --auto

# Manual resolution with proof
objectwire markets resolve btc-100k-456def --outcome no --proof https://coinmarketcap.com
```

---

### `objectwire markets stats <market_id>`
**Purpose**: Show market statistics

**Shows**:
- Total volume
- Number of traders
- Probability changes over time
- Liquidity depth
- Fee revenue
- Resolution status

**Examples**:
```bash
# Show stats for single market
objectwire markets stats mexico-vs-south-africa-123abc

# Show aggregate stats for all markets
objectwire markets stats --all
```

---

## 📈 MONITOR COMMANDS

### `objectwire monitor dashboard`
**Purpose**: Live monitoring dashboard

**Features**:
- Real-time scraper status
- Active markets count
- Recent deployments
- System health metrics
- Error logs
- Performance stats

**Options**:
```bash
--refresh <n>        # Refresh interval in seconds (default: 5)
--compact            # Compact view
--focus <module>     # Focus: scrapers|markets|ai|blockchain
```

**Examples**:
```bash
# Launch dashboard with 10s refresh
objectwire monitor dashboard --refresh 10

# Focus on market activity
objectwire monitor dashboard --focus markets
```

**UI Preview**:
```
╔══════════════════════════════════════════════════════════════╗
║               ObjectWire Live Dashboard                      ║
╠══════════════════════════════════════════════════════════════╣
║ System Status: ✅ Healthy        Uptime: 3d 14h 23m         ║
║                                                              ║
║ 🔍 Research Module                                           ║
║   • Active Scrapers: 3                                       ║
║   • RSS Feeds: 12 monitored                                  ║
║   • Events Processed (24h): 147                              ║
║   • AI Confidence Avg: 0.83                                  ║
║                                                              ║
║ 📊 Markets Module                                            ║
║   • Pending: 23                                              ║
║   • Deployed: 156                                            ║
║   • Resolved: 89                                             ║
║   • Total Volume (24h): $45,230                              ║
║                                                              ║
║ 🎯 Recent Activity                                           ║
║   12:34:56 - Deployed market: mexico-vs-south-africa-123abc  ║
║   12:32:10 - Generated article: btc-100k-456def              ║
║   12:30:45 - Scraped RSS: ESPN (14 articles)                 ║
║                                                              ║
║ Press 'q' to quit | 'r' to refresh | 'h' for help           ║
╚══════════════════════════════════════════════════════════════╝
```

---

### `objectwire monitor logs`
**Purpose**: Real-time log viewer

**Options**:
```bash
--tail               # Follow logs in real-time
--level <name>       # Filter: debug|info|warn|error
--module <name>      # Filter: scraper|ai|blockchain|api
--search <term>      # Search logs
--since <time>       # Show logs since time (1h, 30m, etc.)
```

**Examples**:
```bash
# Tail all logs
objectwire monitor logs --tail

# Show only errors from last hour
objectwire monitor logs --level error --since 1h

# Search logs for specific event
objectwire monitor logs --search "mexico-vs-south-africa"
```

---

### `objectwire monitor stats`
**Purpose**: System statistics and analytics

**Shows**:
- Total events processed
- Success rate by source
- Average processing time
- AI confidence distribution
- Market performance
- Revenue analytics

**Options**:
```bash
--timeframe <n>      # Timeframe: 24h|7d|30d|all (default: 7d)
--export             # Export to JSON/CSV
--chart              # Show ASCII charts
```

**Examples**:
```bash
# Show 30-day stats with charts
objectwire monitor stats --timeframe 30d --chart

# Export all-time stats
objectwire monitor stats --timeframe all --export stats.json
```

---

### `objectwire monitor health`
**Purpose**: System health check

**Checks**:
- Database connectivity
- Blockchain API status
- AI model availability
- Gemini API status
- Disk space
- Memory usage

**Examples**:
```bash
# Run health check
objectwire monitor health

# Continuous health monitoring
objectwire monitor health --watch
```

---

## ⚙️ CONFIG COMMANDS

### `objectwire config show`
**Purpose**: Show current configuration

**Examples**:
```bash
# Show all config
objectwire config show

# Show specific section
objectwire config show blockchain
```

---

### `objectwire config set <key> <value>`
**Purpose**: Set configuration value

**Examples**:
```bash
# Set blockchain network
objectwire config set blockchain.network base

# Set AI confidence threshold
objectwire config set ai.min_confidence 0.75

# Set Gemini article length
objectwire config set gemini.default_length 1000
```

---

### `objectwire config reset`
**Purpose**: Reset configuration to defaults

**Examples**:
```bash
# Reset all config
objectwire config reset

# Reset specific section
objectwire config reset blockchain
```

---

## 🚀 WORKFLOW EXAMPLES

### End-to-End: Article → Market → Article

```bash
# 1. Research: Scrape ESPN for World Cup news
objectwire research scrape https://espn.com/world-cup-2026 --preview

# 2. Generate market from event
objectwire markets generate mexico-vs-south-africa-123abc --ai-suggest

# 3. Deploy to Base L2
objectwire markets deploy mexico-vs-south-africa-123abc --gas-estimate --confirm

# 4. Write article about the market
objectwire write article mexico-vs-south-africa-123abc --template analysis --seo

# 5. Generate Twitter thread
objectwire write thread mexico-vs-south-africa-123abc --tweets 7 --style hype
```

---

### Batch Processing Pipeline

```bash
# 1. Add RSS feeds to watch
objectwire research rss https://espn.com/rss --watch &
objectwire research rss https://techcrunch.com/feed --watch &

# 2. Process batch of URLs
objectwire research batch urls.txt --parallel 10 --ai-filter

# 3. Generate markets for high-confidence events
objectwire markets generate --auto --min-confidence 0.8

# 4. Deploy all pending markets
objectwire markets deploy --all --pending --confirm

# 5. Monitor everything
objectwire monitor dashboard
```

---

### Auto-Resolution Flow

```bash
# 1. List markets ready for resolution
objectwire markets list --status deployed --ready-to-resolve

# 2. Auto-resolve using AI + data sources
objectwire markets resolve --auto --all

# 3. Generate outcome articles
objectwire write article --resolved --last-24h
```

---

## 📝 NOTES

### Philosophy
- **Research-First**: Always validate data before creating markets
- **AI-Augmented**: Use AI for filtering, analysis, and generation
- **Blockchain-Ready**: Every event is deployment-ready
- **Content-Rich**: Generate articles/threads for every market

### Performance Targets
- Scraping: <5s per URL
- AI Extraction: <10s per article
- Market Generation: <2s per event
- Deployment: <30s to L2
- Article Writing: <15s with Gemini 2.0 Flash

### Best Practices
1. Always use `--preview` when testing
2. Use `--ai-filter` for RSS feeds (high noise)
3. Set `--min-confidence 0.75` for quality control
4. Run `monitor health` daily
5. Export stats weekly for analysis

---

## 🎯 FUTURE COMMANDS (Roadmap)

```bash
# Social integrations
objectwire social post <event_id>              # Auto-post to Twitter/X
objectwire social schedule <event_id>          # Schedule social posts

# Advanced analytics
objectwire analyze sentiment <event_id>        # Sentiment analysis
objectwire analyze trends                      # Trend detection

# Automation
objectwire pipeline start                      # Start full automation
objectwire pipeline schedule                   # Schedule tasks

# Creator tracking
objectwire creators add MrBeast youtube       # Add creator to track
objectwire creators alerts                     # Creator activity alerts
```

---

**Last Updated**: December 26, 2025  
**Version**: 2.0.0  
**Status**: In Development
