"""Livescore scraper for match scores, results, and odds."""
import json
import sys
import time
import re
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from bs4 import BeautifulSoup

# Add src directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.tui import TUI
from shared.scraper_utils import init_proxy_manager, get_proxy_manager
from shared.request_with_fallback import request_with_fallback, get_request_delay, RateLimitError
from shared.long_request_warning import LongRequestWarning
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

# GraphQL endpoint for odds (same as FlashScore)
ODDS_GRAPHQL_BASE = "https://global.ds.lsapp.eu/odds/pq_graphql"
PROJECT_ID = 401


def fetch_match_odds(event_id: str, geo_code: str = "BR", geo_subdivision: str = "BRSP") -> Optional[List[Dict]]:
    """Fetch odds for a specific match using GraphQL API.
    
    Args:
        event_id: Match event ID (e.g., "QJkIQSvA")
        geo_code: Geo IP code (default: "BR")
        geo_subdivision: Geo IP subdivision code (default: "BRSP")
        
    Returns:
        List of odds dictionaries with bookmaker and odds data, or None if failed
    """
    try:
        url = f"{ODDS_GRAPHQL_BASE}?_hash=oce&eventId={event_id}&projectId={PROJECT_ID}&geoIpCode={geo_code}&geoIpSubdivisionCode={geo_subdivision}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.livescore.com/',
            'Accept': 'application/json'
        }
        
        with LongRequestWarning(threshold_seconds=25.0,
                               warning_message="Livescore odds API request is taking longer than expected..."):
            response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
            
        data = response.json()
        odds_comparison = data.get('data', {}).get('findOddsByEventId', {})
        if not odds_comparison:
            return None
            
        markets = odds_comparison.get('markets', [])
        all_odds = []
        
        for market in markets:
            market_name = market.get('name', '')
            market_type = market.get('marketType', '')
            outcomes = market.get('outcomes', [])
            
            for outcome in outcomes:
                outcome_name = outcome.get('name', '')
                bookmaker_odds = outcome.get('bookmakerOdds', [])
                
                for bookmaker_odd in bookmaker_odds:
                    bookmaker = bookmaker_odd.get('bookmaker', {})
                    odds_value = bookmaker_odd.get('odds', None)
                    
                    if odds_value and bookmaker:
                        all_odds.append({
                            'market_name': market_name,
                            'market_type': market_type,
                            'outcome_name': outcome_name,
                            'bookmaker_id': bookmaker.get('id'),
                            'bookmaker_name': bookmaker.get('name'),
                            'odds_value': float(odds_value) if odds_value else None
                        })
        
        return all_odds if all_odds else None
        
    except Exception as e:
        TUI.warning(f"Failed to fetch odds for event {event_id}: {e}")
        return None


def fetch_league_winner_odds(tournament_id: str, geo_code: str = "BR", geo_subdivision: str = "SP") -> Optional[List[Dict]]:
    """Fetch league winner odds for a tournament using GraphQL API.
    
    Args:
        tournament_id: Tournament/league ID (e.g., "KKay4EE8")
        geo_code: Geo IP code (default: "BR")
        geo_subdivision: Geo IP subdivision code (default: "SP")
        
    Returns:
        List of league winner odds dictionaries with team and bookmaker data, or None if failed
    """
    try:
        url = f"{ODDS_GRAPHQL_BASE}?_hash=lwo&tournamentId={tournament_id}&projectId={PROJECT_ID}&geoIpCode={geo_code}&geoIpSubdivisionCode={geo_subdivision}&page=1"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.livescore.com/',
            'Accept': 'application/json'
        }
        
        with LongRequestWarning(threshold_seconds=25.0,
                               warning_message="Livescore league winner odds API request is taking longer than expected..."):
            response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
            
        data = response.json()
        league_winner_odds = data.get('data', {}).get('getLeagueWinnerOdds', {})
        if not league_winner_odds:
            return None
            
        participants = league_winner_odds.get('participants', [])
        odds_list = league_winner_odds.get('odds', [])
        bookmakers_list = league_winner_odds.get('settings', {}).get('bookmakers', [])
        
        # Create lookup maps
        participants_map = {p.get('id'): p.get('name') for p in participants}
        bookmakers_map = {bm.get('bookmaker', {}).get('id'): bm.get('bookmaker', {}).get('name') 
                         for bm in bookmakers_list}
        
        all_odds = []
        for odd in odds_list:
            participant_id = odd.get('participantId')
            bookmaker_id = odd.get('bookmakerId')
            odds_value = odd.get('value')
            
            if participant_id and bookmaker_id and odds_value:
                team_name = participants_map.get(participant_id, '')
                bookmaker_name = bookmakers_map.get(bookmaker_id, '')
                
                if team_name and bookmaker_name:
                    all_odds.append({
                        'market_name': 'League Winner',
                        'market_type': 'league_winner',
                        'team_name': team_name,
                        'team_id': participant_id,
                        'bookmaker_id': bookmaker_id,
                        'bookmaker_name': bookmaker_name,
                        'odds_value': float(odds_value) if odds_value else None
                    })
        
        return all_odds if all_odds else None
        
    except Exception as e:
        TUI.warning(f"Failed to fetch league winner odds for tournament {tournament_id}: {e}")
        return None


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
                                    
                                    # Filter out esports matches
                                    from shared.match_utils import is_esports_match
                                    if is_esports_match(home_team_name, away_team_name):
                                        continue
                                    
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
                                    
                                    # Extract event ID from event data
                                    event_id = event.get('eventId') or event.get('id')
                                    
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
                                    
                                    # Fetch odds if event ID found
                                    if event_id:
                                        odds = fetch_match_odds(str(event_id))
                                        if odds:
                                            match['odds'] = odds
                                            TUI.info(f"    Found {len(odds)} odds for {home_team_name} vs {away_team_name}")
                                        time.sleep(0.5)  # Delay between odds requests to avoid rate limiting
                                    
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


