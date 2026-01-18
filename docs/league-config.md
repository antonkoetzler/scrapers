# League Configuration

## Overview

All soccer scrapers use a centralized league configuration defined in `src/shared/league_config.py`. This ensures consistency across all scrapers and makes it easy to add or remove leagues.

## League Categories

Leagues are organized into three categories:

### Primary Leagues
Major European and international competitions:
- Top 5 European Leagues (Premier League, La Liga, Serie A, Bundesliga, Ligue 1)
- Major International Competitions (Champions League, Europa League, Copa del Rey, FA Cup, etc.)

### Secondary Leagues
Strong domestic leagues:
- Championship, Serie B, La Liga 2, 2. Bundesliga, Ligue 2
- Eredivisie, Primeira Liga, Belgian Pro League, Turkish Süper Lig
- Austrian, Swiss, Danish, Swedish, Norwegian, Russian, Greek leagues

### Regional Leagues
Smaller leagues with potential for consistent betting patterns:
- Brazilian leagues (Série A, Série B, state championships)
- South American leagues (Argentina, Chile, Colombia, Mexico)
- Asian leagues (J1 League, K League 1, Chinese Super League)
- North American (MLS)

## Important Notes

- **NO ESPORTS SOCCER**: Only real football/soccer leagues are included
- Leagues are prioritized for betting predictor training
- Smaller leagues may have more consistent patterns and dominant teams

## Usage in Scrapers

Each scraper imports the appropriate league mapping:

```python
# Flashscore
from shared.league_config import get_flashscore_leagues
LEAGUE_MAPPING = get_flashscore_leagues()

# Livescore
from shared.league_config import get_livescore_leagues
LEAGUE_MAPPING = get_livescore_leagues()

# Betano (uses dynamic discovery, but fallback IDs are in config)
from shared.league_config import get_betano_league_ids
```

## Adding New Leagues

To add a new league:

1. Add it to the appropriate category in `league_config.py`
2. Include mappings for all scrapers that support it:
   - `betano_id`: League ID in Betano (if known)
   - `flashscore`: `{'country': '...', 'slug': '...'}`
   - `livescore`: `{'country': '...', 'slug': '...'}`

3. Test the league in each scraper to ensure URLs are correct

## Current League Count

- **Primary**: 12 leagues
- **Secondary**: 15 leagues
- **Regional**: 16 leagues
- **Total**: 43 leagues
