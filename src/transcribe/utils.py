"""Utility functions for transcribe module."""

import os
import sys
import contextlib


@contextlib.contextmanager
def suppress_alsa_warnings():
    """Context manager to suppress ALSA warnings from PyAudio."""
    # Save the original stderr
    old_stderr = os.dup(2)
    
    try:
        # Redirect stderr to /dev/null
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, 2)
        os.close(devnull)
        
        yield
        
    finally:
        # Restore stderr
        os.dup2(old_stderr, 2)
        os.close(old_stderr)