"""Livescore scraper for match scores and results."""
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

from bs4 import BeautifulSoup

# Add src directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.tui import TUI
from shared.scraper_utils import init_proxy_manager, get_proxy_manager
from shared.request_with_fallback import request_with_fallback, get_request_delay, RateLimitError
from shared.match_utils import (
    get_current_season,
    parse_datetime_string,
    format_start_time,
    format_match_date,
    create_match_dict
)
from shared.league_utils import normalize_league_name
from shared.league_config import get_livescore_leagues

# Load league mapping from centralized config
LEAGUE_MAPPING = get_livescore_leagues()


def extract_matches_from_html(soup: BeautifulSoup, league_name: str, season: str) -> List[Dict]:
    """Extract match data from Livescore HTML.
    
    Strategy:
    1. Try to find embedded JSON in script tags (Next.js __NEXT_DATA__)
    2. Fallback to HTML parsing
    """
    matches = []
    
    # Strategy 1: Look for Next.js __NEXT_DATA__
    scripts = soup.find_all('script', id='__NEXT_DATA__')
    for script in scripts:
        if script.string:
            try:
                data = json.loads(script.string)
                
                # Navigate to initialData -> stages -> events
                if 'props' in data and 'pageProps' in data['props']:
                    page_props = data['props']['pageProps']
                    if 'initialData' in page_props:
                        initial_data = page_props['initialData']
                        
                        # Look for stages
                        if 'stages' in initial_data and len(initial_data['stages']) > 0:
                            stage = initial_data['stages'][0]
                            
                            # Look for events
                            if 'events' in stage:
                                events = stage['events']
                                TUI.info(f"Found {len(events)} events in __NEXT_DATA__")
                                
                                # Process each event
                                for event in events:
                                    # Only process finished matches
                                    if event.get('eventStatus') != 'PAST' or event.get('status') not in ['FT', 'AET', 'PEN']:
                                        continue
                                    
                                    # Extract match data
                                    home_team_name = event.get('homeTeamName', '').strip()
                                    away_team_name = event.get('awayTeamName', '').strip()
                                    
                                    # Parse scores
                                    try:
                                        home_score = int(event.get('homeTeamScore', '0') or '0')
                                        away_score = int(event.get('awayTeamScore', '0') or '0')
                                    except (ValueError, TypeError):
                                        continue
                                    
                                    # Parse datetime
                                    start_dt_str = event.get('startDateTimeString', '')
                                    if not start_dt_str:
                                        continue
                                    
                                    start_dt = parse_datetime_string(start_dt_str)
                                    if not start_dt:
                                        continue
                                    
                                    # Create match dict
                                    match = create_match_dict(
                                        home_team_name=home_team_name,
                                        away_team_name=away_team_name,
                                        home_score=home_score,
                                        away_score=away_score,
                                        start_time_iso=format_start_time(start_dt),
                                        status='finished',
                                        match_date_yyyymmdd=format_match_date(start_dt),
                                        league=league_name,
                                        season=season
                                    )
                                    matches.append(match)
                                
                                return matches  # Return early if we found matches
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                TUI.warning(f"Error parsing __NEXT_DATA__: {e}")
                continue
    
    # Strategy 2: HTML parsing (fallback)
    # Livescore uses Next.js SSR, so __NEXT_DATA__ should always be present
    # If we reach here, it means no matches were found in the data
    if not matches:
        TUI.warning("No matches found in __NEXT_DATA__")
    
    return matches


def scrape_league(league_name: str, season: str = None) -> Tuple[List[Dict], bool]:
    """Scrape matches for a specific league."""
    # Normalize league name (handle encoding issues cross-platform)
    normalized_name = normalize_league_name(league_name, LEAGUE_MAPPING)
    if normalized_name is None:
        TUI.warning(f"Unknown league: {league_name}")
        return [], False
    league_name = normalized_name
    
    if season is None:
        season = get_current_season()
    
    league_info = LEAGUE_MAPPING[league_name]
    url = f"https://www.livescore.com/en/football/{league_info['country']}/{league_info['slug']}/"
    
    TUI.info(f"Scraping {league_name} ({season})...")
    
    try:
        response = request_with_fallback(
            'get', url,
            max_retries=3,
            use_proxy=True,
            timeout=30,
            referer='https://www.livescore.com/',
            origin='https://www.livescore.com',
            accept='text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            accept_language='en-US,en;q=0.9'
        )
        
        if response.status_code == 403:
            TUI.warning(f"Access denied (403) for {league_name} - skipping")
            return [], False
        
        if response.status_code != 200:
            TUI.error(f"Failed to fetch {league_name}: Status {response.status_code}")
            return [], False
        
        soup = BeautifulSoup(response.text, 'html.parser')
        matches = extract_matches_from_html(soup, league_name, season)
        
        TUI.success(f"Found {len(matches)} completed matches in {league_name}")
        return matches, False
        
    except RateLimitError as e:
        TUI.error(f"Rate limited scraping {league_name}: {e}")
        return [], True
    except Exception as e:
        error_str = str(e)
        if '403' in error_str or 'Forbidden' in error_str:
            TUI.warning(f"Access denied (403) for {league_name} - skipping")
            return [], False
        TUI.error(f"Error scraping {league_name}: {e}")
        return [], False


def main():
    """Main function to scrape Livescore scores."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Livescore Scores Scraper')
    parser.add_argument('--no-proxy', action='store_true', default=False,
                       help='Disable proxy usage')
    parser.add_argument('--use-proxy', dest='no_proxy', action='store_false',
                       help='Enable proxy usage (default)')
    parser.add_argument('--refresh-proxies', action='store_true', default=False,
                       help='Auto-refresh proxies if < 5 working')
    parser.add_argument('--season', help='Season to scrape (e.g., 2024-2025). Default: current season')
    parser.add_argument('--leagues', nargs='+', help='Specific leagues to scrape. Default: all')
    
    args = parser.parse_args()
    
    init_proxy_manager(no_proxy=args.no_proxy, refresh_proxies_flag=args.refresh_proxies)
    proxy_manager = get_proxy_manager()
    
    TUI.header("Livescore Scores Scraper")
    
    season = args.season or get_current_season()
    TUI.info(f"Scraping season: {season}")
    
    leagues_to_scrape = args.leagues if args.leagues else list(LEAGUE_MAPPING.keys())
    
    all_matches = []
    rate_limited_count = 0
    
    for i, league_name in enumerate(leagues_to_scrape):
        # Normalize league name first (handles encoding issues)
        normalized_name = normalize_league_name(league_name, LEAGUE_MAPPING)
        if normalized_name is None:
            TUI.warning(f"Unknown league: {league_name}, skipping")
            continue
        
        matches, was_rate_limited = scrape_league(normalized_name, season)
        all_matches.extend(matches)
        
        if was_rate_limited:
            rate_limited_count += 1
            if rate_limited_count >= 3:
                TUI.warning("Multiple rate limits hit. Pausing for 60 seconds...")
                time.sleep(60)
                rate_limited_count = 0
        else:
            rate_limited_count = 0
        
        if i < len(leagues_to_scrape) - 1:
            delay = get_request_delay(proxy_manager)
            TUI.info(f"Waiting {delay:.1f}s before next league...")
            time.sleep(delay)
    
    TUI.success(f"\nTotal matches scraped: {len(all_matches)}")
    
    output = {
        'matches': all_matches,
        'total_matches': len(all_matches),
        'season': season
    }
    
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
