"""API Route Discovery Tool - Finds available endpoints by testing common paths."""
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Set
from urllib.parse import urljoin

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.tui import TUI
from shared.scraper_utils import get_session, init_proxy_manager

# Common API route patterns (fallback if no wordlist provided)
DEFAULT_WORDLIST = [
    # Common API patterns
    'hot', 'trending', 'popular', 'featured',
    'events', 'matches', 'fixtures', 'games',
    'leagues', 'tournaments', 'competitions',
    'scores', 'results', 'live', 'upcoming', 'finished', 'completed',
    'teams', 'players', 'standings', 'stats', 'statistics',
    'odds', 'markets', 'bets',
    'today', 'tomorrow', 'week', 'month',
    # Betano specific patterns (based on what we know)
    'hot/trending', 'hot/trending/leagues',
    'hot/trending/leagues/1', 'hot/trending/leagues/1/events',
    # REST patterns
    'list', 'all', 'search', 'find', 'get',
    # Status patterns
    'scheduled', 'live', 'finished', 'cancelled', 'postponed',
    # Numeric patterns (league IDs, etc.)
    '1', '2', '3', '5', '10', '100', '1635', '10483', '16880', '16901', '17082',
    '1/events', '1/matches', '5/events', '1635/events',
    # Date patterns
    '2024', '2025', '2026',
    # Common suffixes
    '/events', '/matches', '/fixtures', '/scores', '/odds',
]

def discover_routes(base_url: str, wordlist: List[str] = None, delay: float = 0.5) -> List[Dict]:
    """Discover available routes by testing wordlist against base URL."""
    if wordlist is None:
        wordlist = DEFAULT_WORDLIST
    
    # Ensure base URL ends with /
    if not base_url.endswith('/'):
        base_url += '/'
    
    from shared.request_with_fallback import request_with_fallback
    results = []
    valid_routes = []
    
    TUI.header(f"Route Discovery: {base_url}")
    TUI.info(f"Testing {len(wordlist)} routes...\n")
    
    for i, route in enumerate(wordlist, 1):
        # Clean route (remove leading/trailing slashes)
        route = route.strip('/')
        test_url = urljoin(base_url, route)
        
        TUI.info(f"[{i}/{len(wordlist)}] Testing: {route}")
        
        # Use request_with_fallback for automatic proxy fallback
        try:
            response = request_with_fallback('get', test_url, max_retries=1, use_proxy=True, timeout=10, allow_redirects=False)
            result = {
                'url': test_url,
                'status': response.status_code,
                'is_json': response.headers.get('Content-Type', '').startswith('application/json'),
                'content_length': len(response.content),
                'has_data': False,
                'valid': False
            }
            
            # Check if it's a valid API response
            if result['is_json']:
                try:
                    data = response.json()
                    result['content_length'] = len(str(data))
                    if isinstance(data, dict):
                        result['has_data'] = bool(data.get('data') or data.get('events') or data.get('fixtures') or 
                                                  data.get('leagues') or data.get('matches') or len(data) > 0)
                    elif isinstance(data, list):
                        result['has_data'] = len(data) > 0
                except:
                    pass
            
            result['valid'] = result['status'] == 200 and result['is_json'] and result['has_data']
        except Exception as e:
            result = {
                'url': test_url,
                'status': 0,
                'error': str(e),
                'valid': False
            }
        
        results.append(result)
        
        if result['valid']:
            TUI.success(f"  ✓ Found valid route: {test_url} (Status: {result['status']}, Size: {result['content_length']} bytes)")
            valid_routes.append(result)
        elif result['status'] == 200:
            TUI.warning(f"  ⚠ Route exists but may not be JSON API: {test_url}")
        elif result['status'] in [301, 302, 307, 308]:
            TUI.info(f"  → Redirect: {test_url} (Status: {result['status']})")
        elif result['status'] == 404:
            pass  # Don't show 404s
        else:
            TUI.error(f"  ✗ Error: {test_url} (Status: {result['status']})")
        
        # Rate limiting
        if i < len(wordlist):
            time.sleep(delay)
    
    return valid_routes, results

