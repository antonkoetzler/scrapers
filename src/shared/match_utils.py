"""Shared utilities for match data parsing and normalization."""
import re
from datetime import datetime
from typing import Optional, Tuple, Dict


def parse_score(score_str: str) -> Optional[Tuple[int, int]]:
    """Parse score string to home and away scores.
    
    Examples: "1–0" -> (1, 0), "2-1" -> (2, 1), "0–0" -> (0, 0)
    
    Args:
        score_str: Score string (e.g., "2-1", "3–0")
    
    Returns:
        Tuple of (home_score, away_score) or None if invalid
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


def get_current_season() -> str:
    """Get current season in YYYY-YYYY format (e.g., '2024-2025').
    
    Returns:
        Season string
    """
    now = datetime.now()
    year = now.year
    month = now.month
    
    # Season typically runs Aug-May, so if we're in Jan-Jul, use previous year
    if month < 8:
        return f"{year-1}-{year}"
    else:
        return f"{year}-{year+1}"


def format_start_time(datetime_obj: datetime) -> str:
    """Format datetime object to ISO 8601 string (YYYY-MM-DDTHH:MM:SSZ).
    
    Args:
        datetime_obj: Datetime object
    
    Returns:
        ISO 8601 formatted string
    """
    return datetime_obj.strftime('%Y-%m-%dT%H:%M:%SZ')


def format_match_date(datetime_obj: datetime) -> str:
    """Format datetime object to YYYY-MM-DD string.
    
    Args:
        datetime_obj: Datetime object
    
    Returns:
        Date string in YYYY-MM-DD format
    """
    return datetime_obj.strftime('%Y-%m-%d')


def parse_datetime_string(dt_str: str, format_str: str = "%Y%m%d%H%M%S") -> Optional[datetime]:
    """Parse datetime string to datetime object.
    
    Args:
        dt_str: Datetime string (e.g., "20260117123000")
        format_str: Format string (default: "%Y%m%d%H%M%S")
    
    Returns:
        Datetime object or None if parsing fails
    """
    try:
        return datetime.strptime(dt_str, format_str)
    except (ValueError, TypeError):
        return None


def is_esports_match(home_team_name: str, away_team_name: str) -> bool:
    """Check if a match is an esports match based on team name patterns.
    
    Esports matches typically have patterns like:
    - <Team name> (Player) v <Team name> (Player)
    - Team names containing "(Player)" or similar patterns
    
    Args:
        home_team_name: Home team name
        away_team_name: Away team name
    
    Returns:
        True if this appears to be an esports match, False otherwise
    """
    if not home_team_name or not away_team_name:
        return False
    
    # Check for (Player) pattern in either team name
    player_pattern = r'\([^)]*[Pp]layer[^)]*\)'
    if re.search(player_pattern, home_team_name) or re.search(player_pattern, away_team_name):
        return True
    
    # Check for other common esports patterns (single name in parentheses)
    # This catches patterns like "Team (Messi)" or "Team (Ronaldo)"
    single_name_pattern = r'\([A-Z][a-z]+\)'
    if re.search(single_name_pattern, home_team_name) or re.search(single_name_pattern, away_team_name):
        return True
    
    return False


def create_match_dict(
    home_team_name: str,
    away_team_name: str,
    home_score: int,
    away_score: int,
    start_time_iso: str,
    status: str,
    match_date_yyyymmdd: str,
    league: str,
    season: str
) -> Dict:
    """Creates a standardized match dictionary.
    
    Args:
        home_team_name: Home team name
        away_team_name: Away team name
        home_score: Home team score
        away_score: Away team score
        start_time_iso: Start time in ISO 8601 format
        status: Match status (e.g., "finished", "FT")
        match_date_yyyymmdd: Match date in YYYY-MM-DD format
        league: League name
        season: Season in YYYY-YYYY format
    
    Returns:
        Match dictionary
    """
    return {
        'home_team_name': home_team_name,
        'away_team_name': away_team_name,
        'home_score': home_score,
        'away_score': away_score,
        'start_time': start_time_iso,
        'status': status,
        'match_date': match_date_yyyymmdd,
        'league': league,
        'season': season
    }
