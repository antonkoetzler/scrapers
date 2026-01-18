"""Shared proxy refresh functionality."""
import time
from pathlib import Path
from typing import Dict, List, Set, Optional

import requests

from shared.tui import TUI


# Target URL for testing proxies (use httpbin for basic connectivity)
HTTPBIN_TEST_URL = "http://httpbin.org/ip"  # Simple connectivity test


def get_proxy_key(proxy: Dict) -> str:
    """Extract proxy key (ip:port) from proxy dict."""
    url = proxy.get('http', proxy.get('https', ''))
    # Extract ip:port from http://ip:port
    if url.startswith('http://'):
        return url[7:]
    elif url.startswith('https://'):
        return url[8:]
    return url


def proxy_str_to_dict(proxy_str: str) -> Optional[Dict]:
    """Convert proxy string (ip:port) to proxy dict."""
    parts = proxy_str.strip().split(':')
    if len(parts) != 2:
        return None
    
    host, port = parts[0].strip(), parts[1].strip()
    if not host or not port:
        return None
    
    return {
        'http': f'http://{host}:{port}',
        'https': f'http://{host}:{port}'
    }


def health_check_proxy(proxy: Dict, timeout: int = 10, target_url: str = None) -> bool:
    """
    Test if a proxy is working by accessing the target URL.
    
    First tests basic connectivity with httpbin, then tests target URL if provided.
    
    Args:
        proxy: Proxy dict with 'http' and 'https' keys
        timeout: Request timeout in seconds
        target_url: URL to test against (default: httpbin for basic connectivity)
        
    Returns:
        True if proxy is working, False otherwise
    """
    # First test basic connectivity with httpbin
    try:
        response = requests.get(
            HTTPBIN_TEST_URL,
            proxies=proxy,
            timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        if response.status_code != 200:
            return False  # Proxy doesn't work at all
    except Exception:
        return False  # Proxy is dead/broken
    
    # If target_url provided, test that too
    if target_url:
        try:
            response = requests.get(
                target_url,
                proxies=proxy,
                timeout=timeout,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            return response.status_code == 200
        except Exception:
            return False
    
    return True  # Basic connectivity works


def load_proxies_from_txt(config_path: Path) -> List[Dict]:
    """Load proxies from .txt file (one ip:port per line)."""
    proxies = []
    if not config_path.exists():
        return proxies
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                proxy_dict = proxy_str_to_dict(line)
                if proxy_dict:
                    proxies.append(proxy_dict)
    except Exception as e:
        TUI.warning(f"Failed to load proxies from {config_path}: {e}")
    
    return proxies


def load_blacklist(blacklist_path: Path) -> Set[str]:
    """Load blacklisted proxy keys from blacklist file."""
    blacklist = set()
    if not blacklist_path.exists():
        return blacklist
    
    try:
        with open(blacklist_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    blacklist.add(line)
    except Exception:
        pass
    
    return blacklist


def save_blacklist(blacklist_path: Path, blacklist: Set[str]):
    """Save blacklist to file."""
    try:
        with open(blacklist_path, 'w', encoding='utf-8') as f:
            f.write("# Blacklisted proxies (one per line)\n")
            for proxy_key in sorted(blacklist):
                f.write(f"{proxy_key}\n")
    except Exception as e:
        TUI.error(f"Failed to save blacklist: {e}")


def add_to_blacklist(blacklist_path: Path, proxy: Dict):
    """Add a proxy to the blacklist."""
    blacklist = load_blacklist(blacklist_path)
    proxy_key = get_proxy_key(proxy)
    blacklist.add(proxy_key)
    save_blacklist(blacklist_path, blacklist)
