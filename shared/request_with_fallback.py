"""Request wrapper with proxy fallback."""
from typing import Optional, Dict, Any
import time

from shared.proxy_manager import ProxyManager
from shared.scraper_utils import get_proxy_manager, get_session
from shared.tui import TUI


def request_with_fallback(method: str, url: str, max_retries: int = 3, 
                         use_proxy: bool = True, **kwargs) -> Any:
    """
    Make HTTP request with automatic proxy fallback.
    
    Args:
        method: HTTP method (get, post, etc.)
        url: Request URL
        max_retries: Maximum retry attempts
        use_proxy: Whether to try proxy first
        **kwargs: Additional arguments for session.request()
    
    Returns:
        Response object
    """
    proxy_manager = get_proxy_manager()
    last_exception = None
    
    # Try with proxy first (if enabled)
    if use_proxy and proxy_manager and not proxy_manager.no_proxy and proxy_manager.proxies:
        proxy = None
        for attempt in range(max_retries):
            try:
                session = get_session(use_proxy=True)
                proxy = proxy_manager.get_proxy()
                
                if proxy:
                    session.proxies.update(proxy)
                
                response = session.request(method, url, timeout=kwargs.get('timeout', 30), **{k: v for k, v in kwargs.items() if k != 'timeout'})
                response.raise_for_status()
                
                # Log IP on first successful proxy request
                if proxy_manager.current_ip is None:
                    try:
                        proxy_manager.log_ip_change(session)
                    except Exception:
                        pass
                
                return response
                
            except Exception as e:
                last_exception = e
                # Check if it's a proxy error
                error_str = str(e).lower()
                if 'proxy' in error_str or 'tunnel' in error_str or ('connection' in error_str and proxy):
                    if proxy:
                        proxy_manager.mark_proxy_failed(proxy)
                        proxy = None  # Reset for next iteration
                    if not proxy_manager.proxies:
                        TUI.warning("All proxies failed, falling back to direct connection")
                        break
                    if attempt < max_retries - 1:
                        time.sleep(1)  # Shorter delay for proxy retries
                    continue
                else:
                    # Not a proxy error, fall through to direct connection
                    break
    
    # Fallback to direct connection
    if use_proxy:
        TUI.info("Using direct connection (no proxy)")
    
    session = get_session(use_proxy=False)
    for attempt in range(max_retries):
        try:
            response = session.request(method, url, timeout=kwargs.get('timeout', 30), **{k: v for k, v in kwargs.items() if k != 'timeout'})
            response.raise_for_status()
            # Log IP on first direct connection
            if proxy_manager and proxy_manager.current_ip is None:
                try:
                    proxy_manager.log_ip_change(session)
                except Exception:
                    pass
            return response
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))
            else:
                raise
    
    raise last_exception

