"""Proxy management for web scraping."""
import json
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

from shared.tui import TUI


class ProxyManager:
    """Manages proxy rotation and IP tracking."""
    
    def __init__(self, config_path: Optional[Path] = None, no_proxy: bool = False):
        """
        Initialize proxy manager.
        
        Args:
            config_path: Path to proxy config file
            no_proxy: If True, disable proxy usage
        """
        self.config_path = config_path or Path(__file__).parent.parent / "proxy_config.json"
        self.no_proxy = no_proxy
        self.proxies: List[Dict] = []
        self.current_proxy_index = 0
        self.current_ip: Optional[str] = None
        self.current_country: Optional[str] = None
        
        if not no_proxy:
            self._load_proxies()
    
    def _load_proxies(self):
        """Load proxies from config file or fetch free proxies."""
        # Try to load from config file
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.proxies = config.get('proxies', [])
                    if self.proxies:
                        TUI.info(f"Loaded {len(self.proxies)} proxies from config")
                        return
            except Exception as e:
                TUI.warning(f"Failed to load proxy config: {e}")
        
        # Try to fetch free proxies
        TUI.info("Attempting to fetch free proxies...")
        fetched_proxies = self._fetch_free_proxies()
        
        if fetched_proxies:
            self.proxies = fetched_proxies
            TUI.success(f"Fetched {len(self.proxies)} free proxies")
            # Save to config for future use
            self._save_proxies()
        else:
            TUI.warning("No proxies available, using direct connection")
    
    def _fetch_free_proxies(self) -> List[Dict]:
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
        
        # Try geonode.com (alternative)
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
    
    def _save_proxies(self):
        """Save proxies to config file."""
        try:
            config = {'proxies': self.proxies}
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass
    
    def get_proxy(self) -> Optional[Dict]:
        """Get next proxy in rotation."""
        if self.no_proxy or not self.proxies:
            return None
        
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy
    
    def mark_proxy_failed(self, proxy: Dict):
        """Mark a proxy as failed and remove it from rotation."""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            TUI.warning(f"Removed failed proxy from rotation ({len(self.proxies)} remaining)")
            if self.current_proxy_index >= len(self.proxies) and self.proxies:
                self.current_proxy_index = 0
    
    def get_ip_info(self, session) -> Tuple[Optional[str], Optional[str]]:
        """
        Get current IP address and country.
        
        Args:
            session: Requests session to use
            
        Returns:
            Tuple of (ip, country)
        """
        try:
            # Try ipapi.co first (free tier: 1000/day)
            response = session.get('https://ipapi.co/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                ip = data.get('ip')
                country = data.get('country_name')
                return ip, country
        except Exception:
            pass
        
        try:
            # Fallback to ip-api.com (free tier: 45/min)
            response = session.get('http://ip-api.com/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                ip = data.get('query')
                country = data.get('country')
                return ip, country
        except Exception:
            pass
        
        return None, None
    
    def log_ip_change(self, session):
        """Log IP address change."""
        ip, country = self.get_ip_info(session)
        
        if ip != self.current_ip:
            self.current_ip = ip
            self.current_country = country
            
            if ip:
                if country:
                    TUI.info(f"IP changed: {ip} ({country})")
                else:
                    TUI.info(f"IP changed: {ip}")
            else:
                TUI.warning("Could not determine IP address")

