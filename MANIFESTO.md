# ObjectWire Manifesto
## The Future of Social Prediction Markets

---

## 🎯 Our Mission

**ObjectWire exists to democratize prediction markets by making social media metrics bettable, verifiable, and fair.**

We believe the creator economy is the new stock market. Views are the new revenue. Subscribers are the new market cap. And just like traditional markets, people should be able to put their conviction where their mouth is.

---

## 🧠 Core Philosophy

### 1. **Public Data Only**

> "If you can't verify it, you can't bet on it."

This is the most critical distinction in social prediction markets: **Public vs. Private Data.**

#### ❌ Betting on "Earnings" ($$$) → NO (Generally)

You **cannot** reliably bet on how much money a video makes.

**Why?** YouTube revenue (RPM/CPM) is private data visible only to the creator in their YouTube Studio dashboard. No external oracle can access this screen.

**The Problem:** Public calculators (like SocialBlade) are just estimates. They often show a range like:
> "Estimated Earnings: $10K - $150K"

That margin of error is **too wide to settle a bet**.

**The Exception:** You could bet on public financial disclosures if:
- The creator is a public company (like FaZe Clan stock price)
- They release audited tax returns (highly unlikely)
- Official press releases with revenue figures

#### ✅ Betting on "Views" → YES (The Gold Standard)

This is the **ideal asset class** for social betting.

**Why?**
- View counts are **public** (visible to everyone)
- **Verifiable via API** (YouTube Data API v3)
- **Hard to fake at scale** (YouTube actively audits view counts)
- **Real-time updates** (changes reflected within minutes)

We draw a hard line between **public** and **private** data:

| ✅ BETTABLE (Public) | ❌ NOT BETTABLE (Private) |
|---------------------|--------------------------|
|---------------------|--------------------------|
| View counts | Revenue/Earnings |
| Subscriber counts | CPM/RPM rates |
| Follower counts | Ad revenue splits |
| Spotify streams | Sponsorship deals |
| Chart positions | Private analytics |
| Concurrent viewers | Backend metrics |

**Why?** Because prediction markets require verifiable resolution. YouTube revenue is visible only to creators in their dashboard. No oracle can access it. SocialBlade estimates are just that—estimates with 10x margins of error.

### 2. **Velocity Over Totals**

The most exciting markets aren't "Will this video get 100M views?" but rather:

> "Will this video hit 100M views **in 24 hours**?"

#### The "Velocity" Bet Explained

**Example:** "Will the GTA VI Trailer #2 hit 100M views in 24 hours?"

**Why it works:**
- ⚡ **Instant gratification** - Resolves in hours, not months
- 📈 **Higher engagement** - Real-time tracking creates tension
- 🎯 **Clearer resolution** - Timestamp + view count = undeniable outcome
- 🔥 **FOMO factor** - Bettors watch the counter live

Velocity markets create:
- ⚡ **Instant gratification** - Resolves in hours, not months
- 📈 **Higher engagement** - Real-time tracking creates tension
- 🎯 **Clearer resolution** - Timestamp + view count = undeniable outcome

### 3. **API-First Resolution**

Every market should specify its **oracle** upfront:

```json
{
  "oracle": "youtube_api",
  "metric": "views",
  "target": 50000000,
  "timeframe_hours": 24
}
```

No arguments. No disputes. The API is the source of truth.

### 4. **Creator Economy is the New Wall Street**

| Traditional Finance | Creator Economy |
|--------------------|-----------------|
| Stock price | Subscriber count |
| Quarterly earnings | Monthly views |
| IPO | Platform exclusive deal |
| Merger | Collab video |
| Bankruptcy | Getting cancelled |
| Analyst ratings | SocialBlade grades |

---

## 🎬 Market Categories

### 📊 Metric Markets (Low Variance)
These are "Over/Under" bets based on verifiable data.

**MrBeast Markets:**
- "Will his next main channel video outperform his last one in 24 hours?"
- Metric: View count at T+24h mark
- Resolution: YouTube API comparison

**The Sidemen Markets:**
- "Will the next 'Tinder in Real Life' video feature a guest with >10M subs?"
- Metric: Guest verification + Sub count check
- "Over/Under 15M views on next Sidemen Sunday?"

**IShowSpeed vs Kai Cenat:**
- "Will IShowSpeed hit 30M subscribers before Kai Cenat hits 15M?"
- "Who gets more concurrent viewers on their next stream?"

### 🎬 Event Markets (High Variance)
These rely on specific occurrences within videos or announcements.

