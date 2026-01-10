"""FBref scraper for match scores and results."""
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup

# Add parent directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.tui import TUI
from shared.scraper_utils import init_proxy_manager
from shared.request_with_fallback import request_with_fallback


# FBref league IDs and names
# Format: 'Display Name': {'id': FBref_comp_id, 'name': 'FBref URL Name'}
FBREF_LEAGUES = {
    # Major Leagues (Big 5)
    'Premier League': {'id': 9, 'name': 'Premier-League'},
    'La Liga': {'id': 12, 'name': 'La-Liga'},
    'Serie A': {'id': 11, 'name': 'Serie-A'},
    'Bundesliga': {'id': 20, 'name': 'Bundesliga'},
    'Ligue 1': {'id': 13, 'name': 'Ligue-1'},
    
    # Second Tier (Big 5)
    'Championship': {'id': 10, 'name': 'Championship'},
    'Serie B': {'id': 18, 'name': 'Serie-B'},
    'La Liga 2': {'id': 17, 'name': 'Segunda-Division'},
    '2. Bundesliga': {'id': 19, 'name': '2-Bundesliga'},
    'Ligue 2': {'id': 60, 'name': 'Ligue-2'},
    
    # Other Top European Leagues
    'Eredivisie': {'id': 23, 'name': 'Eredivisie'},
    'Primeira Liga': {'id': 32, 'name': 'Primeira-Liga'},
    'Austrian Bundesliga': {'id': 28, 'name': 'Bundesliga'},
    'Belgian Pro League': {'id': 37, 'name': 'Pro-League'},
    'Swiss Super League': {'id': 40, 'name': 'Super-League'},
    'Danish Superliga': {'id': 26, 'name': 'Superliga'},
    'Swedish Allsvenskan': {'id': 29, 'name': 'Allsvenskan'},
    'Norwegian Eliteserien': {'id': 30, 'name': 'Eliteserien'},
    'Russian Premier League': {'id': 30, 'name': 'Premier-League'},
    'Turkish Süper Lig': {'id': 26, 'name': 'Super-Lig'},
    'Greek Super League': {'id': 33, 'name': 'Super-League'},
    
    # Brazilian Leagues
    'Brasileiro Série A': {'id': 24, 'name': 'Serie-A'},
    'Brasileiro Série B': {'id': 25, 'name': 'Serie-B'},
    
    # Other South American
    'Argentine Primera División': {'id': 21, 'name': 'Primera-Division'},
    'Chilean Primera División': {'id': 22, 'name': 'Primera-Division'},
    'Colombian Categoría Primera A': {'id': 31, 'name': 'Categoria-Primera-A'},
    'Mexican Liga MX': {'id': 31, 'name': 'Liga-MX'},
    
    # Asian Leagues
    'J1 League': {'id': 25, 'name': 'J1-League'},
    'K League 1': {'id': 55, 'name': 'K-League-1'},
    'Chinese Super League': {'id': 60, 'name': 'Super-League'},
}


def get_current_season() -> str:
    """Get current season in FBref format (e.g., '2024-2025')."""
    now = datetime.now()
    year = now.year
    month = now.month
    
    # Season typically runs Aug-May, so if we're in Jan-Jul, use previous year
    if month < 8:
        return f"{year-1}-{year}"
    else:
        return f"{year}-{year+1}"


def parse_score(score_str: str) -> Optional[Tuple[int, int]]:
    """
    Parse score string to home and away scores.
    
    Examples: "1–0" -> (1, 0), "2-1" -> (2, 1), "0–0" -> (0, 0)
    """
    if not score_str or score_str.strip() == '':
        return None
    
    # Handle different dash types (en dash, em dash, hyphen)
    score_str = score_str.strip()
    score_str = re.sub(r'[–—−-]', '-', score_str)
    
    # Extract numbers
    parts = score_str.split('-')
    if len(parts) != 2:
        return None
    
    try:
        home_score = int(parts[0].strip())
        away_score = int(parts[1].strip())
        return (home_score, away_score)
    except ValueError:
        return None


def normalize_team_name(name: str) -> str:
    """Normalize team name for matching."""
    if not name:
        return ""
    
    # Common name variations mapping
    variations = {
        'nott\'ham forest': 'nottingham forest',
        'nott\'ham': 'nottingham',
        'manchester utd': 'manchester united',
        'man utd': 'manchester united',
        'manchester city': 'man city',
        'tottenham': 'tottenham hotspur',
        'spurs': 'tottenham hotspur',
    }
    
    name_lower = name.lower().strip()
    
    # Apply variations
    for key, value in variations.items():
        if key in name_lower:
            name_lower = name_lower.replace(key, value)
    
    # Remove common suffixes
    name_lower = re.sub(r'\s+(fc|cf|united|city|town|athletic|athletico|atletico|atlético)$', '', name_lower, flags=re.IGNORECASE)
    name_lower = re.sub(r'\s+hotspur$', '', name_lower, flags=re.IGNORECASE)
    
    return name_lower.strip()


