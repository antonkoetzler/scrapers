"""
Utility for warning about long-running requests.
Shows a warning message if a request takes longer than a specified threshold.
"""

import threading
import time
from typing import Callable, Optional
from shared.tui import TUI


class LongRequestWarning:
    """Context manager that warns if an operation takes too long."""
    
    def __init__(self, threshold_seconds: float = 25.0, 
                 warning_message: str = "Still processing... This may take a while."):
        """
        Initialize long request warning.
        
        Args:
            threshold_seconds: Time in seconds before showing warning
            warning_message: Message to display when threshold is exceeded
        """
        self.threshold_seconds = threshold_seconds
        self.warning_message = warning_message
        self.start_time: Optional[float] = None
        self.warning_shown = False
        self._warning_timer: Optional[threading.Timer] = None
    
    def __enter__(self):
        """Start monitoring."""
        self.start_time = time.time()
        self.warning_shown = False
        
        # Schedule warning if threshold is exceeded
        self._warning_timer = threading.Timer(
            self.threshold_seconds,
            self._show_warning
        )
        self._warning_timer.daemon = True
        self._warning_timer.start()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop monitoring."""
        if self._warning_timer:
            self._warning_timer.cancel()
        
        # If warning was shown, show completion message
        if self.warning_shown:
            elapsed = time.time() - (self.start_time or 0)
            TUI.info(f"Request completed in {elapsed:.1f}s")
        
        return False
    
    def _show_warning(self):
        """Show warning message."""
        if not self.warning_shown:
            self.warning_shown = True
            TUI.warning(self.warning_message)


def with_long_request_warning(threshold_seconds: float = 25.0,
                              warning_message: str = "Still processing... This may take a while."):
    """
    Decorator for functions that might take a long time.
    
    Args:
        threshold_seconds: Time in seconds before showing warning
        warning_message: Message to display when threshold is exceeded
    
    Example:
        @with_long_request_warning(threshold_seconds=25.0)
        def slow_function():
            time.sleep(30)
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            with LongRequestWarning(threshold_seconds, warning_message):
                return func(*args, **kwargs)
        return wrapper
    return decorator
