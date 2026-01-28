"""
Stock data scraper.

Fetches stock price data from Alpha Vantage API with yfinance fallback.
Outputs JSON to stdout for piping to ingestion services.
"""
import json
import sys
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    import requests_cache
    REQUESTS_CACHE_AVAILABLE = True
except ImportError:
    REQUESTS_CACHE_AVAILABLE = False

# Add src directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.tui import TUI
from shared.trading_config import (
    get_all_stocks, get_primary_stocks, get_secondary_stocks,
    get_regional_stocks, get_stock_by_symbol
)


class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, calls_per_min: int = 5, calls_per_day: int = 25):
        self.calls_per_min = calls_per_min
        self.calls_per_day = calls_per_day
        self._minute_calls: List[float] = []
        self._day_calls: List[float] = []
        self._day_start: Optional[datetime] = None
    
    def can_call(self) -> bool:
        """Check if we can make an API call within rate limits."""
        now = time.time()
        now_dt = datetime.now()
        
        # Reset day counter at midnight
        if self._day_start is None or now_dt.date() != self._day_start.date():
            self._day_calls = []
            self._day_start = now_dt
        
        # Clean up old minute calls
        self._minute_calls = [t for t in self._minute_calls if now - t < 60]
        
        # Check limits
        if len(self._minute_calls) >= self.calls_per_min:
            return False
        if len(self._day_calls) >= self.calls_per_day:
            return False
        
        return True
    
    def record_call(self) -> None:
        """Record that an API call was made."""
        now = time.time()
        now_dt = datetime.now()
        
        if self._day_start is None:
            self._day_start = now_dt
        
        self._minute_calls.append(now)
        self._day_calls.append(now)
    
    def wait_if_needed(self) -> float:
        """Wait if rate limited. Returns seconds waited, or -1 if day limit reached."""
        if self.can_call():
            return 0.0
        
        now = time.time()
        
        # Check if day limit reached
        if len(self._day_calls) >= self.calls_per_day:
            return -1.0
        
        # Wait for minute limit to reset
        if self._minute_calls:
            oldest = min(self._minute_calls)
            wait_time = 60 - (now - oldest) + 0.1
            if wait_time > 0:
                time.sleep(wait_time)
                return wait_time
        
        return 0.0


