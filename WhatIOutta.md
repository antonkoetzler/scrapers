# Custom Scraper Requirements

This document outlines the essential data you need to scrape for the betting prediction system. Only include data that is actually used for training and prediction.

## Terminology

- **Fixture**: A scheduled match/game between two teams
- **Odds**: The betting price for an outcome (e.g., 2.10 means bet $1 to win $2.10)
- **Market**: A type of bet (e.g., 1x2, over/under, btts)
- **Outcome**: A specific result you can bet on (e.g., "Home win", "Over 2.5 goals")
- **Bookmaker**: A betting company (e.g., Bet365, Pinnacle)
- **BTTS**: Both Teams To Score (betting on whether both teams score)
- **Over/Under**: Betting on total goals above/below a threshold (usually 2.5)
- **Decimal odds**: Odds format where 2.10 = bet $1 to win $2.10 total

## Essential Data to Scrape

### 1. Fixtures (Matches)

**What you need:**

- Unique match identifier
- Home team identifier and name
- Away team identifier and name
- Match start date/time
- Match status (to identify completed matches)

**Required Fields:**

<details>
<summary>Fixture data structure</summary>

```python
{
    'fixture_id': str,           # Unique identifier (e.g., "12345")
    'home_team_id': str,          # Team identifier (e.g., "team_123")
    'home_team_name': str,        # Team name (e.g., "Arsenal")
    'away_team_id': str,          # Team identifier (e.g., "team_456")
    'away_team_name': str,        # Team name (e.g., "Chelsea")
    'start_time': str,            # ISO datetime (e.g., "2024-01-15T15:00:00Z")
    'status': str                 # 'scheduled', 'live', 'finished', 'cancelled', 'postponed'
}
```

</details>

**Why needed:**

- Fixtures are the base data structure
- Team IDs are used to calculate form, head-to-head, and home/away performance
- Start time is used to filter matches by date
- Status is used to identify completed matches (for training)

**Example snippet:**

<details>
<summary>get_fixtures() example</summary>

```python
def get_fixtures(self, from_date: str, to_date: str) -> List[Dict]:
    """Get fixtures in date range."""
    # Your scraping logic here
    return [
        {
            'fixture_id': 'match_123',
            'home_team_id': 'arsenal',
            'home_team_name': 'Arsenal',
            'away_team_id': 'chelsea',
            'away_team_name': 'Chelsea',
            'start_time': '2024-01-15T15:00:00Z',
            'status': 'finished'
        }
    ]
```

</details>

---

### 2. Scores (Match Results)

**What you need:**

- Match identifier (to link to fixture)
- Home team score
- Away team score
- Match status

**Required Fields:**

<details>
<summary>Score data structure</summary>

```python
{
    'fixture_id': str,            # Must match fixture_id from fixtures
    'home_score': int,            # Home team goals (e.g., 2)
    'away_score': int,           # Away team goals (e.g., 1)
    'status': str                # Usually 'finished' for completed matches
}
```

</details>

**Why needed:**

- Scores are used to create training labels (home_win/draw/away_win, over/under, btts)
- Scores are used to calculate team form, head-to-head stats, and home/away performance
- Only needed for completed matches (status = 'finished')

**Example snippet:**

<details>
<summary>get_scores() example</summary>

```python
def get_scores(self, fixture_id: str) -> Dict:
    """Get final score for a completed match."""
    # Your scraping logic here
    return {
        'fixture_id': 'match_123',
        'home_score': 2,
        'away_score': 1,
        'status': 'finished'
    }
```

</details>

---

### 3. Odds (Betting Odds)

**What you need:**

- Match identifier (to link to fixture)
- Bookmaker identifier and name
- Market type (1x2, over_under, btts)
- Outcome identifier and name
- Odds value (decimal format)

**Required Fields:**

<details>
<summary>Odds data structure</summary>

```python
{
    'fixture_id': str,            # Must match fixture_id from fixtures
    'bookmaker_id': str,          # Bookmaker identifier (e.g., "bet365")
    'bookmaker_name': str,        # Bookmaker name (e.g., "Bet365")
    'market_id': str,             # Market type: '1x2', 'over_under', 'btts'
    'market_name': str,           # Market display name (e.g., "1X2", "Over/Under")
    'outcome_id': str,            # Outcome identifier (e.g., "1", "over_2.5", "yes")
    'outcome_name': str,          # Outcome name (e.g., "Home", "Over 2.5", "Yes")
    'odds_value': float           # Decimal odds (e.g., 2.10)
}
```

</details>

**Market Types:**

**1x2 Market:**

<details>
<summary>1x2 market example</summary>

```python
{
    'market_id': '1x2',
    'market_name': '1X2',
    'outcome_id': '1',      # or 'X' or '2'
    'outcome_name': 'Home', # or 'Draw' or 'Away'
    'odds_value': 2.10
}
```

</details>

**Over/Under Market:**

<details>
<summary>Over/Under market example</summary>

