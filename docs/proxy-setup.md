# Proxy Setup

## Configuration

Proxies can be configured via `proxy_config.json`:

```json
{
  "proxies": [
    {
      "http": "http://proxy.example.com:8080",
      "https": "http://proxy.example.com:8080"
    }
  ]
}
```

## Usage

### Automatic Proxy Fetching

If no config file exists, the system attempts to fetch free proxies from public APIs. This is unreliable and not recommended for production.

### Disable Proxies

Use `--no-proxy` flag:

```bash
python sportsbooks/betano.py --no-proxy
```

### Proxy Rotation

Proxies are rotated automatically on each request. The system tracks IP changes and logs them.

## IP Logging

The system logs IP address and country when:

- First request is made
- IP address changes

Log format: `IP changed: <ip> (<country>)`
