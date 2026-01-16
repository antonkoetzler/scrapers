"""Simple Color TUI API for terminal output."""
import sys
from colorama import init, Fore, Style

# Initialize colorama for Windows compatibility
init(autoreset=True)

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        # Python < 3.7 or reconfigure failed
        pass

# Terminal User Interface.
class TUI:
    """Simple Terminal User Interface with color support."""
    
    @staticmethod
    def success(message: str) -> None:
        """Print success message in green to stderr."""
        print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}", file=sys.stderr)
    
    @staticmethod
    def error(message: str) -> None:
        """Print error message in red to stderr."""
        print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}", file=sys.stderr)
    
    @staticmethod
    def warning(message: str) -> None:
        """Print warning message in yellow to stderr."""
        print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}", file=sys.stderr)
    
    @staticmethod
    def info(message: str) -> None:
        """Print info message in cyan to stderr."""
        print(f"{Fore.CYAN}ℹ {message}{Style.RESET_ALL}", file=sys.stderr)
    
    @staticmethod
    def header(message: str) -> None:
        """Print header message in bold to stderr."""
        print(f"{Style.BRIGHT}{message}{Style.RESET_ALL}", file=sys.stderr)
    
    @staticmethod
    def print(message: str, color: str = None) -> None:
        """Print message with optional color to stderr."""
        if color == "green":
            print(f"{Fore.GREEN}{message}{Style.RESET_ALL}", file=sys.stderr)
        elif color == "red":
            print(f"{Fore.RED}{message}{Style.RESET_ALL}", file=sys.stderr)
        elif color == "yellow":
            print(f"{Fore.YELLOW}{message}{Style.RESET_ALL}", file=sys.stderr)
        elif color == "cyan":
            print(f"{Fore.CYAN}{message}{Style.RESET_ALL}", file=sys.stderr)
        elif color == "blue":
            print(f"{Fore.BLUE}{message}{Style.RESET_ALL}", file=sys.stderr)
        else:
            print(message, file=sys.stderr)