```python
{
    'market_id': 'over_under',
    'market_name': 'Over/Under',
    'outcome_id': 'over_2.5',  # or 'under_2.5'
    'outcome_name': 'Over 2.5', # or 'Under 2.5'
    'odds_value': 1.85
}
```

</details>

**Both Teams To Score (BTTS) Market:**

<details>
<summary>BTTS market example</summary>

```python
{
    'market_id': 'btts',
    'market_name': 'Both Teams To Score',
    'outcome_id': 'yes',   # or 'no'
    'outcome_name': 'Yes', # or 'No'
    'odds_value': 1.70
}
```

</details>

**Why needed:**

- Odds are used as features in the model (average odds, odds spread)
- Odds are used to calculate expected value for value betting
- Multiple bookmakers allow finding the best odds

**Example snippet:**

<details>
<summary>get_odds() example</summary>

```python
def get_odds(self, fixture_id: str) -> List[Dict]:
    """Get odds for a fixture from multiple bookmakers."""
    # Your scraping logic here
    return [
        {
            'fixture_id': 'match_123',
            'bookmaker_id': 'bet365',
            'bookmaker_name': 'Bet365',
            'market_id': '1x2',
            'market_name': '1X2',
            'outcome_id': '1',
            'outcome_name': 'Home',
            'odds_value': 2.10
        },
        {
            'fixture_id': 'match_123',
            'bookmaker_id': 'bet365',
            'bookmaker_name': 'Bet365',
            'market_id': '1x2',
            'market_name': '1X2',
            'outcome_id': 'X',
            'outcome_name': 'Draw',
            'odds_value': 3.50
        },
        # ... more outcomes
    ]
```

</details>

---

## Data Relationships

```bash
Fixture (1) ──→ (N) Scores      (One fixture has one score when finished)
Fixture (1) ──→ (N) Odds         (One fixture has many odds from different bookmakers/markets)
```

**Key Points:**

- `fixture_id` is the primary key linking all data
- Team IDs must be consistent across fixtures (same team = same ID)
- Only scrape scores for matches with `status = 'finished'`
- Odds can be scraped for any fixture (scheduled, live, or finished)

---

## Data Format Examples

### Complete Example: One Match

**Fixture:**

<details>
<summary>Fixture example</summary>

```python
{
    'fixture_id': 'match_12345',
    'home_team_id': 'arsenal',
    'home_team_name': 'Arsenal',
    'away_team_id': 'chelsea',
    'away_team_name': 'Chelsea',
    'start_time': '2024-01-15T15:00:00Z',
    'status': 'finished'
}
```

</details>

**Score (if finished):**

<details>
<summary>Score example</summary>

```python
{
    'fixture_id': 'match_12345',
    'home_score': 2,
    'away_score': 1,
    'status': 'finished'
}
```

</details>

**Odds (multiple entries per fixture):**

<details>
<summary>Odds example</summary>

```python
[
    # 1x2 market from Bet365
    {
        'fixture_id': 'match_12345',
        'bookmaker_id': 'bet365',
        'bookmaker_name': 'Bet365',
        'market_id': '1x2',
        'market_name': '1X2',
        'outcome_id': '1',
        'outcome_name': 'Home',
        'odds_value': 2.10
    },
    {
        'fixture_id': 'match_12345',
        'bookmaker_id': 'bet365',
        'bookmaker_name': 'Bet365',
        'market_id': '1x2',
        'market_name': '1X2',
        'outcome_id': 'X',
        'outcome_name': 'Draw',
        'odds_value': 3.50
    },
    {
        'fixture_id': 'match_12345',
        'bookmaker_id': 'bet365',
        'bookmaker_name': 'Bet365',
        'market_id': '1x2',
        'market_name': '1X2',
        'outcome_id': '2',
        'outcome_name': 'Away',
        'odds_value': 3.20
    },
    # Over/Under market
    {
        'fixture_id': 'match_12345',
        'bookmaker_id': 'bet365',
        'bookmaker_name': 'Bet365',
        'market_id': 'over_under',
        'market_name': 'Over/Under',
        'outcome_id': 'over_2.5',
        'outcome_name': 'Over 2.5',
        'odds_value': 1.85
    },
    {
        'fixture_id': 'match_12345',
        'bookmaker_id': 'bet365',
        'bookmaker_name': 'Bet365',
        'market_id': 'over_under',
        'market_name': 'Over/Under',
        'outcome_id': 'under_2.5',
        'outcome_name': 'Under 2.5',
        'odds_value': 1.95
    },
    # BTTS market
    {
        'fixture_id': 'match_12345',
        'bookmaker_id': 'bet365',
        'bookmaker_name': 'Bet365',
        'market_id': 'btts',
        'market_name': 'Both Teams To Score',
        'outcome_id': 'yes',
        'outcome_name': 'Yes',
        'odds_value': 1.70
    },
    {
        'fixture_id': 'match_12345',
        'bookmaker_id': 'bet365',
        'bookmaker_name': 'Bet365',
        'market_id': 'btts',
        'market_name': 'Both Teams To Score',
        'outcome_id': 'no',
        'outcome_name': 'No',
        'odds_value': 2.10
    }
]
```

