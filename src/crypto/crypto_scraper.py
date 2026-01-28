"""
Cryptocurrency data scraper.

Fetches cryptocurrency price data from CoinGecko API.
Outputs JSON to stdout for piping to ingestion services.
"""
import json
import sys
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse

try:
    import requests_cache
    REQUESTS_CACHE_AVAILABLE = True
except ImportError:
    REQUESTS_CACHE_AVAILABLE = False

# Add src directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.tui import TUI
from shared.trading_config import (
    get_all_crypto, get_primary_crypto, get_secondary_crypto,
    get_stablecoins, get_crypto_by_symbol
)


class CryptoRateLimiter:
    """Rate limiter for CoinGecko API calls."""
    
    def __init__(self, calls_per_min: int = 10):
        self.calls_per_min = calls_per_min
        self._calls: List[float] = []
    
    def can_call(self) -> bool:
        """Check if we can make an API call within rate limits."""
        now = time.time()
        self._calls = [t for t in self._calls if now - t < 60]
        return len(self._calls) < self.calls_per_min
    
    def record_call(self) -> None:
        """Record that an API call was made."""
        self._calls.append(time.time())
    
    def wait_if_needed(self) -> float:
        """Wait if rate limited. Returns seconds waited."""
        if self.can_call():
            return 0.0
        
        now = time.time()
        if self._calls:
            oldest = min(self._calls)
            wait_time = 60 - (now - oldest) + 1.0  # Add 1s buffer
            if wait_time > 0:
                time.sleep(wait_time)
                return wait_time
        
        return 0.0


