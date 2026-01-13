# Betano Scraper

Professional-grade scraper for Betano football betting data. Dynamically discovers all FOOT leagues and scrapes fixtures with all available markets, top scorer bets, and league winner bets.

## Features

- **Dynamic League Discovery**: Automatically discovers 248+ football leagues from Betano
- **All Markets**: Extracts 150-200+ odds per fixture (all available markets, not just core)
- **Top Scorer Bets**: Extracts top scorer betting odds for major leagues
- **League Winner Bets**: Extracts league winner odds when available
- **League-Grouped Output**: Clean JSON output grouped by league

## Usage

```bash
# Scrape all leagues (dynamically discovered)
python src/sportsbooks/betano.py --output results.json

# Scrape specific leagues by ID
python src/sportsbooks/betano.py --league-ids 5 17083 16901

# Limit number of leagues
python src/sportsbooks/betano.py --max-leagues 10

# Faster scraping (0.3s delay)
python src/sportsbooks/betano.py --delay 0.3 --pretty

# Pretty print JSON output
python src/sportsbooks/betano.py --pretty
```

## CLI Arguments

| Argument | Description |
|----------|-------------|
| `--delay SECONDS` | Delay between requests (default: 1.0) |
| `--max-leagues N` | Maximum leagues to scrape (default: all) |
| `--league-ids ID [ID ...]` | Specific league IDs to scrape |
| `--output PATH` | Output file path (default: stdout) |
| `--pretty` | Pretty print JSON output |

## Output Format

League-grouped JSON array:

```json
[
  {
    "league_id": 5,
    "league_name": "LaLiga",
    "fixtures": [
      {
        "fixture_id": "75013519",
        "home_team_id": "1970454",
        "home_team_name": "Sevilha FC",
        "away_team_id": "107809",
        "away_team_name": "Celta de Vigo",
        "start_time": "2026-01-12T17:00:00Z",
        "status": "scheduled",
        "odds": [
          {
            "fixture_id": "75013519",
            "market_id": "2431805637",
            "market_name": "Resultado Final",
            "market_type": "MRES",
            "handicap": null,
            "outcome_id": "8275707160",
            "outcome_name": "1",
            "outcome_full_name": "Sevilha FC",
            "odds_value": 2.75,
            "bookmaker": "betano"
          }
        ]
      }
    ],
    "topScorer": [
      {
        "player_id": "18913721",
        "player_name": "Kylian Mbappe",
        "team_name": "Real Madrid",
        "league_id": 5,
        "market_type": "top_scorer",
        "market_name": "Melhor Marcador",
        "selection_id": "7835249119",
        "odds_value": 1.1,
        "bookmaker": "betano"
      }
    ],
    "leagueWinner": [...]
  },
  {
    "league_id": 123,
    "league_name": "Empty League"
  }
]
```

**Notes:**

- Leagues with no fixtures only include `league_id` and `league_name`
- `topScorer` only included when available (major leagues)
- `leagueWinner` only included when available

## Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `/sport/futebol/ligas/` (HTML) | Dynamic league discovery |
| `/api/league/hot/upcoming?leagueId={id}` | Upcoming fixtures per league |
| `/api/event/markets/{fixture_id}?tab=all` | All markets for a fixture |
| `/api/league/topPlayers?leagueId={id}` | Top scorer bets |
| `/api/league/phaseStandings?leagueId={id}` | League winner bets |

## Technical Details

- Uses `cloudscraper` to bypass Cloudflare protection
- Dynamic league discovery from HTML (no static files)
- Professional logging with timestamps
- Retry logic with exponential backoff on rate limits
