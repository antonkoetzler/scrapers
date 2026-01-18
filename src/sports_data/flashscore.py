"""Flashscore scraper for match scores and results."""
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

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


def extract_matches_from_html(soup: BeautifulSoup, league_name: str, season: str) -> List[Dict]:
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
            
        except Exception as e:
            TUI.warning(f"Error extracting match: {e}")
            continue
    
    return matches


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
    matches = extract_matches_from_html(soup, league_name, season)
    
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
        
        page.close()
        
        TUI.success(f"Found {len(matches)} completed matches in {normalized_name}")
        return matches, False
        
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
            
            matches, _ = scrape_league(normalized_name, season, context)
            all_matches.extend(matches)
            
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
