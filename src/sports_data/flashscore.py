"""Flashscore scraper for match scores, results, and odds.

Scrapes a single league per execution. For parallel execution, call this script
multiple times with different --league arguments.
"""
import json
import sys
import time
import re
import requests
import threading
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.exceptions import (
    SSLError, ConnectionError, Timeout, 
    RequestException, ChunkedEncodingError
)
from urllib3.exceptions import ProtocolError, ReadTimeoutError

from playwright.sync_api import sync_playwright, Page, BrowserContext
from bs4 import BeautifulSoup

# Add src directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.tui import TUI
from shared.match_utils import get_current_season
from shared.browser_utils import get_playwright_context, wait_for_content
from shared.league_utils import normalize_league_name
from shared.league_config import get_flashscore_leagues
from shared.long_request_warning import LongRequestWarning

# League mapping from centralized config
LEAGUE_MAPPING = get_flashscore_leagues()

# GraphQL endpoint for odds
ODDS_GRAPHQL_BASE = "https://global.ds.lsapp.eu/odds/pq_graphql"
PROJECT_ID = 401

# Thread-safe lock for TUI output (for odds parallelization within a league)
_tui_lock = threading.Lock()


def _safe_log(level: str, message: str) -> None:
    """Thread-safe logging via TUI for odds fetching."""
    with _tui_lock:
        if level == "info":
            TUI.info(message)
        elif level == "warning":
            TUI.warning(message)
        elif level == "error":
            TUI.error(message)
        elif level == "success":
            TUI.success(message)
        
        # Force flush to ensure output appears immediately
        sys.stderr.flush()
        sys.stdout.flush()


