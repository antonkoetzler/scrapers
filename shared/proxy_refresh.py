"""Shared proxy refresh functionality."""
import json
import time
from pathlib import Path
from typing import Dict, List, Set, Optional

import requests

from shared.tui import TUI


# Target URL for testing proxies (FBref homepage - lightweight)
FBREF_TEST_URL = "https://fbref.com/en/"


def get_proxy_key(proxy: Dict) -> str:
    """Extract proxy key (ip:port) from proxy dict."""
    url = proxy.get('http', proxy.get('https', ''))
    # Extract ip:port from http://ip:port
    if url.startswith('http://'):
        return url[7:]
    elif url.startswith('https://'):
        return url[8:]
    return url


def _fetch_from_proxyscrape() -> List[str]:
    """Fetch proxies from proxyscrape.com API (v3)."""
    try:
        response = requests.get(
            'https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&timeout=10000&proxy_format=ipport&format=text',
            timeout=10
        )
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            # Format is ip:port, filter valid ones
            proxies = []
            for line in lines:
                line = line.strip()
                if ':' in line and not line.startswith('http'):
                    proxies.append(line)
                elif line.startswith('http://'):
                    # Extract ip:port from http://ip:port
                    proxies.append(line[7:])
            return proxies[:30]
    except Exception:
        pass
    return []


def _fetch_from_geonode() -> List[str]:
    """Fetch proxies from geonode.com API."""
    try:
        response = requests.get(
            'https://proxylist.geonode.com/api/proxy-list?limit=30&page=1&sort_by=lastChecked&sort_type=desc&protocols=http',
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            proxies = []
            for item in data.get('data', []):
                ip = item.get('ip')
                port = item.get('port')
                if ip and port:
                    proxies.append(f"{ip}:{port}")
            return proxies[:30]
    except Exception:
        pass
    return []


def _fetch_from_free_proxy_list() -> List[str]:
    """Fetch proxies from free-proxy-list.net (via sslproxies)."""
    try:
        response = requests.get(
            'https://www.sslproxies.org/',
            timeout=10,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        if response.status_code == 200:
            # Parse HTML table
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', class_='table')
            if table:
                proxies = []
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows[:30]:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        ip = cells[0].get_text(strip=True)
                        port = cells[1].get_text(strip=True)
                        if ip and port:
                            proxies.append(f"{ip}:{port}")
                return proxies
    except Exception:
        pass
    return []


def _fetch_from_thespeedx() -> List[str]:
    """Fetch proxies from TheSpeedX GitHub list (fallback)."""
    try:
        response = requests.get(
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
            timeout=10
        )
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            return [line.strip() for line in lines if ':' in line.strip()][:30]
    except Exception:
        pass
    return []


def fetch_free_proxies(blacklist: Set[str] = None, min_needed: int = 5) -> List[Dict]:
    """
    Fetch free proxies from multiple providers sequentially.
    Stops when enough working proxies are found.
    
    Args:
        blacklist: Set of proxy keys to skip
        min_needed: Stop fetching when this many proxies are found
    
    Returns:
        List of proxy dicts
    """
    blacklist = blacklist or set()
    proxies = []
    
    # Provider priority order
    providers = [
        ("proxyscrape.com", _fetch_from_proxyscrape),
        ("geonode.com", _fetch_from_geonode),
        ("sslproxies.org", _fetch_from_free_proxy_list),
        ("TheSpeedX GitHub", _fetch_from_thespeedx),
    ]
    
    for provider_name, fetch_func in providers:
        TUI.info(f"Fetching from {provider_name}...")
        try:
            raw_proxies = fetch_func()
            
            if not raw_proxies:
                TUI.warning(f"No proxies from {provider_name}")
                continue
            
            TUI.info(f"Got {len(raw_proxies)} proxies from {provider_name}")
            
            # Filter out blacklisted and convert to dict format
            for proxy_str in raw_proxies:
                if proxy_str in blacklist:
                    continue
                    
                parts = proxy_str.split(':')
                if len(parts) != 2:
                    continue
                    
                host, port = parts
                proxy_dict = {
                    'http': f'http://{host}:{port}',
                    'https': f'http://{host}:{port}'
                }
                proxies.append(proxy_dict)
            
            # Health check proxies from this provider
            working = []
            for i, proxy in enumerate(proxies, 1):
                TUI.info(f"Testing proxy {i}/{len(proxies)} from {provider_name}...")
                if health_check_proxy(proxy, target_url=FBREF_TEST_URL):
                    working.append(proxy)
                    TUI.success(f"Proxy {i} working")
                    if len(working) >= min_needed:
                        TUI.success(f"Found {len(working)} working proxies, stopping")
                        return working
                else:
                    TUI.warning(f"Proxy {i} failed")
                time.sleep(0.5)
            
            if working:
                proxies = working
                TUI.info(f"Found {len(working)} working proxies from {provider_name}")
                if len(working) >= min_needed:
                    return working
            else:
                proxies = []  # Reset for next provider
                
        except Exception as e:
            TUI.warning(f"Error fetching from {provider_name}: {e}")
            continue
    
    return proxies


def health_check_proxy(proxy: Dict, timeout: int = 10, target_url: str = None) -> bool:
    """
    Test if a proxy is working by accessing the target URL.
    
    Args:
        proxy: Proxy dict with 'http' and 'https' keys
        timeout: Request timeout in seconds
        target_url: URL to test against (default: FBref homepage)
        
    Returns:
        True if proxy is working, False otherwise
    """
    test_url = target_url or FBREF_TEST_URL
    
    try:
        response = requests.get(
            test_url,
            proxies=proxy,
            timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        # Check for successful response (not just 200, could be 403 if blocked)
        return response.status_code == 200
    except Exception:
        return False


def load_blacklist(config_path: Path) -> Set[str]:
    """Load blacklisted proxy keys from config file."""
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return set(config.get('blacklist', []))
        except Exception:
            pass
    return set()


def save_blacklist(config_path: Path, blacklist: Set[str]):
    """Save blacklist to config file (preserves other config data)."""
    config = {}
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception:
            pass
    
    config['blacklist'] = list(blacklist)
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        TUI.error(f"Failed to save blacklist: {e}")


def add_to_blacklist(config_path: Path, proxy: Dict):
    """Add a proxy to the blacklist."""
    blacklist = load_blacklist(config_path)
    proxy_key = get_proxy_key(proxy)
    blacklist.add(proxy_key)
    save_blacklist(config_path, blacklist)


def refresh_proxies(config_path: Path = None, min_working: int = 5) -> int:
    """
    Fetch and health check proxies, save working ones to config.
    
    Args:
        config_path: Path to proxy config file. If None, uses default.
        min_working: Minimum number of working proxies to fetch
        
    Returns:
        Number of working proxies saved
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "proxy_config.json"
    
    TUI.info("Fetching fresh proxies from public sources...")
    
    # Load blacklist
    blacklist = load_blacklist(config_path)
    if blacklist:
        TUI.info(f"Loaded {len(blacklist)} blacklisted proxies")
    
    # Fetch with blacklist filter
    working_proxies = fetch_free_proxies(blacklist=blacklist, min_needed=min_working)
    
    if not working_proxies:
        TUI.warning("No proxies fetched from public sources")
        return 0
    
    if working_proxies:
        # Save working proxies to config (preserve blacklist)
        try:
            config = {}
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['proxies'] = working_proxies
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            TUI.success(f"Saved {len(working_proxies)} working proxies to {config_path}")
        except Exception as e:
            TUI.error(f"Failed to save proxies: {e}")
    else:
        TUI.warning("No working proxies found")
    
    return len(working_proxies)
