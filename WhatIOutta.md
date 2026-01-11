# Scraper Requirements & Progress

This document outlines the essential data to scrape for the betting prediction system and tracks implementation progress.

## Terminology

- **Fixture**: A scheduled match/game between two teams
- **Odds**: The betting price for an outcome (e.g., 2.10 means bet $1 to win $2.10)
- **Market**: A type of bet (e.g., 1x2, over/under, btts)
- **Outcome**: A specific result you can bet on (e.g., "Home win", "Over 2.5 goals")
- **Bookmaker**: A betting company (e.g., Bet365, Pinnacle)
- **BTTS**: Both Teams To Score (betting on whether both teams score)
- **Over/Under**: Betting on total goals above/below a threshold (usually 2.5)
- **Decimal odds**: Odds format where 2.10 = bet $1 to win $2.10 total

---

## Data Requirements

### 1. Fixtures (Matches)

**Required Fields:**

<details>
<summary>Fixture data structure</summary>

```python
{
    'fixture_id': str,           # Unique identifier (e.g., "12345")
    'home_team_id': str,         # Team identifier (e.g., "team_123")
    'home_team_name': str,       # Team name (e.g., "Arsenal")
    'away_team_id': str,         # Team identifier (e.g., "team_456")
    'away_team_name': str,       # Team name (e.g., "Chelsea")
    'start_time': str,           # ISO datetime (e.g., "2024-01-15T15:00:00Z")
    'status': str                # 'scheduled', 'live', 'finished', 'cancelled', 'postponed'
}
```

</details>

**Why needed:**

- Base data structure for all matches
- Team IDs used for form, head-to-head, and home/away performance calculations
- Start time used for date filtering
- Status used to identify completed matches (for training)

---

### 2. Scores (Match Results)

**Required Fields:**

<details>
<summary>Score data structure</summary>

```python
{
    'fixture_id': str,           # Must match fixture_id from fixtures
    'home_score': int,           # Home team goals (e.g., 2)
    'away_score': int,           # Away team goals (e.g., 1)
    'status': str                # Usually 'finished' for completed matches
}
```

</details>

**Why needed:**

- Creates training labels (home_win/draw/away_win, over/under, btts)
- Used for team form, head-to-head stats, and home/away performance
- Only needed for completed matches (status = 'finished')