def fetch_match_odds(event_id: str, geo_code: str = "BR", geo_subdivision: str = "BRSC", 
                     market_types: Optional[List[str]] = None) -> Optional[List[Dict]]:
    """Fetch odds for a specific match using GraphQL API.
    
    Args:
        event_id: Match event ID (e.g., "QJkIQSvA")
        geo_code: Geo IP code (default: "BR")
        geo_subdivision: Geo IP subdivision code (default: "BRSC")
        market_types: Optional list of market types to filter (e.g., ["HOME_DRAW_AWAY", "OVER_UNDER", "BOTH_TEAMS_TO_SCORE"]).
                     If None, returns all market types.
        
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
        
        # Add small delay to avoid rate limiting (100ms between requests for better rate limit handling)
        time.sleep(0.1)
        
        try:
            # Disable requests' automatic retries - we handle retries ourselves with exponential backoff
            session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(max_retries=0)  # Disable automatic retries
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            response = session.get(url, headers=headers, timeout=15)
        except (SSLError, ConnectionError, Timeout, ChunkedEncodingError, ProtocolError, ReadTimeoutError) as e:
            # Connection/SSL errors - return special marker for retry with exponential backoff
            return "CONNECTION_ERROR"
        except RequestException as e:
            # Other request exceptions
            return "CONNECTION_ERROR"
        
        if response.status_code == 429:
            # Rate limited - return special marker for retry with backoff
            return "RATE_LIMITED"
        if response.status_code != 200:
            # Log non-200 status for debugging
            _safe_log("warning", f"⚠️ FlashScore API returned status {response.status_code} for event_id={event_id}")
            return None
            
        try:
            data = response.json()
        except Exception as e:
            _safe_log("warning", f"⚠️ Failed to parse JSON for event_id={event_id}: {e}")
            return None
            
        odds_comparison = data.get('data', {}).get('findOddsByEventId', {})
        if not odds_comparison:
            # Check if there's an error in the response
            errors = data.get('errors', [])
            if errors:
                _safe_log("warning", f"⚠️ GraphQL errors for event_id={event_id}: {errors}")
            else:
                # Log when odds_comparison is empty (might indicate invalid event_id)
                _safe_log("warning", f"⚠️ No odds_comparison data for event_id={event_id} (response keys: {list(data.keys())})")
            return None
        
        # Get bookmaker mapping from settings
        settings = odds_comparison.get('settings', {})
        bookmakers_list = settings.get('bookmakers', [])
        bookmakers_map = {}
        for bm in bookmakers_list:
            bookmaker_obj = bm.get('bookmaker', {})
            bookmaker_id = bookmaker_obj.get('id')
            bookmaker_name = bookmaker_obj.get('name')
            if bookmaker_id and bookmaker_name:
                bookmakers_map[bookmaker_id] = bookmaker_name
        
        # Parse odds array (not markets!)
        odds_array = odds_comparison.get('odds', [])
        if not odds_array:
            _safe_log("warning", f"⚠️ No odds array found for event_id={event_id}")
            return None
            
        all_odds = []
        
        # Map betting types to readable names
        betting_type_names = {
            'HOME_DRAW_AWAY': '1X2',
            'OVER_UNDER': 'Over/Under',
            'BOTH_TEAMS_TO_SCORE': 'Both Teams to Score',
            'ASIAN_HANDICAP': 'Asian Handicap',
            'EUROPEAN_HANDICAP': 'European Handicap',
            'DOUBLE_CHANCE': 'Double Chance',
            'DRAW_NO_BET': 'Draw No Bet',
            'HALF_FULL_TIME': 'Half/Full Time',
            'CORRECT_SCORE': 'Correct Score',
            'ODD_OR_EVEN': 'Odd/Even'
        }
        
        for odds_entry in odds_array:
            bookmaker_id = odds_entry.get('bookmakerId')
            betting_type = odds_entry.get('bettingType', '')
            betting_scope = odds_entry.get('bettingScope', 'FULL_TIME')
            odds_items = odds_entry.get('odds', [])
            
            if not bookmaker_id or not odds_items:
                continue
            
            # Filter by market types if specified
            if market_types is not None and betting_type not in market_types:
                continue
            
            bookmaker_name = bookmakers_map.get(bookmaker_id, f'Bookmaker_{bookmaker_id}')
            market_name = betting_type_names.get(betting_type, betting_type)
            
            for odd_item in odds_items:
                odds_value = odd_item.get('value')
                if not odds_value:
                    continue
                
                # Extract outcome information
                event_participant_id = odd_item.get('eventParticipantId')
                selection = odd_item.get('selection')  # OVER/UNDER, ODD/EVEN, etc.
                handicap = odd_item.get('handicap')
                score = odd_item.get('score')  # For correct score
                winner = odd_item.get('winner')  # For half/full time (e.g., "1/1", "X/2")
                both_teams_to_score = odd_item.get('bothTeamsToScore')
                
                # Build outcome name
                outcome_name = ''
                if score:
                    outcome_name = score
                elif winner:
                    outcome_name = winner
                elif selection:
                    outcome_name = selection
                elif event_participant_id:
                    # Home/Away - we'll use the participant ID as identifier
                    outcome_name = 'Home' if event_participant_id else 'Away'
                elif both_teams_to_score is not None:
                    outcome_name = 'Yes' if both_teams_to_score else 'No'
                else:
                    outcome_name = 'Draw' if event_participant_id is None else 'Unknown'
                
                # Add handicap info if present
                handicap_value = None
                if handicap and isinstance(handicap, dict):
                    handicap_value = handicap.get('value')
                
                try:
                    all_odds.append({
                        'market_name': market_name,
                        'market_type': betting_type,
                        'betting_scope': betting_scope,
                        'outcome_name': outcome_name,
                        'bookmaker_id': bookmaker_id,
                        'bookmaker_name': bookmaker_name,
                        'odds_value': float(odds_value),
                        'handicap': handicap_value,
                        'event_participant_id': event_participant_id
                    })
                except (ValueError, TypeError):
                    continue
        
        return all_odds if all_odds else None
        
    except (SSLError, ConnectionError, Timeout, ChunkedEncodingError, ProtocolError, ReadTimeoutError) as e:
        # Connection/SSL errors - return special marker for retry with exponential backoff
        return "CONNECTION_ERROR"
    except RequestException as e:
        # Other request exceptions
        return "CONNECTION_ERROR"
    except Exception as e:
        _safe_log("warning", f"⚠️ Exception fetching odds for event_id={event_id}: {e}")
        return None


def fetch_odds_with_retry(event_id: str, max_retries: int = 5, geo_code: str = "BR", geo_subdivision: str = "BRSC",
                          market_types: Optional[List[str]] = None) -> Tuple[str, Optional[List[Dict]]]:
    """Fetch odds with exponential backoff retry on failure.
    
    Handles:
    - Rate limiting (429): Exponential backoff up to 8s
    - Connection/SSL errors: Exponential backoff up to 16s
    - Other failures: Linear backoff
    
    Args:
        event_id: Match event ID
        max_retries: Maximum number of retry attempts
        geo_code: Geo IP code (default: "BR")
        geo_subdivision: Geo IP subdivision code (default: "BRSC")
        market_types: Optional list of market types to filter
        
    Returns:
        Tuple of (event_id, odds_list or None)
    """
    for attempt in range(max_retries):
        odds = fetch_match_odds(event_id, geo_code, geo_subdivision, market_types)
        
        # Check if we got actual odds data
        if odds is not None and odds not in ("RATE_LIMITED", "CONNECTION_ERROR"):
            return (event_id, odds)
        
        # Don't retry on last attempt
        if attempt >= max_retries - 1:
            break
        
        # Calculate wait time based on error type
        if odds == "RATE_LIMITED":
            # Rate limited: exponential backoff, cap at 8s
            wait_time = min(2 ** attempt, 8)
        elif odds == "CONNECTION_ERROR":
            # Connection/SSL errors: longer exponential backoff, cap at 16s
            wait_time = min(2 ** (attempt + 1), 16)
        else:
            # Other failures: linear backoff
            wait_time = 0.5 * (attempt + 1)
        
        time.sleep(wait_time)
    
    return (event_id, None)


def fetch_odds_batch(
    event_ids: List[str], 
    max_workers: int = 5,
    league_name: str = "",
    market_types: Optional[List[str]] = None
) -> Dict[str, Optional[List[Dict]]]:
    """Fetch odds for multiple events in parallel with rate limiting.
    
    This is internal to processing a single league - parallelizing odds fetching
    within one league is fine and improves performance.
    
    Args:
        event_ids: List of event IDs to fetch odds for
        max_workers: Maximum number of parallel workers
        league_name: League name for logging context
        market_types: Optional list of market types to filter (e.g., ["HOME_DRAW_AWAY", "OVER_UNDER", "BOTH_TEAMS_TO_SCORE"])
        
    Returns:
        Dict mapping event_id -> odds list (or None if failed)
    """
    if not event_ids:
        return {}
    
    results: Dict[str, Optional[List[Dict]]] = {}
    semaphore = threading.Semaphore(max_workers)
    
    def fetch_with_semaphore(event_id: str) -> Tuple[str, Optional[List[Dict]]]:
        with semaphore:
            return fetch_odds_with_retry(event_id, market_types=market_types)
    
    league_context = f" for {league_name}" if league_name else ""
    TUI.info(f"💰 Fetching odds for {len(event_ids)} matches{league_context}")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_with_semaphore, eid): eid for eid in event_ids}
        
        completed = 0
        failed = 0
        for future in as_completed(futures):
            event_id, odds = future.result()
            results[event_id] = odds
            completed += 1
            if odds is None:
                failed += 1
            
            # Log progress every 25 matches (more frequent updates)
            if completed % 25 == 0 or completed == len(event_ids):
                success_count = completed - failed
                TUI.info(f"  📊 Odds progress{league_context}: {success_count}/{completed} successful ({failed} failed)")
    
    duration = time.time() - start_time
    success_count = len(event_ids) - failed
    TUI.success(f"✅ Odds{league_context}: {success_count}/{len(event_ids)} successful in {duration:.1f}s")
    
    return results


def extract_matches_from_html(
    soup: BeautifulSoup, 
    league_name: str, 
    season: str, 
    page_html: str = "",
    max_workers_odds: int = 5,
    market_types: Optional[List[str]] = None
) -> List[Dict]:
    """Extract match data from Flashscore HTML.
    
    Strategy:
    1. Find match containers (div.event__match)
    2. Extract team names, scores, and time from each match
    3. Collect all event IDs and fetch odds in parallel batch
    
    Args:
        soup: BeautifulSoup parsed HTML
        league_name: Name of the league
        season: Season string
        page_html: Raw HTML for fallback parsing
        max_workers_odds: Max workers for parallel odds fetching (internal to this league)
        
    Returns:
        List of match dictionaries with odds attached
    """
    from shared.match_utils import (
        format_start_time,
        format_match_date,
        create_match_dict
    )
    from datetime import datetime
    
    matches = []
    event_ids_map: Dict[int, str] = {}  # match_index -> event_id
    
    # Find all match containers
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
    
    TUI.info(f"🔍 Found {len(match_containers)} match containers for {league_name}")
    
    for idx, match_div in enumerate(match_containers):
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
                name_span = away_elem.find('span', class_=lambda x: x and isinstance(x, list) and 'name' in ' '.join(x))
                if name_span:
                    away_team_name = name_span.get_text(strip=True)
            
            # Filter out esports matches
            from shared.match_utils import is_esports_match
            if is_esports_match(home_team_name, away_team_name):
                continue
            
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
            
            # Extract event ID for odds fetching (don't fetch yet - collect for batch)
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
            
            # Store event ID for batch fetching
            if event_id:
                event_ids_map[len(matches)] = event_id
            
            matches.append(match)
            
        except Exception as e:
            TUI.warning(f"⚠️ Error extracting match for {league_name}: {e}")
            continue
    
    # Batch fetch all odds in parallel (internal to this league)
    if event_ids_map:
        event_ids = list(event_ids_map.values())
        TUI.info(f"🔍 Extracted {len(event_ids)} event IDs from {len(matches)} matches for {league_name}")
        odds_results = fetch_odds_batch(event_ids, max_workers=max_workers_odds, league_name=league_name, market_types=market_types)
        
        # Attach odds to matches
        matches_with_odds = 0
        for match_idx, event_id in event_ids_map.items():
            odds = odds_results.get(event_id)
            if odds:
                matches[match_idx]['odds'] = odds
                matches_with_odds += 1
        
        if event_ids:
            TUI.info(f"💰 Attached odds to {matches_with_odds}/{len(event_ids)} matches for {league_name}")
    else:
        TUI.warning(f"⚠️ No event IDs extracted from {len(matches)} matches for {league_name}")
    
    return matches


def fetch_league_winner_odds(tournament_id: str, geo_code: str = "BR", geo_subdivision: str = "BRSC") -> Optional[List[Dict]]:
    """Fetch league winner odds for a tournament using GraphQL API.
    
    Args:
        tournament_id: Tournament/league ID (e.g., "KKay4EE8")
        geo_code: Geo IP code (default: "BR")
        geo_subdivision: Geo IP subdivision code (default: "BRSC")
        
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
        
        with LongRequestWarning(threshold_seconds=25.0,
                               warning_message="League winner odds API request is taking longer than expected..."):
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
        TUI.warning(f"⚠️ Failed to fetch league winner odds for tournament {tournament_id}: {e}")
        return None


