"""Shared utilities for web scraping with anti-scraping measures."""
import cloudscraper
from typing import Optional

from shared.proxy_manager import ProxyManager
from shared.tui import TUI


# Global proxy manager instance
_proxy_manager: Optional[ProxyManager] = None


def init_proxy_manager(config_path=None, no_proxy: bool = False, refresh_proxies_flag: bool = False):
    """Initialize global proxy manager."""
    global _proxy_manager
    _proxy_manager = ProxyManager(config_path, no_proxy, refresh_proxies_flag)
    return _proxy_manager


def get_proxy_manager() -> Optional[ProxyManager]:
    """Get global proxy manager instance."""
    return _proxy_manager


def get_session(referer: str = None, 
                origin: str = None,
                accept: str = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                accept_language: str = 'en-US,en;q=0.9',
                use_proxy: bool = True,
                retry_without_proxy: bool = True) -> cloudscraper.CloudScraper:
    """
    Create a cloudscraper session to bypass Cloudflare.
    
    Args:
        referer: Referer header value (optional)
        origin: Origin header value (optional)
        accept: Accept header value (default: HTML)
        accept_language: Accept-Language header value (default: en-US)
        use_proxy: Whether to use proxy if available
    
    Returns:
        Configured cloudscraper session
    """
    session = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    headers = {
        'Accept': accept,
        'Accept-Language': accept_language,
    }
    
    if referer:
        headers['Referer'] = referer
    if origin:
        headers['Origin'] = origin
    
    session.headers.update(headers)
    
    # Apply proxy if available (but don't fail if proxy is bad)
    if use_proxy and _proxy_manager and not _proxy_manager.no_proxy:
        proxy = _proxy_manager.get_proxy()
        if proxy:
            session.proxies.update(proxy)
    
    return session

