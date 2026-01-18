"""
Centralized league configuration for all soccer scrapers.

This file defines the leagues/tournaments that should be scraped across all scrapers.
Leagues are organized by priority and category.

IMPORTANT: NO ESPORTS SOCCER - Only real football/soccer leagues.
"""

# Primary leagues (major European and international leagues)
PRIMARY_LEAGUES = {
    # Top 5 European Leagues
    'Premier League': {
        'betano_id': 4,
        'flashscore': {'country': 'england', 'slug': 'premier-league'},
        'livescore': {'country': 'england', 'slug': 'premier-league'},
    },
    'La Liga': {
        'betano_id': 5,
        'flashscore': {'country': 'spain', 'slug': 'laliga'},
        'livescore': {'country': 'spain', 'slug': 'laliga'},
    },
    'Serie A': {
        'betano_id': 3,
        'flashscore': {'country': 'italy', 'slug': 'serie-a'},
        'livescore': {'country': 'italy', 'slug': 'serie-a'},
    },
    'Bundesliga': {
        'betano_id': 8,
        'flashscore': {'country': 'germany', 'slug': 'bundesliga'},
        'livescore': {'country': 'germany', 'slug': 'bundesliga'},
    },
    'Ligue 1': {
        'betano_id': 6,
        'flashscore': {'country': 'france', 'slug': 'ligue-1'},
        'livescore': {'country': 'france', 'slug': 'ligue-1'},
    },
    
    # Major International Competitions
    'Champions League': {
        'betano_id': None,  # Discovered dynamically
        'flashscore': {'country': 'europe', 'slug': 'champions-league'},
        'livescore': {'country': 'europe', 'slug': 'champions-league'},
    },
    'Europa League': {
        'betano_id': None,
        'flashscore': {'country': 'europe', 'slug': 'europa-league'},
        'livescore': {'country': 'europe', 'slug': 'europa-league'},
    },
    'Copa del Rey': {
        'betano_id': None,
        'flashscore': {'country': 'spain', 'slug': 'copa-del-rey'},
        'livescore': {'country': 'spain', 'slug': 'copa-del-rey'},
    },
    'FA Cup': {
        'betano_id': None,
        'flashscore': {'country': 'england', 'slug': 'fa-cup'},
        'livescore': {'country': 'england', 'slug': 'fa-cup'},
    },
    'Coppa Italia': {
        'betano_id': None,
        'flashscore': {'country': 'italy', 'slug': 'coppa-italia'},
        'livescore': {'country': 'italy', 'slug': 'coppa-italia'},
    },
    'DFB-Pokal': {
        'betano_id': None,
        'flashscore': {'country': 'germany', 'slug': 'dfb-pokal'},
        'livescore': {'country': 'germany', 'slug': 'dfb-pokal'},
    },
    'Coupe de France': {
        'betano_id': None,
        'flashscore': {'country': 'france', 'slug': 'coupe-de-france'},
        'livescore': {'country': 'france', 'slug': 'coupe-de-france'},
    },
}

# Secondary leagues (strong domestic leagues)
SECONDARY_LEAGUES = {
    'Championship': {
        'betano_id': None,
        'flashscore': {'country': 'england', 'slug': 'championship'},
        'livescore': {'country': 'england', 'slug': 'championship'},
    },
    'Serie B': {
        'betano_id': None,
        'flashscore': {'country': 'italy', 'slug': 'serie-b'},
        'livescore': {'country': 'italy', 'slug': 'serie-b'},
    },
    'La Liga 2': {
        'betano_id': None,
        'flashscore': {'country': 'spain', 'slug': 'laliga2'},
        'livescore': {'country': 'spain', 'slug': 'segunda-division'},
    },
    '2. Bundesliga': {
        'betano_id': None,
        'flashscore': {'country': 'germany', 'slug': '2-bundesliga'},
        'livescore': {'country': 'germany', 'slug': '2-bundesliga'},
    },
    'Ligue 2': {
        'betano_id': None,
        'flashscore': {'country': 'france', 'slug': 'ligue-2'},
        'livescore': {'country': 'france', 'slug': 'ligue-2'},
    },
    'Eredivisie': {
        'betano_id': 7,
        'flashscore': {'country': 'netherlands', 'slug': 'eredivisie'},
        'livescore': {'country': 'netherlands', 'slug': 'eredivisie'},
    },
    'Primeira Liga': {
        'betano_id': 17083,
        'flashscore': {'country': 'portugal', 'slug': 'primeira-liga'},
        'livescore': {'country': 'portugal', 'slug': 'primeira-liga'},
    },
    'Belgian Pro League': {
        'betano_id': 10,
        'flashscore': {'country': 'belgium', 'slug': 'pro-league'},
        'livescore': {'country': 'belgium', 'slug': 'pro-league'},
    },
    'Turkish Süper Lig': {
        'betano_id': 26,
        'flashscore': {'country': 'turkey', 'slug': 'super-lig'},
        'livescore': {'country': 'turkey', 'slug': 'super-lig'},
    },
    'Austrian Bundesliga': {
        'betano_id': None,
        'flashscore': {'country': 'austria', 'slug': 'bundesliga'},
        'livescore': {'country': 'austria', 'slug': 'bundesliga'},
    },
    'Swiss Super League': {
        'betano_id': None,
        'flashscore': {'country': 'switzerland', 'slug': 'super-league'},
        'livescore': {'country': 'switzerland', 'slug': 'super-league'},
    },
    'Danish Superliga': {
        'betano_id': None,
        'flashscore': {'country': 'denmark', 'slug': 'superliga'},
        'livescore': {'country': 'denmark', 'slug': 'superliga'},
    },
    'Swedish Allsvenskan': {
        'betano_id': None,
        'flashscore': {'country': 'sweden', 'slug': 'allsvenskan'},
        'livescore': {'country': 'sweden', 'slug': 'allsvenskan'},
    },
    'Norwegian Eliteserien': {
        'betano_id': None,
        'flashscore': {'country': 'norway', 'slug': 'eliteserien'},
        'livescore': {'country': 'norway', 'slug': 'eliteserien'},
    },
    'Russian Premier League': {
        'betano_id': None,
        'flashscore': {'country': 'russia', 'slug': 'premier-league'},
        'livescore': {'country': 'russia', 'slug': 'premier-league'},
    },
    'Greek Super League': {
        'betano_id': None,
        'flashscore': {'country': 'greece', 'slug': 'super-league'},
        'livescore': {'country': 'greece', 'slug': 'super-league'},
    },
}

