# Folder Structure

## `shared/`

Reusable utilities and modules used across all scrapers.

- `scraper_utils.py` - Session creation with Cloudflare bypass and proxy support
- `proxy_manager.py` - Proxy rotation and IP tracking
- `tui.py` - Terminal UI with color output
- `route_discovery.py` - API endpoint discovery tool

## `sportsbooks/`

Sportsbook-specific scrapers.

- `betano.py` - Betano API scraper

Each scraper outputs data in the standardized format defined in `WhatIOutta.md`.

## `docs/`

Documentation for specific functionality.

- `proxy-setup.md` - Proxy configuration
- `betano-scraper.md` - Betano scraper usage
- `route-discovery.md` - Route discovery tool
- `folder-structure.md` - This file

