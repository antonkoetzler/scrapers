"""
Betano API Scraper - Professional grade scraper for football betting data.

Scrapes all FOOT leagues with:
- Fixtures with ALL available markets
- Top scorer bets (when available)
- League winner bets (when available)

Output: League-grouped JSON with comprehensive betting data.
"""
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import cloudscraper

# Add src directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.tui import TUI
from shared.scraper_utils import get_session

# Betano API configuration
BASE_URL = "https://www.betano.bet.br"


class BetanoScraper:
    """Professional Betano scraper for football betting data."""
    
    def __init__(self, delay: float = 1.0):
        """Initialize scraper with cloudscraper session.
        
        Args:
            delay: Delay between requests in seconds (default: 1.0)
        """
        self.session = get_session(
            referer='https://www.betano.bet.br/sport/futebol/ligas/',
            origin='https://www.betano.bet.br',
            accept='application/json, text/plain, */*',
            accept_language='pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            use_proxy=False
        )
        # Add Betano-specific headers
        self.session.headers.update({
            'x-language': '5',
            'x-operator': '8',
        })
        self.delay = delay
        self._request_count = 0
    
    def _request(self, url: str, max_retries: int = 3) -> Optional[Dict]:
        """Make HTTP request with retry logic.
        
        Args:
            url: Full URL to request
            max_retries: Maximum retry attempts
            
        Returns:
            JSON response dict or None on failure
        """
        self._request_count += 1
        
        for attempt in range(max_retries):
            try:
                resp = self.session.get(url, timeout=30)
                
                if resp.status_code == 429:
                    wait = (attempt + 1) * 5
                    TUI.warning(f"Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                    continue
                
                if resp.status_code == 200:
                    try:
                        return resp.json()
                    except:
                        return None
                
                if resp.status_code == 404:
                    return None
                
                TUI.warning(f"HTTP {resp.status_code} for {url[:80]}...")
                
            except Exception as e:
                TUI.warning(f"Request error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        return None
    
    def _request_html(self, url: str) -> Optional[str]:
        """Make HTTP request for HTML content.
        
        Args:
            url: Full URL to request
            
        Returns:
            HTML string or None on failure
        """
        self._request_count += 1
        
        try:
            resp = self.session.get(url, timeout=30)
            if resp.status_code == 200:
                return resp.text
        except Exception as e:
            TUI.warning(f"HTML request error: {e}")
        
        return None
    
    def _rate_limit(self):
        """Apply rate limiting delay."""
        if self.delay > 0:
            time.sleep(self.delay)
    
    # =========================================================================
    # LEAGUE DISCOVERY
    # =========================================================================
    
    def discover_leagues(self) -> List[Dict]:
        """Dynamically discover all FOOT leagues by scraping the leagues page.
        
        Scrapes https://www.betano.bet.br/sport/futebol/ligas/ to find all football leagues.
        Parses embedded JSON data for league IDs and names.
        
        Returns:
            List of dicts with 'id' and 'name' for each football league.
        """
        TUI.info("Discovering FOOT leagues from leagues page...")
        
        html = self._request_html(f"{BASE_URL}/sport/futebol/ligas/")
        
        if not html:
            TUI.error("Failed to fetch leagues page")
            return self._get_fallback_leagues()
        
        leagues = {}  # Use dict to deduplicate by ID
        
        # Primary method: Extract from embedded JSON
        # Pattern: {"id":"17083","name":"Primeira Liga","url":"/sport/futebol/.../17083/"}
        json_pattern = r'\{"id":"(\d+)","name":"([^"]+)","url":"/sport/futebol/[^"]+"\}'
        json_matches = re.findall(json_pattern, html)
        
        for lid, name in json_matches:
            # Clean up name (handle encoding issues)
            name = name.encode('latin-1', errors='ignore').decode('utf-8', errors='ignore')
            leagues[lid] = {'id': int(lid), 'name': name}
        
        if json_matches:
            TUI.info(f"Found {len(leagues)} leagues from embedded JSON")
        
        # Secondary method: Extract league IDs from URLs if JSON parsing missed some
        url_pattern = r'/sport/futebol/[^"\']+/(\d+)/?["\']'
        url_matches = re.findall(url_pattern, html)
        
        for lid in set(url_matches):
            if lid not in leagues:
                leagues[lid] = {'id': int(lid), 'name': f'League {lid}'}
        
        if not leagues:
            TUI.warning("No leagues found from HTML, using fallback")
            return self._get_fallback_leagues()
        
        # Sort by name for consistent ordering
        result = sorted(leagues.values(), key=lambda x: x['name'])
        
        TUI.success(f"Discovered {len(result)} FOOT leagues")
        return result
    
    def _get_fallback_leagues(self) -> List[Dict]:
        """Return major football leagues as fallback.
        
        These are well-known league IDs that are stable.
        """
        TUI.info("Using fallback major leagues")
        return [
            {'id': 5, 'name': 'LaLiga'},
            {'id': 4, 'name': 'Premier League'},
            {'id': 8, 'name': 'Bundesliga'},
            {'id': 3, 'name': 'Serie A'},
            {'id': 6, 'name': 'Ligue 1'},
            {'id': 17083, 'name': 'Primeira Liga'},
            {'id': 16901, 'name': 'Campeonato Paulista'},
            {'id': 16893, 'name': 'Campeonato Mineiro'},
            {'id': 16872, 'name': 'Campeonato Baiano'},
            {'id': 16882, 'name': 'Campeonato Catarinense'},
            {'id': 7, 'name': 'Eredivisie'},
            {'id': 10, 'name': 'Belgian Pro League'},
            {'id': 26, 'name': 'Süper Lig'},
            {'id': 17264, 'name': 'MLS'},
            {'id': 14, 'name': 'Liga Argentina'},
            {'id': 16, 'name': 'Liga MX'},
        ]
    
    # =========================================================================
    # FIXTURE COLLECTION
    # =========================================================================
    
    def fetch_league_fixtures(self, league_id: int) -> List[Dict]:
        """Fetch upcoming fixtures for a league.
        
        Args:
            league_id: Betano league ID
            
        Returns:
            List of fixture dicts with basic info
        """
        url = f"{BASE_URL}/api/league/hot/upcoming?leagueId={league_id}&req=s,stnf,c,mb"
        data = self._request(url)
        
        if not data:
            return []
        
        events = data.get('data', {}).get('events', [])
        fixtures = []
        
        for event in events:
            participants = event.get('participants', [])
            if len(participants) < 2:
                continue
            
            fixture = {
                'fixture_id': str(event.get('id')),
                'home_team_id': str(participants[0].get('id')),
                'home_team_name': participants[0].get('name'),
                'away_team_id': str(participants[1].get('id')),
                'away_team_name': participants[1].get('name'),
                'start_time': self._convert_timestamp(event.get('startTime', 0)),
                'status': 'scheduled',
                'url': event.get('url', ''),
            }
            fixtures.append(fixture)
        
        return fixtures
    
    def fetch_fixture_markets(self, fixture_id: str) -> List[Dict]:
        """Fetch ALL markets/odds for a specific fixture.
        
        Uses /api/event/markets/{fixture_id}?tab=all to get all available markets.
        
        Args:
            fixture_id: Betano fixture/event ID
            
        Returns:
            List of odds dicts
        """
        url = f"{BASE_URL}/api/event/markets/{fixture_id}?tab=all"
        data = self._request(url)
        
        if not data:
            return []
        
        event_data = data.get('data', {}).get('event', {})
        markets = event_data.get('markets', [])
        
        odds_list = []
        
        for market in markets:
            market_type = market.get('type', '')
            market_name = market.get('name', '')
            market_id = market.get('id', '')
            handicap = market.get('handicap', 0.0)
            
            for selection in market.get('selections', []):
                odds_list.append({
                    'fixture_id': fixture_id,
                    'market_id': market_id,
                    'market_name': market_name,
                    'market_type': market_type,
                    'handicap': handicap if handicap else None,
                    'outcome_id': selection.get('id', ''),
                    'outcome_name': selection.get('name', ''),
                    'outcome_full_name': selection.get('fullName', selection.get('name', '')),
                    'odds_value': float(selection.get('price', 0)),
                    'bookmaker': 'betano',
                })
        
        return odds_list
    
    # =========================================================================
    # TOP SCORER COLLECTION
    # =========================================================================
    
    def fetch_top_scorer(self, league_id: int) -> List[Dict]:
        """Fetch top scorer betting odds for a league.
        
        Args:
            league_id: Betano league ID
            
        Returns:
            List of top scorer bet dicts
        """
        url = f"{BASE_URL}/api/league/topPlayers?sportId=1&leagueId={league_id}&gLeagueIds={league_id}&stats=1&displayHeaders=true"
        data = self._request(url)
        
        if not data:
            return []
        
        # Check for errors
        if 'errors' in data or 'errorCode' in data:
            return []
        
        table_layout = data.get('data', {}).get('tableLayout', [])
        if not table_layout:
            return []
        
        top_scorers = []
        
        for section in table_layout:
            section_title = section.get('title', '')
            
            # Focus on top scorer sections
            title_lower = section_title.lower()
            if not any(kw in title_lower for kw in ['marcador', 'scorer', 'artilheiro', 'goleador']):
                continue
            
            for row in section.get('rows', []):
                player_name = row.get('title', '')
                team_name = row.get('subtitle', '')
                player_id = row.get('rowId', '')
                
                for selection in row.get('selections', []):
                    price = selection.get('price')
                    if price:
                        top_scorers.append({
                            'player_id': player_id,
                            'player_name': player_name,
                            'team_name': team_name,
                            'league_id': league_id,
                            'market_type': 'top_scorer',
                            'market_name': section_title,
                            'selection_id': selection.get('id', ''),
                            'odds_value': float(price),
                            'bookmaker': 'betano',
                        })
        
        return top_scorers
    
    # =========================================================================
    # LEAGUE WINNER COLLECTION
    # =========================================================================
    
    def fetch_league_winner(self, league_id: int) -> List[Dict]:
        """Fetch league winner betting odds.
        
        Args:
            league_id: Betano league ID
            
        Returns:
            List of league winner bet dicts
        """
        # Try without phaseId first
        url = f"{BASE_URL}/api/league/phaseStandings?sportId=1&leagueId={league_id}&gLeagueIds={league_id}&req=s,stnf,c,mb"
        data = self._request(url)
        
        if not data:
            return []
        
        # Check for errors
        if 'errors' in data or 'errorCode' in data:
            return []
        
        # Try to extract league winner selections from various structures
        winners = []
        
        # Try standings structure
        standings = data.get('data', {}).get('standings', [])
        if not standings:
            standings = data.get('standings', [])
        
        for standing in standings:
            selections = standing.get('selections', [])
            for selection in selections:
                price = selection.get('price')
                if price:
                    winners.append({
                        'team_id': str(standing.get('teamId', '')),
                        'team_name': standing.get('teamName', ''),
                        'league_id': league_id,
                        'market_type': 'league_winner',
                        'selection_id': selection.get('id', ''),
                        'odds_value': float(price),
                        'bookmaker': 'betano',
                    })
        
        # Try markets structure (some responses have markets directly)
        markets = data.get('data', {}).get('markets', [])
        for market in markets:
            market_type = market.get('type', '').lower()
            if 'winner' in market_type or 'campeao' in market.get('name', '').lower():
                for selection in market.get('selections', []):
                    price = selection.get('price')
                    if price:
                        winners.append({
                            'team_id': selection.get('id', ''),
                            'team_name': selection.get('name', ''),
                            'league_id': league_id,
                            'market_type': 'league_winner',
                            'selection_id': selection.get('id', ''),
                            'odds_value': float(price),
                            'bookmaker': 'betano',
                        })
        
        return winners
    
    # =========================================================================
    # MAIN SCRAPING LOGIC
    # =========================================================================
    
    def scrape_all(self, max_leagues: int = None, league_ids: List[int] = None) -> List[Dict]:
        """Scrape all leagues with fixtures, markets, top scorer, and league winner.
        
        Args:
            max_leagues: Optional limit on number of leagues to scrape
            league_ids: Optional specific league IDs to scrape
            
        Returns:
            List of league dicts with all data
        """
        if league_ids:
            leagues = [{'id': lid, 'name': f'League {lid}'} for lid in league_ids]
        else:
            leagues = self.discover_leagues()
        
        if not leagues:
            TUI.error("No leagues available, cannot proceed")
            return []
        
        if max_leagues:
            leagues = leagues[:max_leagues]
        
        TUI.info(f"Scraping {len(leagues)} leagues...")
        results = []
        
        for i, league in enumerate(leagues, 1):
            league_id = league['id']
            league_name = league['name']
            
            TUI.info(f"[{i}/{len(leagues)}] {league_name} (ID: {league_id})")
            
            league_result = {
                'league_id': league_id,
                'league_name': league_name,
            }
            
            # Fetch fixtures
            fixtures = self.fetch_league_fixtures(league_id)
            self._rate_limit()
            
            if fixtures:
                TUI.info(f"  Fixtures: {len(fixtures)}")
                
                # Fetch all markets for each fixture
                for fixture in fixtures:
                    fixture_id = fixture['fixture_id']
                    odds = self.fetch_fixture_markets(fixture_id)
                    fixture['odds'] = odds
                    home = fixture['home_team_name'][:20]
                    away = fixture['away_team_name'][:20]
                    TUI.info(f"    {home} vs {away}: {len(odds)} odds")
                    self._rate_limit()
                
                league_result['fixtures'] = fixtures
            else:
                TUI.info(f"  No fixtures")
            
            # Fetch top scorer
            top_scorer = self.fetch_top_scorer(league_id)
            self._rate_limit()
            
            if top_scorer:
                TUI.success(f"  Top scorer: {len(top_scorer)} selections")
                league_result['topScorer'] = top_scorer
            
            # Fetch league winner
            league_winner = self.fetch_league_winner(league_id)
            self._rate_limit()
            
            if league_winner:
                TUI.success(f"  League winner: {len(league_winner)} selections")
                league_result['leagueWinner'] = league_winner
            
            results.append(league_result)
        
        return results
    
    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    @staticmethod
    def _convert_timestamp(timestamp_ms: int) -> str:
        """Convert milliseconds timestamp to ISO datetime string."""
        if not timestamp_ms:
            return ""
        return datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%dT%H:%M:%SZ')


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Betano Scraper - Professional football betting data scraper'
    )
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between requests in seconds (default: 1.0)')
    parser.add_argument('--max-leagues', type=int, default=None,
                       help='Maximum number of leagues to scrape (default: all)')
    parser.add_argument('--league-ids', type=int, nargs='+',
                       help='Specific league IDs to scrape')
    parser.add_argument('--output', type=str, default=None,
                       help='Output file path (default: stdout)')
    parser.add_argument('--pretty', action='store_true',
                       help='Pretty print JSON output')
    
    args = parser.parse_args()
    
    TUI.header("=" * 60)
    TUI.header("BETANO SCRAPER")
    TUI.header("=" * 60)
    
    scraper = BetanoScraper(delay=args.delay)
    
    try:
        results = scraper.scrape_all(
            max_leagues=args.max_leagues,
            league_ids=args.league_ids
        )
        
        # Summary
        total_fixtures = sum(len(l.get('fixtures', [])) for l in results)
        total_odds = sum(
            sum(len(f.get('odds', [])) for f in l.get('fixtures', []))
            for l in results
        )
        total_top_scorer = sum(len(l.get('topScorer', [])) for l in results)
        total_league_winner = sum(len(l.get('leagueWinner', [])) for l in results)
        
        TUI.header("=" * 60)
        TUI.header("SUMMARY")
        TUI.header("=" * 60)
        TUI.info(f"Leagues: {len(results)}")
        TUI.info(f"Fixtures: {total_fixtures}")
        TUI.info(f"Total odds: {total_odds}")
        TUI.info(f"Top scorer selections: {total_top_scorer}")
        TUI.info(f"League winner selections: {total_league_winner}")
        TUI.info(f"Requests made: {scraper._request_count}")
        
        # Output
        indent = 2 if args.pretty else None
        output_json = json.dumps(results, indent=indent, ensure_ascii=False)
        
        if args.output:
            Path(args.output).write_text(output_json, encoding='utf-8')
            TUI.success(f"Output written to {args.output}")
        else:
            print(output_json)
        
    except KeyboardInterrupt:
        TUI.warning("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        TUI.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