**Note:** FBref scraper outputs scores without `fixture_id`. See [Matching Strategy](#matching-strategy) section below.

---

### 3. Odds (Betting Odds)

**Required Fields:**

<details>
<summary>Odds data structure</summary>

```python
{
    'fixture_id': str,           # Must match fixture_id from fixtures
    'bookmaker_id': str,         # Bookmaker identifier (e.g., "betano")
    'bookmaker_name': str,       # Bookmaker name (e.g., "Betano")
    'market_id': str,            # Market type: '1x2', 'over_under', 'btts'
    'market_name': str,          # Market display name (e.g., "1X2", "Over/Under")
    'outcome_id': str,           # Outcome identifier (e.g., "1", "over_2.5", "yes")
    'outcome_name': str,         # Outcome name (e.g., "Home", "Over 2.5", "Yes")
    'odds_value': float          # Decimal odds (e.g., 2.10)
}
```

</details>

**Market Types:**

<details>
<summary>1x2 Market</summary>

```python
{
    'market_id': '1x2',
    'market_name': '1X2',
    'outcome_id': '1',           # or 'X' or '2'
    'outcome_name': 'Home',      # or 'Draw' or 'Away'
    'odds_value': 2.10
}
```

</details>

<details>
<summary>Over/Under Market</summary>

```python
{
    'market_id': 'over_under',
    'market_name': 'Over/Under',
    'outcome_id': 'over_2.5',   # or 'under_2.5'
    'outcome_name': 'Over 2.5', # or 'Under 2.5'
    'odds_value': 1.85
}
```

</details>

<details>
<summary>BTTS Market</summary>

```python
{
    'market_id': 'btts',
    'market_name': 'Both Teams To Score',
    'outcome_id': 'yes',         # or 'no'
    'outcome_name': 'Yes',       # or 'No'
    'odds_value': 1.70
}
```

</details>

**Why needed:**

- Used as features in the model (average odds, odds spread)
- Used to calculate expected value for value betting
- Multiple bookmakers allow finding the best odds

---

## Data Relationships

```text
Fixture (1) ──→ (N) Scores      (One fixture has one score when finished)
Fixture (1) ──→ (N) Odds        (One fixture has many odds from different bookmakers/markets)
```

**Key Points:**

- `fixture_id` is the primary key linking all data
- Team IDs must be consistent across fixtures (same team = same ID)
- Only scrape scores for matches with `status = 'finished'`
- Odds can be scraped for any fixture (scheduled, live, or finished)

---

## Matching Strategy

**Problem:** FBref scores don't have Betano's `fixture_id`. Need to link scores to fixtures.

**Solution:** Match FBref scores to Betano fixtures using:

- `home_team_name` + `away_team_name` + `start_time` (normalized team names, datetime within tolerance)

**Implementation:** Matching logic will be handled in arbihawk during data ingestion, not in scrapers.

**FBref Output Format:**

- **Required:** `home_team_name`, `away_team_name`, `home_score`, `away_score`, `start_time`, `status`
- **Optional Metadata:** `league`, `season`, `match_date` (useful for filtering/analysis, not used in core training)

**Note:** FBref now outputs `start_time` (standardized from `match_datetime`).

---

## Optional Metadata Fields

These fields are scraped but not required for core training/prediction:

- **`league`** - League name (e.g., "Premier League") - useful for filtering/analysis
- **`season`** - Season identifier (e.g., "2024-2025") - useful for filtering/analysis
- **`match_date`** - Date only (YYYY-MM-DD) - useful for matching/debugging

These can be kept in scraper output but won't be stored in arbihawk's core database schema.

---

## Implementation Progress

### ✅ Betano Scraper (`sportsbooks/betano.py`)

**Fixtures Collection:**

- [x] Fetches from `/hot/trending/leagues/{league_id}/events` endpoint
- [x] Extracts all required fields: `fixture_id`, `home_team_id`, `home_team_name`, `away_team_id`, `away_team_name`, `start_time`
- [x] Converts timestamps to ISO format
- [x] Status defaults to `'scheduled'` (endpoint doesn't provide status)

**Odds Collection:**

- [x] Extracts odds from event markets
- [x] Supports all 3 required markets:
  - [x] **1x2** (MRES market type) - Home/Draw/Away outcomes
  - [x] **Over/Under 2.5** (HCTG market type with handicap 2.5) - Over/Under outcomes
  - [x] **BTTS** (BTSC market type) - Yes/No outcomes
- [x] Maps Betano market types to standard format
- [x] Handles Portuguese outcome names (e.g., "Sim"/"Não" → "Yes"/"No")
- [x] Extracts all required fields

**Infrastructure:**

- [x] Anti-scraping measures (cloudscraper, headers, retry logic)
- [x] Data transformation to required format
- [x] Outputs JSON to `result.json`

---

### ✅ FBref Scraper (`sports_data/fbref.py`)

**Scores Collection:**

- [x] Scrapes match results from FBref HTML tables
- [x] Extracts: `home_team_name`, `away_team_name`, `home_score`, `away_score`, `start_time`, `status`
- [x] Optional metadata: `league`, `season`, `match_date`
- [x] Supports multiple leagues and seasons
- [x] Only collects completed matches (with scores)

**Note:** Missing `fixture_id` - will be matched in arbihawk using team names + datetime.

---

### ❌ Remaining Tasks

**Status Detection:**

- [ ] Determine actual match status (scheduled/live/finished/cancelled/postponed)
- [ ] Currently defaults to `'scheduled'` for all Betano fixtures
- [ ] May require different endpoint or additional data source

**Date Range Support:**

- [ ] Add `from_date` and `to_date` parameters to filter fixtures
- [ ] Currently only fetches trending leagues (may not cover all dates)

**Multiple League Support:**

- [ ] Currently hardcoded to league ID 1 (Premier League) in Betano scraper
- [ ] Should support fetching from all available leagues or allow `league_id` as parameter

**Data Standardization:**

- [x] Standardize FBref `match_datetime` → `start_time` for consistency
- [ ] Ensure team name normalization for matching

**Error Handling:**

- [ ] Better handling of missing data fields
- [ ] Validation of transformed data format
- [ ] Logging improvements

---

## Endpoint Discovery Status

**Found Endpoints:**

- ✅ `/hot/trending/leagues` - Lists available leagues
- ✅ `/hot/trending/leagues/{league_id}/events` - Events for specific league

**Missing Endpoints:**

- ❌ Scores/results endpoint (not found in discovery)
- ❌ Status endpoint (not found in discovery)
- ❌ Date-filtered fixtures endpoint (not found in discovery)

---

## Summary Checklist

**Essential Data:**

- [x] **Fixtures**: fixture_id, home_team_id, home_team_name, away_team_id, away_team_name, start_time, status
- [x] **Scores**: home_team_name, away_team_name, home_score, away_score, start_time, status (via FBref, matching needed)
- [x] **Odds**: fixture_id, bookmaker_id, bookmaker_name, market_id, market_name, outcome_id, outcome_name, odds_value

**Markets to Support:**

- [x] 1x2 (Home/Draw/Away)
- [x] Over/Under 2.5 goals
- [x] Both Teams To Score (Yes/No)

**Integration:**

- [ ] Implement matching logic in arbihawk for FBref scores → Betano fixtures
- [x] Standardize datetime field naming (`match_datetime` → `start_time`)
- [ ] Ensure team IDs are consistent across fixtures
