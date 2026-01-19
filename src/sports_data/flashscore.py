"""Flashscore scraper for match scores, results, and odds."""
import json
import sys
import time
import re
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup

# Add src directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.tui import TUI
from shared.match_utils import get_current_season
from shared.browser_utils import get_playwright_context, wait_for_content
from shared.league_utils import normalize_league_name
from shared.league_config import get_flashscore_leagues

# League mapping from centralized config
LEAGUE_MAPPING = get_flashscore_leagues()

# GraphQL endpoint for odds
ODDS_GRAPHQL_BASE = "https://global.ds.lsapp.eu/odds/pq_graphql"
PROJECT_ID = 401


def extract_matches_from_html(soup: BeautifulSoup, league_name: str, season: str, page_html: str = "") -> List[Dict]:
    """Extract match data from Flashscore HTML.
    
    Strategy:
    1. Find match containers (div.event__match)
    2. Extract team names, scores, and time from each match
    """
    from shared.match_utils import (
        format_start_time,
        format_match_date,
        create_match_dict
    )
    from datetime import datetime
    import re
    
    matches = []
    
    # Find all match containers
    # Try multiple selector strategies
    match_containers = []
    
    # Strategy 1: List-based class matching
    containers1 = soup.find_all('div', class_=lambda x: x and isinstance(x, list) and any('event__match' in str(c) for c in x))
    match_containers.extend(containers1)
    
    # Strategy 2: Regex-based class matching
    if not match_containers:
        containers2 = soup.find_all('div', class_=re.compile(r'event__match', re.I))
        match_containers.extend(containers2)
    
    # Strategy 3: String-based class matching (for BeautifulSoup 4.12+)
    if not match_containers:
        containers3 = soup.find_all('div', class_=lambda x: x and 'event__match' in str(x))
        match_containers.extend(containers3)
    
    TUI.info(f"Found {len(match_containers)} match containers")
    
    for match_div in match_containers:
        try:
            # Extract time
            time_elem = match_div.find('div', class_=lambda x: x and isinstance(x, list) and 'event__time' in ' '.join(x))
            if not time_elem:
                time_elem = match_div.find('div', class_=re.compile(r'event__time', re.I))
            
            if not time_elem:
                continue
            
            time_str = time_elem.get_text(strip=True)
            if not time_str:
                continue
            
            # Parse time (format: "17.01. 14:30" -> "2026-01-17 14:30:00")
            # Extract date and time
            time_parts = time_str.split()
            if len(time_parts) < 2:
                continue
            
            date_part = time_parts[0]  # "17.01."
            time_part = time_parts[1]  # "14:30"
            
            # Parse date (DD.MM. format, assume current year)
            try:
                day, month = date_part.rstrip('.').split('.')
                current_year = datetime.now().year
                # If month > current month, assume previous year
                if int(month) > datetime.now().month:
                    current_year -= 1
                
                # Parse time
                hour, minute = time_part.split(':')
                
                start_dt = datetime(current_year, int(month), int(day), int(hour), int(minute))
            except (ValueError, IndexError):
                continue
            
            # Extract home team
            home_elem = match_div.find('div', class_=lambda x: x and isinstance(x, list) and 'event__homeParticipant' in ' '.join(x))
            if not home_elem:
                home_elem = match_div.find('div', class_=re.compile(r'event__homeParticipant', re.I))
            
            if not home_elem:
                continue
            
            home_team_name = home_elem.get_text(strip=True)
            if not home_team_name:
                # Try to find text in nested span
                name_span = home_elem.find('span', class_=lambda x: x and isinstance(x, list) and 'name' in ' '.join(x))
                if name_span:
                    home_team_name = name_span.get_text(strip=True)
            
            # Extract away team
            away_elem = match_div.find('div', class_=lambda x: x and isinstance(x, list) and 'event__awayParticipant' in ' '.join(x))
            if not away_elem:
                away_elem = match_div.find('div', class_=re.compile(r'event__awayParticipant', re.I))
            
            if not away_elem:
                continue
            
            away_team_name = away_elem.get_text(strip=True)
            if not away_team_name:
                # Try to find text in nested span
                name_span = away_elem.find('span', class_=lambda x: x and isinstance(x, list) and 'name' in ' '.join(x))
                if name_span:
                    away_team_name = name_span.get_text(strip=True)
            
            # Extract scores
            score_home_elem = match_div.find('span', class_=lambda x: x and isinstance(x, list) and 'event__score--home' in ' '.join(x))
            if not score_home_elem:
                score_home_elem = match_div.find('span', class_=re.compile(r'event__score.*home', re.I))
            
            score_away_elem = match_div.find('span', class_=lambda x: x and isinstance(x, list) and 'event__score--away' in ' '.join(x))
            if not score_away_elem:
                score_away_elem = match_div.find('span', class_=re.compile(r'event__score.*away', re.I))
            
            if not score_home_elem or not score_away_elem:
                continue
            
            try:
                home_score = int(score_home_elem.get_text(strip=True))
                away_score = int(score_away_elem.get_text(strip=True))
            except (ValueError, TypeError):
                continue
            
            # Only include finished matches (scores are present)
            if home_score is None or away_score is None:
                continue
            
            # Extract event ID for odds fetching
            event_id = extract_event_id_from_match(match_div, page_html)
            
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
                odds = fetch_match_odds(event_id)
                if odds:
                    match['odds'] = odds
                    TUI.info(f"    Found {len(odds)} odds for {home_team_name} vs {away_team_name}")
                time.sleep(0.5)  # Delay between odds requests to avoid rate limiting
            
            matches.append(match)
            
        except Exception as e:
            TUI.warning(f"Error extracting match: {e}")
            continue
    
    return matches


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
            'Referer': 'https://www.flashscore.com/',
            'Accept': 'application/json'
        }
        
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
            'Referer': 'https://www.flashscore.com/',
            'Accept': 'application/json'
        }
        
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


