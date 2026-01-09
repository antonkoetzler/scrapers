# Betano Scraper

Scrapes fixtures and odds from Betano API.

## Usage

```bash
python sportsbooks/betano.py [--no-proxy]
```

## Output

Results are saved to `sportsbooks/result.json` in the required format:
- `fixtures` - Array of fixture objects
- `odds` - Array of odds objects

## Endpoints

- `/hot/trending/leagues` - Lists available leagues
- `/hot/trending/leagues/{league_id}/events` - Events for specific league

## Supported Markets

- 1x2 (Home/Draw/Away)
- Over/Under 2.5 goals
- Both Teams To Score (Yes/No)

## Status

✅ Fixtures collection  
✅ Odds collection  
❌ Scores collection (endpoint not found)  
❌ Database integration