# Regional leagues (smaller leagues with potential for consistent patterns)
REGIONAL_LEAGUES = {
    # Brazilian leagues (strong betting markets)
    'Brasileiro Série A': {
        'betano_id': None,  # Discovered dynamically
        'flashscore': {'country': 'brazil', 'slug': 'brasileirao-betano'},
        'livescore': {'country': 'brazil', 'slug': 'brasileirao'},
    },
    'Brasileiro Série B': {
        'betano_id': None,
        'flashscore': {'country': 'brazil', 'slug': 'serie-b'},
        'livescore': {'country': 'brazil', 'slug': 'serie-b'},
    },
    'Campeonato Paulista': {
        'betano_id': 16901,
        'flashscore': {'country': 'brazil', 'slug': 'paulista'},
        'livescore': {'country': 'brazil', 'slug': 'paulista'},
    },
    'Campeonato Mineiro': {
        'betano_id': 16893,
        'flashscore': {'country': 'brazil', 'slug': 'mineiro'},
        'livescore': {'country': 'brazil', 'slug': 'mineiro'},
    },
    'Campeonato Baiano': {
        'betano_id': 16872,
        'flashscore': {'country': 'brazil', 'slug': 'baiano'},
        'livescore': {'country': 'brazil', 'slug': 'baiano'},
    },
    'Campeonato Catarinense': {
        'betano_id': 16882,
        'flashscore': {'country': 'brazil', 'slug': 'catarinense'},
        'livescore': {'country': 'brazil', 'slug': 'catarinense'},
    },
    
    # South American leagues
    'Argentine Primera División': {
        'betano_id': 14,
        'flashscore': {'country': 'argentina', 'slug': 'primera-division'},
        'livescore': {'country': 'argentina', 'slug': 'primera-division'},
    },
    'Chilean Primera División': {
        'betano_id': None,
        'flashscore': {'country': 'chile', 'slug': 'primera-division'},
        'livescore': {'country': 'chile', 'slug': 'primera-division'},
    },
    'Colombian Categoría Primera A': {
        'betano_id': None,
        'flashscore': {'country': 'colombia', 'slug': 'categoria-primera-a'},
        'livescore': {'country': 'colombia', 'slug': 'categoria-primera-a'},
    },
    'Mexican Liga MX': {
        'betano_id': 16,
        'flashscore': {'country': 'mexico', 'slug': 'liga-mx'},
        'livescore': {'country': 'mexico', 'slug': 'liga-mx'},
    },
    
    # Asian leagues
    'J1 League': {
        'betano_id': None,
        'flashscore': {'country': 'japan', 'slug': 'j1-league'},
        'livescore': {'country': 'japan', 'slug': 'j1-league'},
    },
    'K League 1': {
        'betano_id': None,
        'flashscore': {'country': 'south-korea', 'slug': 'k-league-1'},
        'livescore': {'country': 'south-korea', 'slug': 'k-league-1'},
    },
    'Chinese Super League': {
        'betano_id': None,
        'flashscore': {'country': 'china', 'slug': 'super-league'},
        'livescore': {'country': 'china', 'slug': 'super-league'},
    },
    
    # North American
    'MLS': {
        'betano_id': 17264,
        'flashscore': {'country': 'usa', 'slug': 'mls'},
        'livescore': {'country': 'usa', 'slug': 'mls'},
    },
}

# Combine all leagues
ALL_LEAGUES = {**PRIMARY_LEAGUES, **SECONDARY_LEAGUES, **REGIONAL_LEAGUES}

# Get league names for each scraper
def get_flashscore_leagues() -> dict:
    """Get league mapping for Flashscore scraper."""
    return {
        name: info['flashscore']
        for name, info in ALL_LEAGUES.items()
        if 'flashscore' in info
    }

def get_livescore_leagues() -> dict:
    """Get league mapping for Livescore scraper."""
    return {
        name: info['livescore']
        for name, info in ALL_LEAGUES.items()
        if 'livescore' in info
    }

def get_betano_league_ids() -> list:
    """Get Betano league IDs (only those with known IDs)."""
    return [
        info['betano_id']
        for info in ALL_LEAGUES.values()
        if info.get('betano_id') is not None
    ]