def extract_tournament_id_from_page(page: Page) -> Optional[str]:
    """Extract tournament ID from league page.
    
    Args:
        page: Playwright page object
        
    Returns:
        Tournament ID string or None if not found
    """
    try:
        html = page.content()
        
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
        
        # Try to find in URL parameters or data attributes
        url = page.url
        url_match = re.search(r'tournament[_-]?id=([A-Za-z0-9]{8})', url, re.I)
        if url_match:
            return url_match.group(1)
            
        return None
        
    except Exception as e:
        TUI.warning(f"⚠️ Failed to extract tournament ID: {e}")
        return None


def extract_event_id_from_match(match_div, page_html: str = "") -> Optional[str]:
    """Extract event ID (match ID) from match container or page HTML.
    
    FlashScore match IDs are exactly 8 alphanumeric characters (e.g., 'bBQm4aAM').
    They appear in URLs as ?mid= parameter or in data attributes.
    
    Args:
        match_div: BeautifulSoup match container element
        page_html: Full page HTML as fallback
        
    Returns:
        Event ID string (8 alphanumeric chars) or None if not found
    """
    def is_valid_match_id(event_id: str) -> bool:
        """Check if event ID is a valid FlashScore match ID (exactly 8 alphanumeric chars)."""
        if not event_id:
            return False
        # Must be exactly 8 alphanumeric characters, no underscores or other chars
        return bool(re.match(r'^[A-Za-z0-9]{8}$', event_id))
    
    # Priority 1: Try to find mid= parameter in link href (most reliable)
    link = match_div.find('a', href=True)
    if link:
        href = link.get('href', '')
        # Extract mid= parameter (exactly 8 chars)
        mid_match = re.search(r'[?&]mid=([A-Za-z0-9]{8})(?:&|$)', href)
        if mid_match:
            event_id = mid_match.group(1)
            if is_valid_match_id(event_id):
                return event_id
    
    # Priority 2: Try data attributes (but filter out GraphQL node IDs like 'g_1_xxx')
    for attr in ['data-id', 'id', 'data-event-id', 'data-match-id']:
        event_id = match_div.get(attr)
        if event_id and is_valid_match_id(event_id):
            # Skip GraphQL node IDs (they contain underscores)
            if '_' not in event_id:
                return event_id
    
    # Priority 3: Try to find in page HTML near the match
    if page_html:
        match_html = str(match_div)
        # Look for mid= parameter in the HTML
        mid_html_match = re.search(r'mid=([A-Za-z0-9]{8})', match_html, re.I)
        if mid_html_match:
            event_id = mid_html_match.group(1)
            if is_valid_match_id(event_id):
                return event_id
        
        # Look for event/match IDs in data attributes or JavaScript
        patterns = [
            r'["\']?mid["\']?\s*[:=]\s*["\']([A-Za-z0-9]{8})["\']',
            r'eventId["\']?\s*[:=]\s*["\']([A-Za-z0-9]{8})["\']',
            r'matchId["\']?\s*[:=]\s*["\']([A-Za-z0-9]{8})["\']',
        ]
        for pattern in patterns:
            event_id_match = re.search(pattern, match_html, re.I)
            if event_id_match:
                event_id = event_id_match.group(1)
                if is_valid_match_id(event_id):
                    return event_id
    
    return None


