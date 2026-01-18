"""Proxy management for web scraping."""
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import requests

from shared.proxy_refresh import (
    health_check_proxy, get_proxy_key, 
    load_proxies_from_txt, load_blacklist, save_blacklist, add_to_blacklist
)
from shared.tui import TUI


class ProxyManager:
    """Manages proxy rotation, blacklist, and rate-limit cooldowns."""
    
    # Cooldown duration for rate-limited proxies (in seconds)
    RATE_LIMIT_COOLDOWN = 600  # 10 minutes
    
    def __init__(self, config_path: Optional[Path] = None, no_proxy: bool = False, 
                 refresh_proxies_flag: bool = False):
        """
        Initialize proxy manager.
        
        Args:
            config_path: Path to proxy config .txt file
            no_proxy: If True, disable proxy usage
            refresh_proxies_flag: If True, auto-refresh when < 5 working proxies (disabled by default)
        """
        self.config_path = config_path or Path(__file__).parent.parent.parent / "proxy_config.txt"
        self.blacklist_path = self.config_path.parent / "proxy_blacklist.txt"
        self.no_proxy = no_proxy
        self.proxies: List[Dict] = []
        self.current_proxy_index = 0
        self.current_ip: Optional[str] = None
        self.current_country: Optional[str] = None
        self.refresh_proxies_flag = refresh_proxies_flag
        
        # Rate-limited proxy tracking: {proxy_key: timestamp_when_rate_limited}
        self.rate_limited_proxies: Dict[str, float] = {}
        
        # Blacklist (persistent, loaded from blacklist file)
        self.blacklist: Set[str] = set()
        
        if not no_proxy:
            self._load_blacklist()
            self._load_proxies()
            # Health check proxies after loading
            self.precheck_proxies()
    
    def _load_blacklist(self):
        """Load blacklist from blacklist file."""
        self.blacklist = load_blacklist(self.blacklist_path)
        if self.blacklist:
            TUI.info(f"Loaded {len(self.blacklist)} blacklisted proxies")
    
    def _load_proxies(self):
        """Load proxies from .txt config file."""
        if self.config_path.exists():
            loaded_proxies = load_proxies_from_txt(self.config_path)
            
            # Filter out blacklisted proxies
            self.proxies = [
                p for p in loaded_proxies 
                if get_proxy_key(p) not in self.blacklist
            ]
            
            if self.proxies:
                TUI.info(f"Loaded {len(self.proxies)} proxies from {self.config_path}")
            else:
                TUI.warning(f"No proxies available in {self.config_path}")
        else:
            TUI.warning(f"Proxy config file not found: {self.config_path}")
            TUI.info("Using direct connection (no proxies)")
    
    def _save_proxies(self):
        """Save current working proxies to .txt config file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write("# Proxy configuration file\n")
                f.write("# Format: one proxy per line as IP:PORT\n\n")
                for proxy in self.proxies:
                    proxy_key = get_proxy_key(proxy)
                    f.write(f"{proxy_key}\n")
        except Exception as e:
            TUI.warning(f"Failed to save proxies: {e}")
    
    def precheck_proxies(self):
        """Health check all proxies and remove non-functional ones."""
        if self.no_proxy or not self.proxies:
            return
        
        initial_count = len(self.proxies)
        working_proxies = []
        
        TUI.info(f"Health check: Testing {initial_count} proxies...")
        
        for i, proxy in enumerate(self.proxies, 1):
            # Skip blacklisted
            if get_proxy_key(proxy) in self.blacklist:
                TUI.warning(f"Proxy {i} is blacklisted, skipping")
                continue
            
            if health_check_proxy(proxy):
                working_proxies.append(proxy)
            else:
                TUI.warning(f"Proxy {i}/{initial_count} failed health check")
            time.sleep(0.3)  # Rate limiting
        
        self.proxies = working_proxies
        working_count = len(working_proxies)
        
        if working_count < initial_count:
            TUI.info(f"Health check: {working_count}/{initial_count} proxies working")
            # Save only working proxies
            self._save_proxies()
        else:
            TUI.success(f"Health check: {working_count}/{initial_count} proxies working")
    
    def get_proxy(self, skip_rate_limited: bool = True) -> Optional[Dict]:
        """
        Get next proxy in rotation.
        
        Args:
            skip_rate_limited: If True, skip proxies that are in rate-limit cooldown
        
        Returns:
            Proxy dict or None if no proxies available
        """
        if self.no_proxy or not self.proxies:
            return None
        
        # Clean up expired rate-limit cooldowns
        self._cleanup_rate_limited()
        
        # Find next available proxy
        attempts = 0
        while attempts < len(self.proxies):
            proxy = self.proxies[self.current_proxy_index]
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
            
            if skip_rate_limited and self.is_proxy_rate_limited(proxy):
                attempts += 1
                continue
            
            return proxy
        
        # All proxies are rate-limited
        TUI.warning("All proxies are rate-limited")
        return None
    
    def _cleanup_rate_limited(self):
        """Remove expired rate-limit cooldowns."""
        now = time.time()
        expired = [
            key for key, timestamp in self.rate_limited_proxies.items()
            if now - timestamp > self.RATE_LIMIT_COOLDOWN
        ]
        for key in expired:
            del self.rate_limited_proxies[key]
            TUI.info(f"Proxy cooldown expired: {key[:20]}...")
    
    def is_proxy_rate_limited(self, proxy: Dict) -> bool:
        """Check if a proxy is currently in rate-limit cooldown."""
        key = get_proxy_key(proxy)
        if key not in self.rate_limited_proxies:
            return False
        
        # Check if cooldown expired
        elapsed = time.time() - self.rate_limited_proxies[key]
        if elapsed > self.RATE_LIMIT_COOLDOWN:
            del self.rate_limited_proxies[key]
            return False
        
        return True
    
    def mark_proxy_rate_limited(self, proxy: Dict):
        """Mark a proxy as rate-limited (429). Goes into temporary cooldown."""
        key = get_proxy_key(proxy)
        self.rate_limited_proxies[key] = time.time()
        remaining = self.get_available_proxy_count()
        TUI.warning(f"Proxy rate-limited (429), cooldown {self.RATE_LIMIT_COOLDOWN}s ({remaining} proxies available)")
    
    def mark_proxy_failed(self, proxy: Dict, add_to_blacklist_flag: bool = True):
        """
        Mark a proxy as permanently failed.
        
        Args:
            proxy: Proxy dict
            add_to_blacklist_flag: If True, add to persistent blacklist
        """
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            TUI.warning(f"Removed failed proxy from rotation ({len(self.proxies)} remaining)")
            if self.current_proxy_index >= len(self.proxies) and self.proxies:
                self.current_proxy_index = 0
            # Save updated proxy list
            self._save_proxies()
        
        # Add to blacklist
        if add_to_blacklist_flag:
            key = get_proxy_key(proxy)
            self.blacklist.add(key)
            add_to_blacklist(self.blacklist_path, proxy)
            TUI.info(f"Added proxy to blacklist")
    
    def get_available_proxy_count(self) -> int:
        """Get count of proxies not in rate-limit cooldown."""
        self._cleanup_rate_limited()
        return sum(
            1 for p in self.proxies 
            if not self.is_proxy_rate_limited(p)
        )
    
    def has_available_proxies(self) -> bool:
        """Check if there are any proxies available (not rate-limited)."""
        return self.get_available_proxy_count() > 0
    
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
                    TUI.info(f"IP: {ip} ({country})")
                else:
                    TUI.info(f"IP: {ip}")
            else:
                TUI.warning("Could not determine IP address")