**Logan Paul / Impaulsive:**
- "Will Donald Trump appear on Impaulsive before the inauguration?"
- "Will Logan Paul fight in 2025?"

**Sidemen Sunday:**
- "Who will win the next 'Hide and Seek': KSI or Miniminter?"
- "Will the next video feature a celebrity guest?"

**Boxing/Fight Markets:**
- "Will KSI announce a fight with Jake Paul in 2025?"
- "Will the next Misfits Boxing event sell out?"

### ⚔️ Platform Wars
Streamers are constantly switching platforms or getting banned. This is high drama.

- "Will [Streamer X] sign an exclusive deal with Kick.com in Q1 2025?"
- "Will Asmongold get banned on Twitch for >7 days this year?"
- "Will YouTube Gaming surpass Twitch in total watch hours?"
- "Will Ninja return to Twitch streaming?"

### 🛍️ Creator Products
Creators are now launching physical products (Prime, Feastables, Lunchly).

- "Will Prime Hydration announce a new flavor in January?"
- "Will MrBeast's 'Feastables' be sold out at Walmart (online check) on Super Bowl Sunday?"
- "Will Lunchly receive an FDA warning in 2025?"
- "Will Prime outsell Gatorade at 7-Eleven this month?"

### 🎵 Music & Streaming
For YouTuber musicians (KSI, Corpse Husband), Spotify streams are the new "View Count."

- "Will KSI's new single enter the Spotify Global Top 50?"
- "Will The Weeknd's new album get >100M streams on Day 1?"
- "Will a YouTuber win a Grammy in 2025?"
- "Over/Under 50M Spotify streams for [Artist]'s next release?"

---

## 🔮 The Oracle Problem

### How We Resolve Markets

**Tier 1: Automatic (API-Based)**
```
YouTube Data API → Views, Subscribers, Likes
Twitch API → Followers, Concurrent Viewers
Spotify API → Streams, Chart Position
Twitter API → Followers, Engagement
```

**Tier 2: Semi-Automatic (Scraping)**
```
SocialBlade → Historical data, projections
Billboard → Chart positions
App Store → Download rankings
```

**Tier 3: Manual (Community Consensus)**
```
Event occurrence verification
Subjective outcomes
Breaking news events
```

---

## ⚖️ Ethical Guidelines

### We DO NOT support markets on:
- ❌ Personal relationships or breakups
- ❌ Health conditions or death
- ❌ Children or minors
- ❌ Anything requiring private information
- ❌ Illegal activities
- ❌ Market manipulation schemes

### We DO support markets on:
- ✅ Public performance metrics
- ✅ Professional announcements
- ✅ Product launches
- ✅ Platform migrations
- ✅ Competitive outcomes (boxing, gaming)
- ✅ Chart/ranking positions

---

## 🚀 The Vision

**Phase 1: Scraper Intelligence** (Current)
- Smart detection of social media content
- AI-powered market generation
- Structured payloads for blockchain
- **Article drafting from scraped events**

**Phase 2: Real-Time Oracles**
- YouTube API integration for live resolution
- Twitch webhook listeners
- Spotify chart monitoring
- Automated market resolution

**Phase 3: Content & Creator Partnerships**
- Auto-generate articles on trending markets
- Verified creator accounts
- Insider markets (with disclosure)
- Revenue sharing with creators

**Phase 4: Prediction Market Protocol**
- Decentralized oracle network
- Cross-platform liquidity
- Mobile-first betting experience
- Full content publishing pipeline

---

## 💡 Key Insights

### Why Social > Traditional
1. **Daily content** = Daily markets (vs quarterly earnings)
2. **Public metrics** = Verifiable outcomes (vs insider info)
3. **Emotional investment** = Higher engagement (fans bet on favorites)
4. **Global audience** = Massive liquidity potential

### The "Views Economy" Thesis
Views are the universal currency of attention. Unlike revenue (which is private and platform-dependent), views are:
- Publicly displayed
- Updated in real-time
- Comparable across creators
- Impossible to fake at scale

This makes them the **perfect asset class** for prediction markets.

---

## 📜 Closing Statement

> "In the attention economy, the only honest metric is the one everyone can see."

ObjectWire is building the infrastructure to turn public attention metrics into tradeable, verifiable prediction markets. We're not gambling on creators—we're creating price discovery for the attention economy.

**The future of finance is social. The future of social is verifiable. The future is ObjectWire.**

---

*Last updated: December 2024*
*Version: 1.0.0*