def _setup_page_resource_blocking(page: Page) -> None:
    """Set up resource blocking on a Playwright page to improve load times and reduce resource usage.
    
    Blocks images, fonts, media, and analytics scripts.
    
    Args:
        page: Playwright page to configure
    """
    # Block images
    page.route("**/*.{png,jpg,jpeg,gif,svg,webp,ico}", lambda route: route.abort())
    # Block fonts
    page.route("**/*.{woff,woff2,ttf,eot,otf}", lambda route: route.abort())
    # Block media
    page.route("**/*.{mp4,webm,ogg,mp3,wav}", lambda route: route.abort())
    # Block analytics and tracking
    page.route("**/analytics/**", lambda route: route.abort())
    page.route("**/tracking/**", lambda route: route.abort())
    page.route("**/gtm.js", lambda route: route.abort())
    page.route("**/ga.js", lambda route: route.abort())
    # Block additional resource-heavy content
    page.route("**/*.css", lambda route: route.abort() if 'font' in route.request.url.lower() else route.continue_())
    page.route("**/ads/**", lambda route: route.abort())
    page.route("**/advertising/**", lambda route: route.abort())


def extract_matches_from_page(
    page: Page, 
    league_name: str, 
    season: str,
    max_workers_odds: int = 5,
    market_types: Optional[List[str]] = None
) -> List[Dict]:
    """Extract match data from Flashscore page using Playwright.
    
    Strategy:
    1. Wait for page to load (domcontentloaded + targeted selector)
    2. Extract from rendered HTML
    3. Fetch odds in parallel batch (internal to this league)
    
    Args:
        page: Playwright page object
        league_name: Name of the league
        season: Season string
        max_workers_odds: Max workers for parallel odds fetching (internal)
        
    Returns:
        List of match dictionaries
    """
    # Wait for page to load using domcontentloaded (faster than networkidle)
    try:
        page.wait_for_load_state('domcontentloaded', timeout=30000)
        # Wait for match containers to appear
        try:
            page.wait_for_selector('div[class*="event__match"]', timeout=10000)
        except:
            # If selector doesn't appear, wait a bit for JS rendering
            time.sleep(0.5)
    except:
        pass
    
    # Get rendered HTML
    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract matches with parallel odds fetching (internal to this league)
    matches = extract_matches_from_html(
        soup, league_name, season, page_html=html, max_workers_odds=max_workers_odds, market_types=market_types
    )
    
    return matches


