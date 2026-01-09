# Route Discovery Tool

Discovers available API endpoints by testing common route patterns.

## Usage

```bash
python shared/route_discovery.py <url> [options]
```

## Options

- `--wordlist <file>` - Custom wordlist file
- `--recursive, -r` - Recursive discovery
- `--depth <n>` - Max depth for recursive discovery
- `--delay <seconds>` - Delay between requests
- `--no-proxy` - Disable proxy usage

## Examples

```bash
# Basic discovery
python shared/route_discovery.py "https://api.example.com/"

# Recursive discovery
python shared/route_discovery.py "https://api.example.com/" --recursive --depth 3
```

## Output

Results are printed to console. Valid routes are highlighted.

