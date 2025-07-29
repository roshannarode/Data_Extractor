#!/usr/bin/env python3
"""
Build script for creating executable from Data Extractor application.

This script uses PyInstaller to create a standalone executable with:
- Version information embedded in the exe
- Custom icon
- All necessary dependencies included
- Optional digital signing

Usage:
    python build_exe.py
    python build_exe.py --sign  # Build and sign with certificate

Requirements:
    pip install pyinstaller
    Windows SDK (for signtool.exe)
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import argparse

# Import version from data_processor
try:
    from data_processor import APP_VERSION
except ImportError:
    # Fallback if import fails
    APP_VERSION = "0.0.6"
    print(f"⚠️ Could not import version, using fallback: {APP_VERSION}")

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

def find_signtool():
    """Find signtool.exe from Windows SDK."""
    possible_paths = [
        r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe",  # Found path
        r"C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe",
        r"C:\Program Files (x86)\Windows Kits\10\bin\x86\signtool.exe",
        r"C:\Program Files\Microsoft SDKs\Windows\v7.1\Bin\signtool.exe",
        r"C:\Program Files (x86)\Microsoft SDKs\Windows\v7.1A\Bin\signtool.exe"
    ]
    
    for path in possible_paths:
        if Path(path).exists():
            print(f"✅ Found signtool: {path}")
            return path
    
    # Try to find in PATH
    try:
        result = subprocess.run(['where', 'signtool'], capture_output=True, text=True, check=True)
        signtool_path = result.stdout.strip().split('\n')[0]
        print(f"✅ Found signtool in PATH: {signtool_path}")
        return signtool_path
    except subprocess.CalledProcessError:
        pass
    
    print("❌ signtool.exe not found!")
    print("💡 Install Windows SDK from: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/")
    return None

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

def sign_executable(exe_path, signtool_path):
    """Sign the executable with digital certificate."""
    print(f"🔐 Signing executable: {exe_path}")
    
    # Check for certificate file
    cert_files = list(Path(".").glob("*.pfx")) + list(Path(".").glob("*.p12"))
    
    if cert_files:
        # Use certificate file
        cert_file = cert_files[0]
        print(f"📜 Using certificate file: {cert_file}")
        
        # Prompt for password
        try:
            password = input("🔑 Enter certificate password (or press Enter to skip): ").strip()
            if not password:
                print("⚠️ No password provided, skipping signing")
                return False
        except KeyboardInterrupt:
            print("\n⚠️ Signing cancelled")
            return False
        
        # Sign with certificate file
        cmd = [
            signtool_path,
            "sign",
            "/f", str(cert_file),
            "/p", password,
            "/t", "http://timestamp.digicert.com",  # Timestamp server
            "/fd", "SHA256",  # Hash algorithm
            "/v",  # Verbose
            str(exe_path)
        ]
    else:
        # Use certificate from store
        print("📜 No certificate file found, attempting to use certificate store")
        print("💡 List available certificates: certmgr.msc")
        
        try:
            cert_name = input("🔑 Enter certificate subject name (or press Enter to skip): ").strip()
            if not cert_name:
                print("⚠️ No certificate name provided, skipping signing")
                return False
        except KeyboardInterrupt:
            print("\n⚠️ Signing cancelled")
            return False
        
        # Sign with certificate store
        cmd = [
            signtool_path,
            "sign",
            "/n", cert_name,
            "/t", "http://timestamp.digicert.com",  # Timestamp server
            "/fd", "SHA256",  # Hash algorithm
            "/v",  # Verbose
            str(exe_path)
        ]
    
    try:
        print(f"Running: {' '.join(cmd[:6])} [hidden password/cert info]")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Executable signed successfully!")
        print("🔐 Digital signature added")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Signing failed: {e}")
        print("Error output:", e.stderr)
        return False

def verify_signature(exe_path, signtool_path):
    """Verify the digital signature of the executable."""
    print(f"🔍 Verifying signature: {exe_path}")
    
    cmd = [signtool_path, "verify", "/pa", "/v", str(exe_path)]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Signature verification successful!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Signature verification failed: {e}")
        return False

def build_executable():
    """Build the executable using PyInstaller."""
    print(f"🔨 Building Data Extractor v{APP_VERSION} executable...")
    
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
        f"--name=Data Extractor v{APP_VERSION}",  # Name of the executable with version
        "--version-file=version_info.txt",  # Version information
    ]
    
    # Add icon if available
    if icon_path:
        cmd.extend(["--icon", icon_path])
        # Also add icon as data file so GUI can access it at runtime
        cmd.extend(["--add-data", f"{icon_path};."])
    
    # Add the main script
    cmd.append("app.py")
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build completed successfully!")
        
        # Check if executable was created
        exe_path = Path("dist") / f"Data Extractor v{APP_VERSION}.exe"
        if exe_path.exists():
            file_size = exe_path.stat().st_size / (1024 * 1024)  # Size in MB
            print(f"✅ Executable created: {exe_path}")
            print(f"📁 Size: {file_size:.1f} MB")
            return str(exe_path)
        else:
            print("❌ Executable not found in dist folder")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print("Error output:", e.stderr)
        return None

def cleanup_build_files():
    """Clean up temporary build files."""
    print("🧹 Cleaning up build files...")
    
    folders_to_remove = ["build", "__pycache__"]
    files_to_remove = [f"Data Extractor v{APP_VERSION}.spec"]
    
    for folder in folders_to_remove:
        if Path(folder).exists():
            shutil.rmtree(folder)
            print(f"🗑️ Removed {folder}/")
    
    for file in files_to_remove:
        if Path(file).exists():
            Path(file).unlink()
            print(f"🗑️ Removed {file}")

def show_signing_help():
    """Show help information for code signing setup."""
    print("\n" + "="*60)
    print("🔐 CODE SIGNING SETUP GUIDE")
    print("="*60)
    print()
    print("Option 1: Certificate File (.pfx/.p12)")
    print("  1. Place your .pfx or .p12 certificate file in project folder")
    print("  2. Run: python build_exe.py --sign")
    print("  3. Enter certificate password when prompted")
    print()
    print("Option 2: Certificate Store")
    print("  1. Install certificate in Windows certificate store")
    print("  2. Run: python build_exe.py --sign")
    print("  3. Enter certificate subject name when prompted")
    print()
    print("Option 3: Self-Signed Certificate (Testing)")
    print("  1. Create self-signed cert:")
    print("     makecert -sv mykey.pvk -n \"CN=YourName\" mycert.cer")
    print("     pvk2pfx -pvk mykey.pvk -spc mycert.cer -pfx mycert.pfx")
    print("  2. Place mycert.pfx in project folder")
    print()
    print("💡 Professional certificates: DigiCert, Sectigo, GlobalSign")
    print("💡 Windows SDK required for signtool.exe")
    print()

def main():
    """Main build process."""
    parser = argparse.ArgumentParser(description="Build Data Extractor executable")
    parser.add_argument("--sign", action="store_true", help="Sign the executable with digital certificate")
    parser.add_argument("--help-signing", action="store_true", help="Show code signing setup guide")
    
    args = parser.parse_args()
    
    if args.help_signing:
        show_signing_help()
        return 0
    
    print(f"🚀 Data Extractor v{APP_VERSION} Build Process")
    print("=" * 50)
    
    # Check if PyInstaller is available
    if not check_pyinstaller():
        return 1
    
    # Build the executable
    exe_path = build_executable()
    if not exe_path:
        print("\n❌ Build process failed!")
        return 1
    
    # Sign the executable if requested
    if args.sign:
        signtool_path = find_signtool()
        if signtool_path:
            if sign_executable(exe_path, signtool_path):
                verify_signature(exe_path, signtool_path)
            else:
                print("⚠️ Signing failed, but executable is still usable")
        else:
            print("⚠️ Cannot sign - signtool.exe not found")
            show_signing_help()
    
    print("\n🎉 Build process completed successfully!")
    print(f"📦 Your executable is ready: {exe_path}")
    
    if args.sign:
        print("🔐 Digital signature applied")
    else:
        print("💡 Use --sign flag to add digital signature")
    
    # Ask if user wants to clean up
    try:
        clean = input("\n🧹 Clean up build files? (y/N): ").lower().strip()
        if clean in ['y', 'yes']:
            cleanup_build_files()
    except KeyboardInterrupt:
        print("\nBuild process completed.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 