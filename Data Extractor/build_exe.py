#!/usr/bin/env python3
"""
Build script for creating executable from Data Extractor application.

This script uses PyInstaller to create a standalone executable with:
- Version information embedded in the exe
- Custom icon
- All necessary dependencies included

Usage:
    python build_exe.py

Requirements:
    pip install pyinstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_pyinstaller():
    """Check if PyInstaller is installed."""
    try:
        import PyInstaller
        print("✅ PyInstaller is available")
        return True
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✅ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install PyInstaller")
            return False

def find_icon():
    """Look for icon file in common locations."""
    icon_names = ["icon.ico", "app_icon.ico", "data_extractor.ico"]
    current_dir = Path(".")
    
    for icon_name in icon_names:
        icon_path = current_dir / icon_name
        if icon_path.exists():
            print(f"✅ Found icon: {icon_path}")
            return str(icon_path)
    
    print("⚠️ No icon file found. Creating a placeholder...")
    print("💡 Place an .ico file named 'icon.ico' in the project directory for a custom icon")
    return None

def build_executable():
    """Build the executable using PyInstaller."""
    print("🔨 Building Data Extractor executable...")
    
    # Check for required files
    if not Path("app.py").exists():
        print("❌ app.py not found!")
        return False
    
    if not Path("version_info.txt").exists():
        print("❌ version_info.txt not found!")
        return False
    
    # Find icon
    icon_path = find_icon()
    
    # Build PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",  # Create a single executable file
        "--windowed",  # Hide console window (for GUI apps)
        "--name=DataExtractor",  # Name of the executable
        "--version-file=version_info.txt",  # Version information
    ]
    
    # Add icon if available
    if icon_path:
        cmd.extend(["--icon", icon_path])
    
    # Add the main script
    cmd.append("app.py")
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build completed successfully!")
        
        # Check if executable was created
        exe_path = Path("dist") / "DataExtractor.exe"
        if exe_path.exists():
            file_size = exe_path.stat().st_size / (1024 * 1024)  # Size in MB
            print(f"✅ Executable created: {exe_path}")
            print(f"📁 Size: {file_size:.1f} MB")
            return True
        else:
            print("❌ Executable not found in dist folder")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print("Error output:", e.stderr)
        return False

def cleanup_build_files():
    """Clean up temporary build files."""
    print("🧹 Cleaning up build files...")
    
    folders_to_remove = ["build", "__pycache__"]
    files_to_remove = ["DataExtractor.spec"]
    
    for folder in folders_to_remove:
        if Path(folder).exists():
            shutil.rmtree(folder)
            print(f"🗑️ Removed {folder}/")
    
    for file in files_to_remove:
        if Path(file).exists():
            Path(file).unlink()
            print(f"🗑️ Removed {file}")

def main():
    """Main build process."""
    print("🚀 Data Extractor Build Process")
    print("=" * 40)
    
    # Check if PyInstaller is available
    if not check_pyinstaller():
        return 1
    
    # Build the executable
    if build_executable():
        print("\n🎉 Build process completed successfully!")
        print(f"📦 Your executable is ready in the 'dist' folder")
        
        # Ask if user wants to clean up
        try:
            clean = input("\n🧹 Clean up build files? (y/N): ").lower().strip()
            if clean in ['y', 'yes']:
                cleanup_build_files()
        except KeyboardInterrupt:
            print("\nBuild process completed.")
        
        return 0
    else:
        print("\n❌ Build process failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 