def scrape_league(
    league_name: str, 
    season: str = None, 
    max_workers_odds: int = 5,
    market_types: Optional[List[str]] = None
) -> Tuple[List[Dict], bool, Optional[List[Dict]]]:
    """Scrape matches for a specific league using Playwright.
    
    This function scrapes a SINGLE league. For multiple leagues, call this
    function multiple times or use the scheduler's parallel execution.
    
    Args:
        league_name: Name of the league to scrape
        season: Season string (default: current season)
        max_workers_odds: Max workers for parallel odds fetching (internal to this league)
        
    Returns:
        Tuple of (matches, error_flag, league_winner_odds)
    """
    # Normalize league name (handle encoding issues cross-platform)
    normalized_name = normalize_league_name(league_name, LEAGUE_MAPPING)
    if normalized_name is None:
        TUI.warning(f"⚠️ Unknown league: {league_name}")
        return [], True, None
    
    if season is None:
        season = get_current_season()
    
    league_info = LEAGUE_MAPPING[normalized_name]
    url = f"https://www.flashscore.com/football/{league_info['country']}/{league_info['slug']}/results/"
    
    TUI.info(f"🏟️ Scraping {normalized_name} ({season})...")
    start_time = time.time()
    
    try:
        with sync_playwright() as p:
            browser, context = get_playwright_context(p, headless=True)
            page = context.new_page()
            
            # Set up resource blocking for faster page loads
            _setup_page_resource_blocking(page)
            
            with LongRequestWarning(threshold_seconds=25.0,
                                   warning_message=f"Loading {normalized_name} page is taking longer than expected..."):
                page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            # Short wait for JS rendering (reduced from 2s)
            time.sleep(0.5)
            
            # Wait for content with targeted selector
            try:
                page.wait_for_selector('div[class*="event__match"]', timeout=10000)
            except:
                # Fallback to generic content wait
                wait_for_content(page)
            
            matches = extract_matches_from_page(page, normalized_name, season, max_workers_odds, market_types)
            
            # Try to fetch league winner odds
            tournament_id = extract_tournament_id_from_page(page)
            league_winner_odds = None
            if tournament_id:
                league_winner_odds = fetch_league_winner_odds(tournament_id)
                if league_winner_odds:
                    TUI.success(f"👑 Found {len(league_winner_odds)} league winner odds for {normalized_name}")
            
            # Close page and browser to free resources immediately
            try:
                page.close()
            except:
                pass
            try:
                context.close()
            except:
                pass
            try:
                browser.close()
            except:
                pass
        
        duration = time.time() - start_time
        TUI.success(f"✅ Completed {normalized_name}: {len(matches)} matches in {duration:.1f}s")
        return matches, False, league_winner_odds
        
    except Exception as e:
        TUI.error(f"❌ Error scraping {normalized_name}: {e}")
        return [], True, None


