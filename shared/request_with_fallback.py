"""Request wrapper with proxy fallback and hybrid rate-limit handling."""
import time
import random
from typing import Optional, Dict, Any

from shared.proxy_manager import ProxyManager
from shared.scraper_utils import get_proxy_manager, get_session
from shared.tui import TUI


class RateLimitError(Exception):
    """Raised when rate limited after all retries."""
    pass


def request_with_fallback(method: str, url: str, max_retries: int = 3, 
                         use_proxy: bool = True, **kwargs) -> Any:
    """
    Make HTTP request with automatic proxy fallback and hybrid 429 handling.
    
    Strategy:
    - Plan A (proxies available): Rotate proxy on 429, immediate retry
    - Plan B (direct connection): Exponential backoff on 429
    
    Args:
        method: HTTP method (get, post, etc.)
        url: Request URL
        max_retries: Maximum retry attempts for Plan B
        use_proxy: Whether to try proxy first
        **kwargs: Additional arguments for session.request()
    
    Returns:
        Response object
    
    Raises:
        RateLimitError: If rate limited after all retries
    """
    proxy_manager = get_proxy_manager()
    last_exception = None
    current_proxy = None
    
    # Determine which plan to use
    has_proxies = (
        use_proxy and 
        proxy_manager and 
        not proxy_manager.no_proxy and 
        proxy_manager.has_available_proxies()
    )
    
    # Plan A: Try with proxies
    if has_proxies:
        max_proxy_attempts = len(proxy_manager.proxies) * 2  # Allow cycling through all proxies
        
        for attempt in range(max_proxy_attempts):
            try:
                session = get_session(use_proxy=True)
                current_proxy = proxy_manager.get_proxy()
                
                if not current_proxy:
                    # No available proxies (all rate-limited or failed)
                    TUI.warning("No available proxies, falling back to direct connection")
                    break
                
                session.proxies.update(current_proxy)
                
                response = session.request(
                    method, url, 
                    timeout=kwargs.get('timeout', 30), 
                    **{k: v for k, v in kwargs.items() if k != 'timeout'}
                )
                
                # Handle 429 - Plan A: rotate proxy
                if response.status_code == 429:
                    proxy_manager.mark_proxy_rate_limited(current_proxy)
                    
                    if proxy_manager.has_available_proxies():
                        TUI.info("Rotating to next proxy...")
                        continue  # Try next proxy immediately
                    else:
                        TUI.warning("All proxies rate-limited, falling back to direct")
                        break
                
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
                error_str = str(e).lower()
                
                # Check if it's a proxy error
                is_proxy_error = (
                    'proxy' in error_str or 
                    'tunnel' in error_str or 
                    ('connection' in error_str and current_proxy)
                )
                
                if is_proxy_error and current_proxy:
                    proxy_manager.mark_proxy_failed(current_proxy)
                    current_proxy = None
                    
                    if not proxy_manager.proxies:
                        TUI.warning("All proxies failed, falling back to direct connection")
                        break
                    continue
                else:
                    # Not a proxy error, fall through to direct connection
                    break
    
    # Plan B: Direct connection with exponential backoff
    if use_proxy:
        TUI.info("Using direct connection")
    
    session = get_session(use_proxy=False)
    
    for attempt in range(max_retries):
        try:
            response = session.request(
                method, url, 
                timeout=kwargs.get('timeout', 30), 
                **{k: v for k, v in kwargs.items() if k != 'timeout'}
            )
            
            # Handle 429 - Plan B: exponential backoff
            if response.status_code == 429:
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter: 2s, 4s, 8s, etc.
                    base_wait = 2 ** (attempt + 1)
                    jitter = random.uniform(0, 1)
                    wait_time = base_wait + jitter
                    TUI.warning(f"Rate limited (429). Waiting {wait_time:.1f}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise RateLimitError(f"Rate limited after {max_retries} retries")
            
            response.raise_for_status()
            
            # Log IP on first direct connection
            if proxy_manager and proxy_manager.current_ip is None:
                try:
                    proxy_manager.log_ip_change(session)
                except Exception:
                    pass
            
            return response
            
        except RateLimitError:
            raise
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                wait_time = 2 * (attempt + 1)
                TUI.warning(f"Request failed, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
    
    raise last_exception


def get_request_delay(proxy_manager: Optional[ProxyManager] = None) -> float:
    """
    Get recommended delay between requests based on proxy availability.
    
    Returns:
        Delay in seconds:
        - 3-5s if proxies available (Plan A)
        - 5-10s if direct connection (Plan B)
    """
    if proxy_manager and proxy_manager.has_available_proxies():
        # Plan A: shorter delays with proxy rotation
        return random.uniform(3, 5)
    else:
        # Plan B: longer delays for direct connection
        return random.uniform(5, 10)
