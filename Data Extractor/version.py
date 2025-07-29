#!/usr/bin/env python3
"""
Central version management for Data Extractor application.

This is the SINGLE SOURCE OF TRUTH for the application version.
Update the version here and all other files will automatically use the new version.

Author: Roshan Narode
"""

# Application version - ONLY change this line to update version everywhere
__version__ = "0.0.0.8"

# Legacy compatibility
APP_VERSION = __version__

def get_version():
    """Get the current application version."""
    return __version__

def get_version_tuple():
    """Get version as tuple (major, minor, patch, build) for version_info.txt."""
    parts = __version__.split('.')
    # Pad with zeros to ensure we have 4 parts
    while len(parts) < 4:
        parts.append('0')
    return tuple(int(part) for part in parts[:4])

if __name__ == "__main__":
    print(f"Data Extractor Version: {__version__}")
    print(f"Version tuple: {get_version_tuple()}") 