def extract_matches_from_table(soup: BeautifulSoup, league_name: str, season: str) -> List[Dict]:
    """Extract match data from FBref schedule table."""
    matches = []
    
    # Find schedule table (ID pattern: sched_{season}_{league_id}_1)
    table = soup.find('table', {'id': re.compile(r'sched_\d{4}-\d{4}_\d+_\d+')})
    if not table:
        TUI.warning(f"No schedule table found for {league_name}")
        return matches
    
    rows = table.find_all('tr')
    if len(rows) < 2:
        return matches
    
    # Parse header to find column indices
    header_row = rows[0]
    headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
    
    # Find column indices
    try:
        date_idx = headers.index('Date')
        time_idx = headers.index('Time') if 'Time' in headers else None
        home_idx = headers.index('Home')
        score_idx = headers.index('Score')
        away_idx = headers.index('Away')
    except ValueError as e:
        TUI.error(f"Could not find required columns: {e}")
        TUI.info(f"Available columns: {headers}")
        return matches
    
    # Parse data rows
    for row in rows[1:]:
        cells = row.find_all(['td', 'th'])
        if len(cells) < max(home_idx, score_idx, away_idx, date_idx) + 1:
            continue
        
        # Extract data
        date_str = cells[date_idx].get_text(strip=True)
        time_str = cells[time_idx].get_text(strip=True) if time_idx and time_idx < len(cells) else ''
        home_team = cells[home_idx].get_text(strip=True)
        score_str = cells[score_idx].get_text(strip=True)
        away_team = cells[away_idx].get_text(strip=True)
        
        # Skip if no score (match not played yet)
        if not score_str or score_str == '':
            continue
        
        # Parse score
        score_result = parse_score(score_str)
        if not score_result:
            continue
        
        home_score, away_score = score_result
        
        # Parse date
        try:
            # FBref date format: "2024-08-16"
            if time_str:
                datetime_str = f"{date_str} {time_str}"
                match_date = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            else:
                match_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            match_data = {
                'home_team_name': home_team,
                'away_team_name': away_team,
                'home_score': home_score,
                'away_score': away_score,
                'match_date': match_date.strftime('%Y-%m-%d'),
                'match_datetime': match_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'status': 'finished',
                'league': league_name,
                'season': season
            }
            matches.append(match_data)
        except ValueError as e:
            TUI.warning(f"Could not parse date '{date_str} {time_str}': {e}")
            continue
    
    return matches


def scrape_league(league_name: str, league_id: int, season: str, url_name: str = None) -> List[Dict]:
    """Scrape matches for a specific league."""
    if url_name is None:
        url_name = league_name.replace(' ', '-')
    url = f"https://fbref.com/en/comps/{league_id}/{season}/schedule/{season}-{url_name}-Scores-and-Fixtures"
    
    TUI.info(f"Scraping {league_name} ({season})...")
    
    try:
        response = request_with_fallback('get', url, max_retries=3, use_proxy=True, timeout=15)
        if response.status_code != 200:
            TUI.error(f"Failed to fetch {league_name}: Status {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        matches = extract_matches_from_table(soup, league_name, season)
        
        TUI.success(f"Found {len(matches)} completed matches in {league_name}")
        return matches
        
    except Exception as e:
        TUI.error(f"Error scraping {league_name}: {e}")
        return []




def main():
    """Main function to scrape FBref scores."""
    import argparse
    
    parser = argparse.ArgumentParser(description='FBref Scores Scraper')
    parser.add_argument('--no-proxy', action='store_true', help='Disable proxy usage')
    parser.add_argument('--refresh-proxies', action='store_true', default=True, 
                       help='Auto-refresh proxies if < 5 working (default: True)')
    parser.add_argument('--no-refresh-proxies', dest='refresh_proxies', action='store_false',
                       help='Disable auto-refresh of proxies')
    parser.add_argument('--season', help='Season to scrape (e.g., 2024-2025). Default: current season')
    parser.add_argument('--leagues', nargs='+', help='Specific leagues to scrape. Default: all')
    
    args = parser.parse_args()
    
    # Initialize proxy manager
    init_proxy_manager(no_proxy=args.no_proxy, refresh_proxies=args.refresh_proxies)
    
    TUI.header("FBref Scores Scraper")
    
    # Get season
    season = args.season or get_current_season()
    TUI.info(f"Scraping season: {season}")
    
    # Get leagues to scrape
    leagues_to_scrape = args.leagues if args.leagues else list(FBREF_LEAGUES.keys())
    
    # Scrape all leagues
    all_matches = []
    for league_name in leagues_to_scrape:
        if league_name not in FBREF_LEAGUES:
            TUI.warning(f"Unknown league: {league_name}, skipping")
            continue
        
        league_info = FBREF_LEAGUES[league_name]
        matches = scrape_league(league_info['name'], league_info['id'], season, league_info.get('name'))
        all_matches.extend(matches)
        
        # Rate limiting
        time.sleep(1)
    
    TUI.success(f"\nTotal matches scraped: {len(all_matches)}")
    
    # Save results - output raw match data
    result_path = Path(__file__).parent / "fbref_scores.json"
    output = {
        'matches': all_matches,
        'total_matches': len(all_matches),
        'season': season
    }
    
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    TUI.success(f"Results saved to: {result_path}")


if __name__ == "__main__":
    main()

