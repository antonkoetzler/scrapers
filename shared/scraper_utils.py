"""Shared utilities for web scraping with anti-scraping measures."""
import cloudscraper
from typing import Optional

from shared.proxy_manager import ProxyManager
from shared.tui import TUI


# Global proxy manager instance
_proxy_manager: Optional[ProxyManager] = None


def init_proxy_manager(config_path=None, no_proxy: bool = False):
    """Initialize global proxy manager."""
    global _proxy_manager
    _proxy_manager = ProxyManager(config_path, no_proxy)
    return _proxy_manager


def get_proxy_manager() -> Optional[ProxyManager]:
    """Get global proxy manager instance."""
    return _proxy_manager


def get_session(referer: str = 'https://www.betano.bet.br/', 
                origin: str = 'https://www.betano.bet.br/',
                use_proxy: bool = True,
                retry_without_proxy: bool = True) -> cloudscraper.CloudScraper:
    """
    Create a cloudscraper session to bypass Cloudflare.
    
    Args:
        referer: Referer header value
        origin: Origin header value
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
    
    session.headers.update({
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': referer,
        'Origin': origin,
    })
    
    # Apply proxy if available (but don't fail if proxy is bad)
    if use_proxy and _proxy_manager and not _proxy_manager.no_proxy:
        proxy = _proxy_manager.get_proxy()
        if proxy:
            session.proxies.update(proxy)
    
    return session

