"""Standalone script to refresh proxy list."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.proxy_refresh import refresh_proxies
from shared.tui import TUI


def main():
    """Main function to refresh proxies."""
    TUI.header("Proxy Refresh Tool")
    
    working_count = refresh_proxies()
    
    if working_count > 0:
        TUI.success(f"Refresh complete: {working_count} working proxies available")
    else:
        TUI.error("No working proxies found. Check your internet connection or proxy sources.")


if __name__ == "__main__":
    main()