def extract_tournament_id_from_page(page: Page, league_slug: str) -> Optional[str]:
    """Extract tournament ID from league page.
    
    Args:
        page: Playwright page object
        league_slug: League slug for URL construction
        
    Returns:
        Tournament ID string or None if not found
    """
    try:
        # Try to find tournament ID in page HTML or JavaScript
        html = page.content()
        
        # Look for tournament ID in various patterns
        patterns = [
            r'tournamentId["\']?\s*[:=]\s*["\']?([A-Za-z0-8]{8})',
            r'tournament["\']?\s*[:=]\s*["\']?([A-Za-z0-9]{8})',
            r'leagueId["\']?\s*[:=]\s*["\']?([A-Za-z0-9]{8})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.I)
            if match:
                return match.group(1)
        
        # Try to find in URL parameters or data attributes
        url = page.url
        url_match = re.search(r'tournament[_-]?id=([A-Za-z0-9]{8})', url, re.I)
        if url_match:
            return url_match.group(1)
            
        return None
        
    except Exception as e:
        TUI.warning(f"Failed to extract tournament ID: {e}")
        return None


def extract_event_id_from_match(match_div, page_html: str = "") -> Optional[str]:
    """Extract event ID from match container or page HTML.
    
    Args:
        match_div: BeautifulSoup match container element
        page_html: Full page HTML as fallback
        
    Returns:
        Event ID string or None if not found
    """
    # Try to find event ID in data attributes
    event_id = match_div.get('data-id') or match_div.get('id')
    if event_id and len(event_id) >= 8:
        return event_id
    
    # Try to find in link href
    link = match_div.find('a', href=True)
    if link:
        href = link.get('href', '')
        # Look for mid parameter: ?mid=QJkIQSvA
        mid_match = re.search(r'[?&]mid=([A-Za-z0-9]{8})', href)
        if mid_match:
            return mid_match.group(1)
        # Look for event ID in path: /jogo/.../mid/QJkIQSvA
        path_match = re.search(r'/([A-Za-z0-9]{8})(?:/|$|\?)', href)
        if path_match:
            return path_match.group(1)
    
    # Try to find in page HTML near the match
    if page_html:
        # Look for data-event-id or similar patterns
        match_html = str(match_div)
        # Search for event IDs near this match HTML
        event_id_match = re.search(r'event[_-]?id["\']?\s*[:=]\s*["\']?([A-Za-z0-9]{8})', match_html, re.I)
        if event_id_match:
            return event_id_match.group(1)
    
    return None


def extract_matches_from_page(page: Page, league_name: str, season: str) -> List[Dict]:
    """Extract match data from Flashscore page using Playwright.
    
    Strategy:
    1. Wait for page to fully load (networkidle)
    2. Extract from rendered HTML using same logic as non-Playwright version
    """
    # Wait for page to load
    try:
        page.wait_for_load_state('networkidle', timeout=30000)
    except:
        pass
    
    # Additional wait for JS rendering
    time.sleep(2)
    
    # Get rendered HTML
    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')
    
    # Use the same extraction logic
    matches = extract_matches_from_html(soup, league_name, season, page_html=html)
    
    return matches


def scrape_league(league_name: str, season: str = None, context=None) -> Tuple[List[Dict], bool]:
    """Scrape matches for a specific league using Playwright."""
    # Normalize league name (handle encoding issues cross-platform)
    normalized_name = normalize_league_name(league_name, LEAGUE_MAPPING)
    if normalized_name is None:
        TUI.warning(f"Unknown league: {league_name}")
        return [], False
    
    if season is None:
        season = get_current_season()
    
    league_info = LEAGUE_MAPPING[normalized_name]
    url = f"https://www.flashscore.com/football/{league_info['country']}/{league_info['slug']}/results/"
    
    TUI.info(f"Scraping {normalized_name} ({season})...")
    
    try:
        page = context.new_page()
        
        page.goto(url, wait_until='domcontentloaded', timeout=60000)
        
        # Wait for content with human-like delay
        time.sleep(2)
        wait_for_content(page)
        time.sleep(2)  # Extra wait for JS rendering
        
        matches = extract_matches_from_page(page, normalized_name, season)
        
        # Try to fetch league winner odds
        tournament_id = extract_tournament_id_from_page(page, league_info['slug'])
        league_winner_odds = None
        if tournament_id:
            league_winner_odds = fetch_league_winner_odds(tournament_id)
            if league_winner_odds:
                TUI.info(f"  Found {len(league_winner_odds)} league winner odds")
        
        page.close()
        
        TUI.success(f"Found {len(matches)} completed matches in {normalized_name}")
        return matches, False, league_winner_odds
        
    except Exception as e:
        TUI.error(f"Error scraping {normalized_name}: {e}")
        return [], False


def main():
    """Main function to scrape Flashscore scores."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Flashscore Scores Scraper')
    parser.add_argument('--season', help='Season to scrape (e.g., 2024-2025). Default: current season')
    parser.add_argument('--leagues', nargs='+', help='Specific leagues to scrape. Default: all')
    parser.add_argument('--headless', action='store_true', default=False, help='Run in headless mode')
    
    args = parser.parse_args()
    
    TUI.header("Flashscore Scores Scraper")
    
    season = args.season or get_current_season()
    TUI.info(f"Scraping season: {season}")
    
    leagues_to_scrape = args.leagues if args.leagues else list(LEAGUE_MAPPING.keys())
    
    all_matches = []
    
    with sync_playwright() as p:
        browser, context = get_playwright_context(p, headless=args.headless)
        
        for i, league_name in enumerate(leagues_to_scrape):
            # Normalize league name first (handles encoding issues)
            normalized_name = normalize_league_name(league_name, LEAGUE_MAPPING)
            if normalized_name is None:
                TUI.warning(f"Unknown league: {league_name}, skipping")
                continue
            
            matches, _, league_winner_odds = scrape_league(normalized_name, season, context)
            all_matches.extend(matches)
            
            # Store league winner odds if available (could be added to output structure)
            if league_winner_odds:
                TUI.info(f"  League winner odds: {len(league_winner_odds)} entries")
            
            if i < len(leagues_to_scrape) - 1:
                time.sleep(2)  # Delay between leagues
        
        browser.close()
    
    TUI.success(f"\nTotal matches scraped: {len(all_matches)}")
    
    output = {
        'matches': all_matches,
        'total_matches': len(all_matches),
        'season': season
    }
    
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