</details>

---

## 📊 Scraper Progress

### FBref Scraper (`sports_data/fbref.py`)

- [x] **Scores Collection** ✅
  - [x] Scrapes match results from FBref HTML tables
  - [x] Extracts: `home_team_name`, `away_team_name`, `home_score`, `away_score`, `match_date`, `status`, `league`, `season`
  - [x] Supports multiple leagues and seasons
  - [x] Outputs raw match data independently (decoupled from Betano)

### Betano Scraper (`sportsbooks/betano.py`)

### ✅ What's Currently Working

- [x] **Fixtures Collection** ✅
  - [x] Fetches fixtures from `/hot/trending/leagues/{league_id}/events` endpoint
  - [x] Extracts: `fixture_id`, `home_team_id`, `home_team_name`, `away_team_id`, `away_team_name`, `start_time`
  - [x] Converts timestamps to ISO format
  - [x] Handles multiple leagues (1, 5, 1635, 10483, 16880, 16901, 17082)
  - [x] Status defaults to `'scheduled'` (endpoint doesn't provide status)

- [x] **Odds Collection** ✅
  - [x] Extracts odds from event markets
  - [x] Supports all 3 required markets:
    - [x] **1x2** (MRES market type) - Home/Draw/Away outcomes
    - [x] **Over/Under 2.5** (HCTG market type with handicap 2.5) - Over/Under outcomes
    - [x] **BTTS** (BTSC market type) - Yes/No outcomes
  - [x] Maps Betano market types to standard format
  - [x] Handles Portuguese outcome names (e.g., "Sim"/"Não" → "Yes"/"No")
  - [x] Extracts: `fixture_id`, `bookmaker_id`, `bookmaker_name`, `market_id`, `market_name`, `outcome_id`, `outcome_name`, `odds_value`

- [x] **Anti-Scraping Measures** ✅
  - [x] Uses `cloudscraper` to bypass Cloudflare protection
  - [x] Proper browser headers and session management
  - [x] Retry logic with exponential backoff
  - [x] Error handling and logging

- [x] **Data Transformation** ✅
  - [x] Transforms raw API responses to required format
  - [x] Outputs JSON to `result.json` file
  - [x] Filters out unnecessary data (only keeps required fields)

### ❌ What Still Needs to Be Done

- [x] **Scores Collection** ✅
  - [x] FBref scraper (`sports_data/fbref.py`) provides match scores/results
  - [x] Extracts: `home_team_name`, `away_team_name`, `home_score`, `away_score`, `match_date`, `status`
  - [x] Only collects completed matches (with scores)
  - [x] Supports multiple leagues (Premier League, Serie A, La Liga, Bundesliga, etc.)

- [ ] **Status Detection** ⚠️
  - [ ] Currently defaults to `'scheduled'` for all fixtures
  - [ ] Need to determine actual match status (scheduled/live/finished/cancelled/postponed)
  - [ ] May require different endpoint or additional data source

- [ ] **Database Integration** ❌
  - [ ] Implement `collect_fixtures()` method with database storage
  - [ ] Implement `collect_odds()` method with database storage
  - [ ] Implement `collect_scores()` method with database storage
  - [ ] Use `self.db.insert_fixture()`, `self.db.insert_odds()`, `self.db.insert_score()`

- [ ] **Date Range Support** ❌
  - [ ] Add `from_date` and `to_date` parameters to filter fixtures
  - [ ] Currently only fetches trending leagues (may not cover all dates)

- [ ] **Multiple League Support** ⚠️
  - [ ] Currently hardcoded to league ID 1 (Premier League)
  - [ ] Should support fetching from all available leagues
  - [ ] Or allow league_id as parameter

- [ ] **Error Handling Improvements** ⚠️
  - [ ] Better handling of missing data fields
  - [ ] Validation of transformed data format
  - [ ] Logging improvements

### 🔍 Endpoint Discovery Status

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

- [ ] **Fixtures**: fixture_id, home_team_id, home_team_name, away_team_id, away_team_name, start_time, status
- [x] **Scores**: home_team_name, away_team_name, home_score, away_score, match_date, status (via FBref scraper)
- [ ] **Odds**: fixture_id, bookmaker_id, bookmaker_name, market_id, market_name, outcome_id, outcome_name, odds_value

**Markets to Support:**

- [ ] 1x2 (Home/Draw/Away)
- [ ] Over/Under 2.5 goals
- [ ] Both Teams To Score (Yes/No)

**Implementation:**

- [ ] Implement `collect_fixtures()` method
- [ ] Implement `collect_odds()` method
- [ ] Implement `collect_scores()` method
- [ ] Use database methods to store data
- [ ] Ensure team IDs are consistent across fixtures
