"""Simple logging utility for debug messages."""

import sys
from typing import Any


class Logger:
    """Simple logger for debug messages."""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def debug_log(self, message: str, *args: Any) -> None:
        """Print debug message if debug mode is enabled."""
        if self.debug:
            if args:
                message = message.format(*args)
            print(f"[DEBUG] {message}", file=sys.stderr)
    
    def error(self, message: str, *args: Any) -> None:
        """Print error message."""
        if args:
            message = message.format(*args)
        print(f"[ERROR] {message}", file=sys.stderr)
    
    def info(self, message: str, *args: Any) -> None:
        """Print info message."""
        if args:
            message = message.format(*args)
        print(f"[INFO] {message}", file=sys.stderr)