class CryptoScraper:
    """Scraper for cryptocurrency price data."""
    
    COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self, api_key: Optional[str] = None, use_cache: bool = True):
        """Initialize scraper.
        
        Args:
            api_key: CoinGecko API key (optional, free tier works without key)
            use_cache: Whether to use request caching
        """
        self.api_key = api_key
        self.rate_limiter = CryptoRateLimiter(calls_per_min=10)
        
        # Setup session with optional caching
        if use_cache and REQUESTS_CACHE_AVAILABLE:
            cache_path = Path(__file__).parent.parent.parent / "cache" / "crypto_api_cache"
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.session = requests_cache.CachedSession(
                str(cache_path),
                expire_after=1800,  # 30 min cache
                allowable_methods=['GET']
            )
        else:
            self.session = requests.Session()
        
        # Set headers
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "Arbihawk Trading Scraper"
        })
        
        # Add API key to headers if provided
        if self.api_key:
            self.session.headers["x-cg-demo-api-key"] = self.api_key
    
    def fetch_price_history(self, symbol: str, days: int = 365) -> Optional[Dict[str, Any]]:
        """Fetch price history from CoinGecko API."""
        crypto_config = get_crypto_by_symbol(symbol)
        if not crypto_config:
            TUI.error(f"Unknown crypto symbol: {symbol}")
            return None
        
        coin_id = crypto_config.get('coingecko_id')
        if not coin_id:
            TUI.error(f"No CoinGecko ID for {symbol}")
            return None
        
        # Check rate limits
        wait_result = self.rate_limiter.wait_if_needed()
        if wait_result > 0:
            TUI.info(f"Rate limited, waited {wait_result:.1f}s")
        
        # CoinGecko market_chart endpoint
        url = f"{self.COINGECKO_BASE_URL}/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": min(days, 365),  # Max 365 for daily granularity
            "interval": "daily"
        }
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                self.rate_limiter.record_call()
                
                if response.status_code == 429:
                    delay = min((2 ** attempt) * (2 + attempt), 60)  # Cap at 60s
                    TUI.warning(f"Rate limited for {symbol}, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    # Clear recent calls to reset rate limiter state
                    self.rate_limiter._calls = [t for t in self.rate_limiter._calls if time.time() - t > 60]
                    continue
                
                if response.status_code != 200:
                    TUI.error(f"API error for {symbol}: HTTP {response.status_code}")
                    return None
                
                data = response.json()
                
                if "prices" not in data:
                    TUI.warning(f"No price data for {symbol}")
                    return None
                
                return data
                
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    delay = (2 ** attempt) * 0.5
                    TUI.warning(f"Request failed for {symbol}: {e}. Retrying in {delay:.1f}s")
                    time.sleep(delay)
                    continue
                TUI.error(f"Request failed for {symbol}: {e}")
                return None
            except Exception as e:
                TUI.error(f"Unexpected error fetching {symbol}: {e}")
                return None
        
        return None
    
    def fetch_coin_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch coin metadata from CoinGecko API."""
        crypto_config = get_crypto_by_symbol(symbol)
        if not crypto_config:
            return None
        
        coin_id = crypto_config.get('coingecko_id')
        if not coin_id:
            return None
        
        # Check rate limits
        wait_result = self.rate_limiter.wait_if_needed()
        if wait_result > 0:
            TUI.info(f"Rate limited, waited {wait_result:.1f}s")
        
        url = f"{self.COINGECKO_BASE_URL}/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false"
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            self.rate_limiter.record_call()
            
            if response.status_code != 200:
                return None
            
            return response.json()
            
        except Exception:
            return None
    
    def _parse_market_chart_data(self, symbol: str, data: Dict[str, Any],
                                 coin_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Parse CoinGecko market_chart response into our standard format."""
        prices = data.get("prices", [])
        volumes = data.get("total_volumes", [])
        
        # Create volume lookup by timestamp
        volume_map = {v[0]: v[1] for v in volumes}
        
        price_data = []
        for price_point in prices:
            timestamp_ms = price_point[0]
            close_price = price_point[1]
            
            # Convert timestamp to date string
            date = datetime.fromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d")
            
            # CoinGecko market_chart only provides close prices
            # We'll use close for OHLC (single daily data point)
            price_data.append({
                "timestamp": date,
                "open": close_price,  # Use close as open (approximate)
                "high": close_price,  # Use close as high (approximate)
                "low": close_price,   # Use close as low (approximate)
                "close": close_price,
                "volume": volume_map.get(timestamp_ms)
            })
        
        # Remove duplicates (keep latest for each day)
        seen_dates = {}
        for price in price_data:
            seen_dates[price["timestamp"]] = price
        price_data = sorted(seen_dates.values(), key=lambda x: x["timestamp"])
        
        # Build metadata
        crypto_config = get_crypto_by_symbol(symbol)
        metadata = {
            "name": crypto_config.get("name", symbol) if crypto_config else symbol,
            "category": crypto_config.get("category", "") if crypto_config else "",
            "market_cap": None
        }
        
        if coin_info:
            metadata["name"] = coin_info.get("name", metadata["name"])
            market_data = coin_info.get("market_data", {})
            if market_data:
                metadata["market_cap"] = market_data.get("market_cap", {}).get("usd")
        
        return {
            "symbol": symbol,
            "prices": price_data,
            "metadata": metadata,
            "source": "coingecko"
        }
    
    def fetch_ohlc_data(self, symbol: str, days: int = 365) -> Optional[Dict[str, Any]]:
        """Fetch OHLC data from CoinGecko API."""
        crypto_config = get_crypto_by_symbol(symbol)
        if not crypto_config:
            return None
        
        coin_id = crypto_config.get('coingecko_id')
        if not coin_id:
            return None
        
        # Check rate limits
        self.rate_limiter.wait_if_needed()
        
        # OHLC endpoint
        url = f"{self.COINGECKO_BASE_URL}/coins/{coin_id}/ohlc"
        params = {
            "vs_currency": "usd",
            "days": days
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            self.rate_limiter.record_call()
            
            if response.status_code != 200:
                return None
            
            ohlc_data = response.json()
            
            if not ohlc_data:
                return None
            
            # Parse OHLC: [timestamp, open, high, low, close]
            price_data = []
            for ohlc in ohlc_data:
                if len(ohlc) >= 5:
                    timestamp_ms, open_p, high_p, low_p, close_p = ohlc[:5]
                    date = datetime.fromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d")
                    price_data.append({
                        "timestamp": date,
                        "open": open_p,
                        "high": high_p,
                        "low": low_p,
                        "close": close_p,
                        "volume": None  # OHLC endpoint doesn't include volume
                    })
            
            # Remove duplicates
            seen_dates = {}
            for price in price_data:
                seen_dates[price["timestamp"]] = price
            price_data = sorted(seen_dates.values(), key=lambda x: x["timestamp"])
            
            crypto_config = get_crypto_by_symbol(symbol)
            return {
                "symbol": symbol,
                "prices": price_data,
                "metadata": {
                    "name": crypto_config.get("name", symbol) if crypto_config else symbol,
                    "category": crypto_config.get("category", "") if crypto_config else "",
                    "market_cap": None
                },
                "source": "coingecko_ohlc"
            }
            
        except Exception as e:
            TUI.error(f"OHLC fetch failed for {symbol}: {e}")
            return None
    
    def fetch_crypto_data(self, symbol: str, days: int = 365) -> Optional[Dict[str, Any]]:
        """Fetch crypto data with best available method."""
        TUI.info(f"Fetching {symbol} from CoinGecko")
        
        # Try market_chart first (more complete data)
        data = self.fetch_price_history(symbol, days=days)
        
        if data:
            # Try to get coin info for metadata
            coin_info = None
            if self.rate_limiter.can_call():
                coin_info = self.fetch_coin_info(symbol)
            
            return self._parse_market_chart_data(symbol, data, coin_info)
        
        # Fallback to OHLC endpoint
        TUI.info(f"Trying OHLC endpoint for {symbol}")
        ohlc_data = self.fetch_ohlc_data(symbol, days=days)
        
        return ohlc_data
    
    def scrape_symbol(self, symbol: str, days: int = 365) -> Dict[str, Any]:
        """Scrape data for a single symbol."""
        result = {
            "symbol": symbol,
            "success": False,
            "source": None,
            "prices": [],
            "metadata": {},
            "error": None
        }
        
        try:
            data = self.fetch_crypto_data(symbol, days=days)
            
            if not data:
                result["error"] = "Failed to fetch data"
                return result
            
            result["success"] = True
            result["source"] = data.get("source", "unknown")
            result["prices"] = data.get("prices", [])
            result["metadata"] = data.get("metadata", {})
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def scrape_all(self, symbols: Optional[List[str]] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Scrape data for multiple symbols.
        
        Args:
            symbols: Optional list of symbols (defaults to all from config)
            category: Optional category filter ('primary', 'secondary', 'stablecoins')
        """
        if symbols is None or len(symbols) == 0:
            if category == "primary":
                crypto = get_primary_crypto()
            elif category == "secondary":
                crypto = get_secondary_crypto()
            elif category == "stablecoins":
                crypto = get_stablecoins()
            else:
                crypto = get_all_crypto()
            symbols = list(crypto.keys())
        else:
            # Filter symbols to only those in config
            all_crypto = get_all_crypto()
            symbols = [s for s in symbols if s.upper() in all_crypto]
        
        if not symbols:
            TUI.warning("No crypto symbols to scrape")
            return []
        
        TUI.info(f"Starting crypto collection for {len(symbols)} symbols")
        
        results = []
        for i, symbol in enumerate(symbols):
            TUI.info(f"Collecting {symbol} ({i+1}/{len(symbols)})")
            
            result = self.scrape_symbol(symbol)
            results.append(result)
            
            if result["success"]:
                TUI.success(f"[OK] {symbol}: {len(result['prices'])} prices")
            else:
                TUI.error(f"[FAIL] {symbol}: {result['error']}")
            
            # Longer delay between symbols to avoid rate limiting
            if i < len(symbols) - 1:
                time.sleep(2.0)  # 2 second delay between symbols
        
        successful = sum(1 for r in results if r["success"])
        TUI.success(f"\n✓ Successfully scraped {successful}/{len(symbols)} symbols")
        
        return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Crypto Scraper - Fetch cryptocurrency price data from CoinGecko'
    )
    parser.add_argument('--symbol', type=str, nargs='*', default=None,
                       help='Symbol(s) to scrape (can specify multiple, for parallel execution use single --symbol)')
    parser.add_argument('--category', type=str, choices=['primary', 'secondary', 'stablecoins'],
                       help='Category of crypto to scrape')
    parser.add_argument('--api-key', type=str, default=None,
                       help='CoinGecko API key (optional, free tier works without key)')
    parser.add_argument('--days', type=int, default=365,
                       help='Number of days of history to fetch (default: 365)')
    parser.add_argument('--no-cache', action='store_true',
                       help='Disable request caching')
    parser.add_argument('--pretty', action='store_true',
                       help='Pretty print JSON output')
    
    args = parser.parse_args()
    
    # Get API key from args or environment
    api_key = args.api_key or None
    if not api_key:
        import os
        api_key = os.getenv('COINGECKO_API_KEY')
    
    try:
        scraper = CryptoScraper(api_key=api_key, use_cache=not args.no_cache)
        
        if args.symbol:
            # One or more symbols
            if len(args.symbol) == 1:
                # Single symbol
                result = scraper.scrape_symbol(args.symbol[0], days=args.days)
                output = [result]
            else:
                # Multiple symbols
                output = scraper.scrape_all(symbols=args.symbol)
        else:
            # All symbols or category
            output = scraper.scrape_all(category=args.category)
        
        # Output JSON
        indent = 2 if args.pretty else None
        print(json.dumps(output, indent=indent, ensure_ascii=False))
        
    except KeyboardInterrupt:
        TUI.warning("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        TUI.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