def extract_tournament_id_from_html(html: str) -> Optional[str]:
    """Extract tournament ID from HTML page.
    
    Args:
        html: Page HTML content
        
    Returns:
        Tournament ID string or None if not found
    """
    try:
        # Look for tournament ID in various patterns
        patterns = [
            r'tournamentId["\']?\s*[:=]\s*["\']?([A-Za-z0-9]{8})',
            r'tournament["\']?\s*[:=]\s*["\']?([A-Za-z0-9]{8})',
            r'leagueId["\']?\s*[:=]\s*["\']?([A-Za-z0-9]{8})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.I)
            if match:
                return match.group(1)
        
        # Try to find in __NEXT_DATA__
        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script', id='__NEXT_DATA__')
        for script in scripts:
            if script.string:
                try:
                    data = json.loads(script.string)
                    # Navigate to find tournament ID
                    if 'props' in data and 'pageProps' in data['props']:
                        page_props = data['props']['pageProps']
                        if 'initialData' in page_props:
                            initial_data = page_props['initialData']
                            tournament_id = initial_data.get('tournamentId') or initial_data.get('tournament', {}).get('id')
                            if tournament_id:
                                return str(tournament_id)
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue
                    
        return None
        
    except Exception as e:
        TUI.warning(f"Failed to extract tournament ID: {e}")
        return None


def scrape_league(league_name: str, season: str = None) -> Tuple[List[Dict], bool, Optional[List[Dict]]]:
    """Scrape matches for a specific league."""
    # Normalize league name (handle encoding issues cross-platform)
    normalized_name = normalize_league_name(league_name, LEAGUE_MAPPING)
    if normalized_name is None:
        TUI.warning(f"Unknown league: {league_name}")
        return [], False, None
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
            return [], False, None
        
        if response.status_code != 200:
            TUI.error(f"Failed to fetch {league_name}: Status {response.status_code}")
            return [], False, None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        matches = extract_matches_from_html(soup, league_name, season)
        
        # Try to fetch league winner odds
        tournament_id = extract_tournament_id_from_html(response.text)
        league_winner_odds = None
        if tournament_id:
            league_winner_odds = fetch_league_winner_odds(tournament_id)
            if league_winner_odds:
                TUI.info(f"  Found {len(league_winner_odds)} league winner odds")
        
        TUI.success(f"Found {len(matches)} completed matches in {league_name}")
        return matches, False, league_winner_odds
        
    except RateLimitError as e:
        TUI.error(f"Rate limited scraping {league_name}: {e}")
        return [], True
    except Exception as e:
        error_str = str(e)
        if '403' in error_str or 'Forbidden' in error_str:
            TUI.warning(f"Access denied (403) for {league_name} - skipping")
            return [], False, None
        TUI.error(f"Error scraping {league_name}: {e}")
        return [], False, None


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
        
        matches, was_rate_limited, league_winner_odds = scrape_league(normalized_name, season)
        all_matches.extend(matches)
        
        # Store league winner odds if available (could be added to output structure)
        if league_winner_odds:
            TUI.info(f"  League winner odds: {len(league_winner_odds)} entries")
        
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
