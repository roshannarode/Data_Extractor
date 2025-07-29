#!/usr/bin/env python3
"""
Script to automatically update version_info.txt based on the central version.

This script reads the version from version.py and updates all version references
in version_info.txt to match. Run this script whenever you change the version.

Usage:
    python update_version_info.py
    
Author: Roshan Narode
"""

import os
import sys
from pathlib import Path

def update_version_info():
    """Update version_info.txt to match the central version."""
    
    # Import version from central location
    try:
        from version import __version__, get_version_tuple
    except ImportError:
        print("❌ Could not import version from version.py")
        return False
    
    version_info_path = Path("version_info.txt")
    
    if not version_info_path.exists():
        print("❌ version_info.txt not found!")
        return False
    
    # Read current version_info.txt
    try:
        with open(version_info_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading version_info.txt: {e}")
        return False
    
    # Get version tuple for filevers and prodvers
    version_tuple = get_version_tuple()
    filevers_str = f"({version_tuple[0]},{version_tuple[1]},{version_tuple[2]},{version_tuple[3]})"
    
    print(f"🔄 Updating version_info.txt...")
    print(f"   Version: {__version__}")
    print(f"   Tuple: {version_tuple}")
    
    # Update all version references
    # Update filevers and prodvers tuples
    import re
    
    # Replace filevers=(0,0,0,7) with current version
    content = re.sub(
        r'filevers=\([0-9,\s]+\)',
        f'filevers={filevers_str}',
        content
    )
    
    # Replace prodvers=(0,0,6,0) with current version  
    content = re.sub(
        r'prodvers=\([0-9,\s]+\)',
        f'prodvers={filevers_str}',
        content
    )
    
    # Replace FileVersion string
    content = re.sub(
        r"StringStruct\(u'FileVersion',\s*u'[^']+'\)",
        f"StringStruct(u'FileVersion', u'{__version__}')",
        content
    )
    
    # Replace ProductVersion string
    content = re.sub(
        r"StringStruct\(u'ProductVersion',\s*u'[^']+'\)",
        f"StringStruct(u'ProductVersion', u'{__version__}')",
        content
    )
    
    # Write updated content back to file
    try:
        with open(version_info_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ version_info.txt updated successfully!")
        return True
    except Exception as e:
        print(f"❌ Error writing version_info.txt: {e}")
        return False

def main():
    """Main function."""
    print("🔄 Data Extractor - Version Info Updater")
    print("=" * 40)
    
    if update_version_info():
        print("\n🎉 Version info updated successfully!")
        print("💡 You can now build the executable with the updated version.")
    else:
        print("\n❌ Failed to update version info.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 