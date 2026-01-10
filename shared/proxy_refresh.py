"""Shared proxy refresh functionality."""
import json
import time
from pathlib import Path
from typing import Dict, List

import requests

from shared.tui import TUI


def fetch_free_proxies() -> List[Dict]:
    """Fetch free proxies from public APIs."""
    proxies = []
    
    # Try proxyscrape.com
    try:
        response = requests.get(
            'https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
            timeout=10
        )
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            for line in lines[:20]:  # Limit to 20 proxies
                line = line.strip()
                if ':' in line:
                    host, port = line.split(':')
                    proxies.append({
                        'http': f'http://{host}:{port}',
                        'https': f'http://{host}:{port}'
                    })
    except Exception:
        pass
    
    # Try TheSpeedX/PROXY-List (alternative)
    if not proxies:
        try:
            response = requests.get(
                'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
                timeout=10
            )
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                for line in lines[:20]:
                    line = line.strip()
                    if ':' in line:
                        host, port = line.split(':')
                        proxies.append({
                            'http': f'http://{host}:{port}',
                            'https': f'http://{host}:{port}'
                        })
        except Exception:
            pass
    
    return proxies


def health_check_proxy(proxy: Dict, timeout: int = 5) -> bool:
    """
    Test if a proxy is working.
    
    Args:
        proxy: Proxy dict with 'http' and 'https' keys
        timeout: Request timeout in seconds
        
    Returns:
        True if proxy is working, False otherwise
    """
    try:
        response = requests.get(
            'http://httpbin.org/ip',
            proxies=proxy,
            timeout=timeout
        )
        return response.status_code == 200
    except Exception:
        return False


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
    fetched_proxies = fetch_free_proxies()
    
    if not fetched_proxies:
        TUI.warning("No proxies fetched from public sources")
        return 0
    
    TUI.info(f"Fetched {len(fetched_proxies)} proxies, testing health...")
    
    # Health check all fetched proxies
    working_proxies = []
    for i, proxy in enumerate(fetched_proxies, 1):
        TUI.info(f"Testing proxy {i}/{len(fetched_proxies)}...")
        if health_check_proxy(proxy):
            working_proxies.append(proxy)
            TUI.success(f"Proxy {i} is working")
        else:
            TUI.warning(f"Proxy {i} failed health check")
        time.sleep(0.5)  # Rate limiting
    
    if working_proxies:
        # Save working proxies to config
        try:
            config = {'proxies': working_proxies}
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            TUI.success(f"Saved {len(working_proxies)} working proxies to {config_path}")
        except Exception as e:
            TUI.error(f"Failed to save proxies: {e}")
    else:
        TUI.warning("No working proxies found")
    
    return len(working_proxies)

