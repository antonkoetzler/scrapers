# Web Scrapers

Collection of web scrapers for sports betting data with anti-scraping measures and proxy support.

## Overview

This repository contains scrapers for various sportsbooks, designed to collect fixtures, odds, and scores for betting prediction systems. All scrapers include Cloudflare bypass, proxy rotation, and IP geolocation tracking.

## Structure

- `shared/` - Reusable utilities (proxy management, TUI, scraper utils)
- `sportsbooks/` - Sportsbook-specific scrapers (Betano, etc.)
- `sports_data/` - Sports data sources (Flashscore, Livescore, etc.)
- `docs/` - Detailed documentation for specific functionality

## Quick Start

1. Set up virtual environment (recommended):

```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

See [docs/setup.md](docs/setup.md) for detailed setup instructions.

1. Install dependencies:

```bash
pip install -r requirements.txt
```

1. Configure proxies (optional):

```bash
cp proxy_config.json.example proxy_config.json
# Edit proxy_config.json with your proxies
```

1. Run a scraper:

```bash
python sportsbooks/betano.py
```

## Documentation

- [WhatIOutta.md](WhatIOutta.md) - Scraper requirements and data format specifications
- [docs/proxy-setup.md](docs/proxy-setup.md) - Proxy configuration guide
- [docs/betano-scraper.md](docs/betano-scraper.md) - Betano scraper documentation
- [docs/route-discovery.md](docs/route-discovery.md) - API route discovery tool
- [docs/folder-structure.md](docs/folder-structure.md) - Project folder structure

## Features

- ✅ Cloudflare bypass (cloudscraper)
- ✅ Proxy rotation and management
- ✅ IP geolocation tracking
- ✅ Retry logic with exponential backoff
- ✅ Color-coded terminal output (TUI)
- ✅ API route discovery tools

## Free Proxy Sources

- **ProxyScrape**: <https://proxyscrape.com/free-proxy-list>
- **GeoNode**: <https://geonode.com/free-proxy-list>
- **Free Proxy List**: <https://free-proxy-list.net/>
- **Proxy List**: <https://www.proxy-list.download/>

Note: Free proxies are often unreliable. For production use, consider paid proxy services.