class StockScraper:
    """Scraper for stock price data."""
    
    ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: Optional[str] = None, use_cache: bool = True):
        """Initialize scraper.
        
        Args:
            api_key: Alpha Vantage API key (optional, will use yfinance if not provided)
            use_cache: Whether to use request caching
        """
        self.api_key = api_key
        self.rate_limiter = RateLimiter(calls_per_min=5, calls_per_day=25)
        
        # Setup session with optional caching
        if use_cache and REQUESTS_CACHE_AVAILABLE:
            cache_path = Path(__file__).parent.parent.parent / "cache" / "stock_api_cache"
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.session = requests_cache.CachedSession(
                str(cache_path),
                expire_after=3600,  # 1 hour cache
                allowable_methods=['GET']
            )
        else:
            self.session = requests.Session()
    
    def fetch_price_history_api(self, symbol: str, outputsize: str = "full") -> Optional[Dict[str, Any]]:
        """Fetch price history from Alpha Vantage API."""
        if not self.api_key:
            return None
        
        # Check rate limits
        wait_result = self.rate_limiter.wait_if_needed()
        if wait_result < 0:
            TUI.warning(f"Daily API limit reached for {symbol}")
            return None
        elif wait_result > 0:
            TUI.info(f"Rate limited, waited {wait_result:.1f}s")
        
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": outputsize,
            "apikey": self.api_key
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(self.ALPHA_VANTAGE_BASE_URL, params=params, timeout=30)
                self.rate_limiter.record_call()
                
                if response.status_code == 429:
                    delay = (2 ** attempt) * 2
                    TUI.warning(f"Rate limited for {symbol}, retrying in {delay:.1f}s")
                    time.sleep(delay)
                    continue
                
                if response.status_code != 200:
                    TUI.error(f"API error for {symbol}: HTTP {response.status_code}")
                    return None
                
                data = response.json()
                
                if "Error Message" in data:
                    TUI.error(f"API error for {symbol}: {data['Error Message']}")
                    return None
                
                if "Note" in data:
                    delay = (2 ** attempt) * 2
                    TUI.warning(f"API rate limit message for {symbol}, retrying in {delay:.1f}s")
                    time.sleep(delay)
                    continue
                
                if "Time Series (Daily)" not in data:
                    TUI.warning(f"No time series data for {symbol}")
                    return None
                
                return data
                
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = (2 ** attempt) * 0.5
                    time.sleep(delay)
                    continue
                TUI.error(f"Request failed for {symbol}: {e}")
                return None
        
        return None
    
    def fetch_company_overview_api(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch company overview from Alpha Vantage API."""
        if not self.api_key:
            return None
        
        wait_result = self.rate_limiter.wait_if_needed()
        if wait_result < 0:
            return None
        
        params = {
            "function": "OVERVIEW",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        try:
            response = self.session.get(self.ALPHA_VANTAGE_BASE_URL, params=params, timeout=30)
            self.rate_limiter.record_call()
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if not data or "Symbol" not in data:
                return None
            
            return data
            
        except Exception:
            return None
    
    def fetch_via_yfinance(self, symbol: str, period: str = "1y") -> Optional[Dict[str, Any]]:
        """Fetch price history using yfinance."""
        if not YFINANCE_AVAILABLE:
            TUI.error("yfinance not installed - cannot use fallback")
            return None
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Get historical data
            hist = ticker.history(period=period)
            
            if hist.empty:
                TUI.warning(f"No yfinance data for {symbol}")
                return None
            
            # Get company info
            try:
                info = ticker.info
            except Exception:
                info = {}
            
            # Convert to our format
            price_data = []
            for date, row in hist.iterrows():
                price_data.append({
                    "timestamp": date.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]) if row["Open"] else None,
                    "high": float(row["High"]) if row["High"] else None,
                    "low": float(row["Low"]) if row["Low"] else None,
                    "close": float(row["Close"]) if row["Close"] else None,
                    "volume": float(row["Volume"]) if row["Volume"] else None
                })
            
            return {
                "symbol": symbol,
                "prices": price_data,
                "metadata": {
                    "name": info.get("longName", info.get("shortName", symbol)),
                    "sector": info.get("sector", ""),
                    "industry": info.get("industry", ""),
                    "market_cap": info.get("marketCap"),
                    "exchange": info.get("exchange", "")
                },
                "source": "yfinance"
            }
            
        except Exception as e:
            TUI.error(f"yfinance error for {symbol}: {e}")
            return None
    
    def _parse_alpha_vantage_data(self, symbol: str, data: Dict[str, Any],
                                   overview: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Parse Alpha Vantage response into our standard format."""
        time_series = data.get("Time Series (Daily)", {})
        
        price_data = []
        for date_str, values in time_series.items():
            price_data.append({
                "timestamp": date_str,
                "open": float(values.get("1. open", 0)),
                "high": float(values.get("2. high", 0)),
                "low": float(values.get("3. low", 0)),
                "close": float(values.get("4. close", 0)),
                "volume": float(values.get("5. volume", 0))
            })
        
        # Sort by date (oldest first)
        price_data.sort(key=lambda x: x["timestamp"])
        
        # Build metadata
        metadata = {
            "name": symbol,
            "sector": "",
            "industry": "",
            "market_cap": None,
            "exchange": ""
        }
        
        if overview:
            metadata["name"] = overview.get("Name", symbol)
            metadata["sector"] = overview.get("Sector", "")
            metadata["industry"] = overview.get("Industry", "")
            metadata["exchange"] = overview.get("Exchange", "")
            try:
                metadata["market_cap"] = float(overview.get("MarketCapitalization", 0))
            except (ValueError, TypeError):
                pass
        
        return {
            "symbol": symbol,
            "prices": price_data,
            "metadata": metadata,
            "source": "alpha_vantage"
        }
    
    def fetch_stock_data(self, symbol: str, use_fallback: bool = True) -> Optional[Dict[str, Any]]:
        """Fetch stock data with automatic fallback."""
        stock_config = get_stock_by_symbol(symbol)
        if not stock_config:
            TUI.warning(f"Unknown stock symbol: {symbol}")
            return None
        
        # Try Alpha Vantage API first
        if self.api_key and self.rate_limiter.can_call():
            TUI.info(f"Fetching {symbol} from Alpha Vantage API")
            data = self.fetch_price_history_api(symbol)
            
            if data:
                # Try to get company overview (optional)
                overview = None
                if self.rate_limiter.can_call():
                    overview = self.fetch_company_overview_api(symbol)
                
                result = self._parse_alpha_vantage_data(symbol, data, overview)
                # Add config metadata
                result["metadata"]["sector"] = stock_config.get("sector", result["metadata"]["sector"])
                result["metadata"]["industry"] = stock_config.get("industry", result["metadata"]["industry"])
                result["metadata"]["exchange"] = stock_config.get("exchange", result["metadata"]["exchange"])
                return result
        
        # Fallback to yfinance
        if use_fallback and YFINANCE_AVAILABLE:
            TUI.info(f"Using yfinance fallback for {symbol}")
            result = self.fetch_via_yfinance(stock_config.get("yfinance", symbol))
            if result:
                # Add config metadata
                result["metadata"]["sector"] = stock_config.get("sector", result["metadata"]["sector"])
                result["metadata"]["industry"] = stock_config.get("industry", result["metadata"]["industry"])
                result["metadata"]["exchange"] = stock_config.get("exchange", result["metadata"]["exchange"])
            return result
        
        return None
    
    def scrape_symbol(self, symbol: str) -> Dict[str, Any]:
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
            data = self.fetch_stock_data(symbol)
            
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
            category: Optional category filter ('primary', 'secondary', 'regional')
        """
        if symbols is None or len(symbols) == 0:
            if category == "primary":
                stocks = get_primary_stocks()
            elif category == "secondary":
                stocks = get_secondary_stocks()
            elif category == "regional":
                stocks = get_regional_stocks()
            else:
                stocks = get_all_stocks()
            symbols = list(stocks.keys())
        else:
            # Filter symbols to only those in config
            all_stocks = get_all_stocks()
            symbols = [s for s in symbols if s.upper() in all_stocks]
        
        if not symbols:
            TUI.warning("No symbols to scrape")
            return []
        
        TUI.info(f"Starting stock collection for {len(symbols)} symbols")
        
        results = []
        for i, symbol in enumerate(symbols):
            TUI.info(f"Collecting {symbol} ({i+1}/{len(symbols)})")
            
            result = self.scrape_symbol(symbol)
            results.append(result)
            
            if result["success"]:
                TUI.success(f"[OK] {symbol}: {len(result['prices'])} prices ({result['source']})")
            else:
                TUI.error(f"[FAIL] {symbol}: {result['error']}")
        
        successful = sum(1 for r in results if r["success"])
        TUI.success(f"\n✓ Successfully scraped {successful}/{len(symbols)} symbols")
        
        return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Stock Scraper - Fetch stock price data from Alpha Vantage/yfinance'
    )
    parser.add_argument('--symbol', type=str, nargs='*', default=None,
                       help='Symbol(s) to scrape (can specify multiple, for parallel execution use single --symbol)')
    parser.add_argument('--category', type=str, choices=['primary', 'secondary', 'regional'],
                       help='Category of stocks to scrape')
    parser.add_argument('--api-key', type=str, default=None,
                       help='Alpha Vantage API key (or set ALPHA_VANTAGE_API_KEY env var)')
    parser.add_argument('--no-cache', action='store_true',
                       help='Disable request caching')
    parser.add_argument('--pretty', action='store_true',
                       help='Pretty print JSON output')
    
    args = parser.parse_args()
    
    # Get API key from args or environment
    api_key = args.api_key or None
    if not api_key:
        import os
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    try:
        scraper = StockScraper(api_key=api_key, use_cache=not args.no_cache)
        
        if args.symbol:
            # One or more symbols
            if len(args.symbol) == 1:
                # Single symbol
                result = scraper.scrape_symbol(args.symbol[0])
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
