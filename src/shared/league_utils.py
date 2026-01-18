"""Shared utilities for league name normalization and matching."""
import sys
from typing import Optional


def normalize_league_name(league_name: str, league_mapping: dict) -> Optional[str]:
    """Normalize league name to handle encoding issues and find correct key.
    
    This function handles:
    - Double-encoding issues (common with command-line args on Windows)
    - Case-insensitive matching
    - Fuzzy matching for partial names
    
    Args:
        league_name: Input league name (may have encoding issues)
        league_mapping: Dictionary of league names to league info
    
    Returns:
        Correct league name key from mapping, or None if not found
    """
    # Try exact match first
    if league_name in league_mapping:
        return league_name
    
    # Fix double-encoding issues (common with command-line args)
    # This happens when UTF-8 is interpreted as Latin-1
    try:
        if 'Ã©' in league_name or 'ã©' in league_name or 'Ã­' in league_name:
            # Try to decode double-encoded UTF-8
            # Method 1: Encode as latin-1, decode as utf-8
            try:
                fixed = league_name.encode('latin-1', errors='ignore').decode('utf-8', errors='ignore')
                if fixed in league_mapping:
                    return fixed
            except:
                pass
            
            # Method 2: Direct replacement for common cases
            fixed = league_name.replace('Ã©', 'é').replace('ã©', 'é').replace('Ã­', 'í')
            if fixed in league_mapping:
                return fixed
    except:
        pass
    
    # Try case-insensitive exact match
    league_lower = league_name.lower()
    for key in league_mapping.keys():
        if key.lower() == league_lower:
            return key
    
    # Try fuzzy matching for partial names
    # Common patterns: "Brasileiro Serie A" -> "Brasileiro Série A"
    league_lower_clean = league_lower.replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('á', 'a').replace('ú', 'u')
    
    for key in league_mapping.keys():
        key_lower = key.lower()
        key_lower_clean = key_lower.replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('á', 'a').replace('ú', 'u')
        
        # Exact match after removing accents
        if key_lower_clean == league_lower_clean:
            return key
        
        # Partial match for Brazilian leagues
        if 'brasil' in league_lower_clean and 'brasil' in key_lower_clean:
            if ('serie a' in league_lower_clean or 'serie a' in key_lower_clean) and 'serie a' in key_lower_clean:
                return key
            elif ('serie b' in league_lower_clean or 'serie b' in key_lower_clean) and 'serie b' in key_lower_clean:
                return key
    
    return None