def recursive_discover(base_url: str, depth: int = 2, wordlist: List[str] = None, delay: float = 0.3) -> Set[str]:
    """Recursively discover routes up to a certain depth."""
    if wordlist is None:
        wordlist = DEFAULT_WORDLIST
    
    discovered = set()
    to_explore = [(base_url, 0)]
    
    from shared.request_with_fallback import request_with_fallback
    
    while to_explore:
        current_url, current_depth = to_explore.pop(0)
        
        if current_depth >= depth:
            continue
        
        TUI.header(f"\nExploring depth {current_depth + 1}: {current_url}")
        
        for route in wordlist:
            route = route.strip('/')
            test_url = urljoin(current_url if current_url.endswith('/') else current_url + '/', route)
            
            if test_url in discovered:
                continue
            
            try:
                response = request_with_fallback('get', test_url, max_retries=1, use_proxy=True, timeout=10, allow_redirects=False)
                is_json = response.headers.get('Content-Type', '').startswith('application/json')
                has_data = False
                
                if is_json:
                    try:
                        data = response.json()
                        if isinstance(data, dict):
                            has_data = bool(data.get('data') or data.get('events') or data.get('fixtures') or 
                                          data.get('leagues') or data.get('matches') or len(data) > 0)
                        elif isinstance(data, list):
                            has_data = len(data) > 0
                    except:
                        pass
                
                is_valid = response.status_code == 200 and is_json and has_data
            except Exception as e:
                is_valid = False
                response = None
            
            if is_valid:
                TUI.success(f"  ✓ {test_url}")
                discovered.add(test_url)
                # Add to exploration queue if not at max depth
                if current_depth + 1 < depth:
                    to_explore.append((test_url, current_depth + 1))
            elif response and response.status_code == 200:
                TUI.warning(f"  ⚠ {test_url} (not JSON API)")
            
            time.sleep(delay)
    
    return discovered

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Discover API routes')
    parser.add_argument('url', help='Base URL to test')
    parser.add_argument('--wordlist', help='Custom wordlist file (one word per line)')
    parser.add_argument('--recursive', '-r', action='store_true', help='Recursively discover routes')
    parser.add_argument('--depth', type=int, default=2, help='Max depth for recursive discovery')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between requests (seconds)')
    parser.add_argument('--no-proxy', action='store_true', help='Disable proxy usage')
    
    args = parser.parse_args()
    
    # Initialize proxy manager
    init_proxy_manager(no_proxy=args.no_proxy)
    
    wordlist = DEFAULT_WORDLIST
    if args.wordlist:
        try:
            with open(args.wordlist, 'r', encoding='utf-8') as f:
                wordlist = [line.strip() for line in f if line.strip()]
            TUI.info(f"Loaded {len(wordlist)} words from {args.wordlist}")
        except Exception as e:
            TUI.error(f"Failed to load wordlist: {e}")
            return
    
    if args.recursive:
        discovered = recursive_discover(args.url, args.depth, wordlist, args.delay)
        TUI.header("\n" + "="*60)
        TUI.header("Discovered Routes (Recursive)")
        TUI.header("="*60)
        for route in sorted(discovered):
            TUI.success(route)
    else:
        valid_routes, all_results = discover_routes(args.url, wordlist, args.delay)
        
        TUI.header("\n" + "="*60)
        TUI.header("Summary")
        TUI.header("="*60)
        TUI.info(f"Total routes tested: {len(all_results)}")
        TUI.success(f"Valid API routes found: {len(valid_routes)}")
        
        if valid_routes:
            TUI.header("\nValid Routes:")
            for route in valid_routes:
                TUI.success(f"  {route['url']} (Status: {route['status']}, Size: {route['content_length']} bytes)")

if __name__ == "__main__":
    main()

