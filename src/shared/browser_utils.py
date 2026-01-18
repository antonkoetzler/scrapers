"""Shared browser utilities for Playwright and requests-based scraping."""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from shared.tui import TUI


def find_brave_browser() -> Optional[str]:
    """Find Brave browser executable path.
    
    Returns:
        Path to brave.exe or None if not found
    """
    brave_paths = [
        os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"),
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
    ]
    
    for path in brave_paths:
        if os.path.exists(path):
            return path
    
    return None


def get_playwright_context(playwright, headless: bool = False, proxy: Optional[Dict] = None):
    """Create a Playwright browser context with stealth settings.
    
    Args:
        playwright: Playwright instance
        headless: Whether to run in headless mode
        proxy: Optional proxy configuration
    
    Returns:
        Browser context
    """
    brave_exe = find_brave_browser()
    
    if not brave_exe:
        TUI.warning("Brave browser not found, using default Chromium")
        browser = playwright.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
    else:
        browser = playwright.chromium.launch(
            executable_path=brave_exe,
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
    
    context_options = {
        'viewport': {'width': 1920, 'height': 1080},
        'locale': 'en-US',
    }
    
    if proxy:
        context_options['proxy'] = proxy
    
    context = browser.new_context(**context_options)
    
    # Stealth: Remove webdriver flag
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    """)
    
    return browser, context


def extract_from_next_data(html: str) -> Optional[Dict]:
    """Extract __NEXT_DATA__ from HTML (for Next.js sites like Livescore).
    
    Args:
        html: HTML content
    
    Returns:
        Parsed JSON data or None
    """
    import json
    import re
    
    # Look for __NEXT_DATA__ script tag
    pattern = r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>'
    match = re.search(pattern, html, re.DOTALL)
    
    if match:
        try:
            data = json.loads(match.group(1))
            return data
        except:
            pass
    
    return None


def wait_for_content(page, timeout: int = 30000):
    """Wait for page content to load (with fallback).
    
    Args:
        page: Playwright page object
        timeout: Timeout in milliseconds
    """
    try:
        page.wait_for_load_state('networkidle', timeout=timeout)
    except:
        try:
            page.wait_for_load_state('domcontentloaded', timeout=timeout)
        except:
            pass  # Continue anyway


def normalize_match_data(match: Dict, league_name: str, season: str) -> Optional[Dict]:
    """Normalize match data to standard format.
    
    Args:
        match: Raw match data dict
        league_name: League name
        season: Season string (YYYY-YYYY)
    
    Returns:
        Normalized match dict or None if invalid
    """
    from datetime import datetime
    import re
    
    # Extract required fields (flexible field names)
    home_team = match.get('homeTeam') or match.get('home_team') or match.get('home')
    away_team = match.get('awayTeam') or match.get('away_team') or match.get('away')
    home_score = match.get('homeScore') or match.get('home_score') or match.get('score', {}).get('home')
    away_score = match.get('awayScore') or match.get('away_score') or match.get('score', {}).get('away')
    
    # Parse score if it's a string
    if isinstance(home_score, str) or isinstance(away_score, str):
        score_str = f"{home_score}-{away_score}"
        from shared.match_utils import parse_score
        score_result = parse_score(score_str)
        if score_result:
            home_score, away_score = score_result
        else:
            return None
    
    # Convert to int
    try:
        home_score = int(home_score) if home_score is not None else None
        away_score = int(away_score) if away_score is not None else None
    except (ValueError, TypeError):
        return None
    
    # Skip if no score (match not finished)
    if home_score is None or away_score is None:
        return None
    
    # Extract date/time
    start_time = match.get('startTime') or match.get('start_time') or match.get('date') or match.get('time')
    
    # Parse date (handle various formats)
    match_date = None
    if isinstance(start_time, (int, float)):
        # Unix timestamp
        match_date = datetime.fromtimestamp(start_time / 1000 if start_time > 1e10 else start_time)
    elif isinstance(start_time, str):
        # Try various date formats
        date_formats = [
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%d/%m/%Y %H:%M',
            '%d/%m/%Y',
        ]
        for fmt in date_formats:
            try:
                match_date = datetime.strptime(start_time, fmt)
                break
            except:
                continue
    
    if not match_date:
        return None
    
    return {
        'home_team_name': str(home_team).strip(),
        'away_team_name': str(away_team).strip(),
        'home_score': home_score,
        'away_score': away_score,
        'start_time': match_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'status': 'finished',
        'match_date': match_date.strftime('%Y-%m-%d'),
        'league': league_name,
        'season': season
    }