def main():
    """Main function to scrape Flashscore scores for a single league."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Flashscore Scores Scraper - Single League')
    parser.add_argument('--league', required=True, help='League name to scrape (e.g., "Premier League")')
    parser.add_argument('--season', help='Season to scrape (e.g., 2024-2025). Default: current season')
    parser.add_argument('--headless', action='store_true', default=True, help='Run in headless mode (default: True)')
    parser.add_argument('--max-workers-odds', type=int, default=5,
                       help='Max parallel workers for odds fetching within this league (default: 5)')
    parser.add_argument('--market-types', nargs='+', 
                       help='Filter odds by market types (e.g., HOME_DRAW_AWAY OVER_UNDER BOTH_TEAMS_TO_SCORE). If not specified, all markets are scraped.')
    
    args = parser.parse_args()
    
    season = args.season or get_current_season()
    
    # Scrape the single league (scrape_league will log the start message)
    matches, error, league_winner_odds = scrape_league(
        args.league, 
        season, 
        max_workers_odds=args.max_workers_odds,
        market_types=args.market_types
    )
    
    if error:
        TUI.error(f"❌ Failed to scrape {args.league}")
        print(json.dumps({'matches': [], 'total_matches': 0, 'season': season, 'league': args.league, 'error': True}, ensure_ascii=False))
        sys.exit(1)
    
    output = {
        'matches': matches,
        'total_matches': len(matches),
        'season': season,
        'league': args.league,
        'league_winner_odds': league_winner_odds or []
    }
    
    # Output compact JSON to reduce logging noise
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
