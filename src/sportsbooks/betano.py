"""Betano API scraper with anti-scraping measures."""
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add src directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.tui import TUI
from shared.scraper_utils import get_session, init_proxy_manager


def fetch_betano_data(url: str, max_retries: int = 3) -> dict:
    """Fetch data from Betano API with retry logic and proxy fallback."""
    from shared.request_with_fallback import request_with_fallback
    
    try:
        TUI.info(f"Fetching data...")
        response = request_with_fallback('get', url, max_retries=max_retries, use_proxy=True)
        TUI.success(f"Successfully fetched data (Status: {response.status_code})")
        return response.json()
    except Exception as e:
        TUI.error(f"Request failed: {e}")
        raise


def convert_timestamp_to_iso(timestamp_ms: int) -> str:
    """Convert milliseconds timestamp to ISO datetime string."""
    return datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%dT%H:%M:%SZ')


def transform_fixture(event: Dict) -> Dict:
    """Transform event to fixture format."""
    participants = event.get("participants", [])
    if len(participants) < 2:
        return None
    
    return {
        'fixture_id': event.get('id'),
        'home_team_id': participants[0].get('id'),
        'home_team_name': participants[0].get('name'),
        'away_team_id': participants[1].get('id'),
        'away_team_name': participants[1].get('name'),
        'start_time': convert_timestamp_to_iso(event.get('startTime', 0)),
        'status': 'scheduled'  # This endpoint doesn't provide status, defaulting to scheduled
    }


def transform_odds(event: Dict) -> List[Dict]:
    """Transform markets to odds format."""
    fixture_id = event.get('id')
    odds_list = []
    
    for market in event.get('markets', []):
        market_type = market.get('type')
        market_name = market.get('name')
        handicap = market.get('handicap', 0.0)
        
        # Map market types to required format
        if market_type == 'MRES':  # 1x2 market
            market_id = '1x2'
            market_display_name = '1X2'
        elif market_type == 'HCTG' and handicap == 2.5:  # Over/Under 2.5
            market_id = 'over_under'
            market_display_name = 'Over/Under'
        elif market_type == 'BTSC':  # Both Teams To Score
            market_id = 'btts'
            market_display_name = 'Both Teams To Score'
        else:
            continue  # Skip markets we don't need
        
        # Process selections
        for selection in market.get('selections', []):
            outcome_name = selection.get('name', '').strip()
            price = selection.get('price')
            
            if not price:
                continue
            
            # Map outcome names to standard format
            if market_id == '1x2':
                if outcome_name == '1':
                    outcome_id = '1'
                    outcome_display = 'Home'
                elif outcome_name == 'X':
                    outcome_id = 'X'
                    outcome_display = 'Draw'
                elif outcome_name == '2':
                    outcome_id = '2'
                    outcome_display = 'Away'
                else:
                    continue
            elif market_id == 'over_under':
                if 'Mais de' in outcome_name or 'Over' in outcome_name:
                    outcome_id = 'over_2.5'
                    outcome_display = 'Over 2.5'
                elif 'Menos de' in outcome_name or 'Under' in outcome_name:
                    outcome_id = 'under_2.5'
                    outcome_display = 'Under 2.5'
                else:
                    continue
            elif market_id == 'btts':
                if outcome_name.lower() in ['sim', 'yes']:
                    outcome_id = 'yes'
                    outcome_display = 'Yes'
                elif outcome_name.lower() in ['não', 'nao', 'no']:
                    outcome_id = 'no'
                    outcome_display = 'No'
                else:
                    continue
            else:
                continue
            
            odds_list.append({
                'fixture_id': fixture_id,
                'bookmaker_id': 'betano',
                'bookmaker_name': 'Betano',
                'market_id': market_id,
                'market_name': market_display_name,
                'outcome_id': outcome_id,
                'outcome_name': outcome_display,
                'odds_value': float(price)
            })
    
    return odds_list


def transform_data(events: List[Dict]) -> Dict:
    """Transform raw events to required format."""
    fixtures = []
    all_odds = []
    
    for event in events:
        fixture = transform_fixture(event)
        if fixture:
            fixtures.append(fixture)
        
        odds = transform_odds(event)
        all_odds.extend(odds)
    
    return {
        'fixtures': fixtures,
        'odds': all_odds
    }


def main():
    """Main function to scrape Betano API."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Betano API Scraper')
    parser.add_argument('--no-proxy', action='store_true', help='Disable proxy usage')
    parser.add_argument('--refresh-proxies', action='store_true', default=True, 
                       help='Auto-refresh proxies if < 5 working (default: True)')
    parser.add_argument('--no-refresh-proxies', dest='refresh_proxies', action='store_false',
                       help='Disable auto-refresh of proxies')
    args = parser.parse_args()
    
    # Initialize proxy manager
    init_proxy_manager(no_proxy=args.no_proxy, refresh_proxies=args.refresh_proxies)
    
    url = "https://www.betano.bet.br/api/sports/FOOT/hot/trending/leagues/1/events"
    # url = "https://www.betano.bet.br/api/sports/FOOT/hot/trending/leagues/1/events?req=s,stnf,c,mb"
    
    TUI.header("Betano API Scraper")
    TUI.info(f"Target URL: {url}")
    
    try:
        data = fetch_betano_data(url)
        
        TUI.success("Data retrieved successfully!")
        
        events = data.get("data", {}).get("events", [])
        transformed_data = transform_data(events)
        
        # Output JSON to stdout
        print(json.dumps(transformed_data, indent=2, ensure_ascii=False))
        
    except Exception as e:
        TUI.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

