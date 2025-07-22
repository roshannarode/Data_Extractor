#!/usr/bin/env python3
"""
Data Extractor Application
Version 2.0

Main entry point for the Data Extractor application.
This application processes CSV files from different connectors (Tekla, Rhino)
and generates summary reports.

Usage:
    python app.py

Author: Roshan Narode
"""

from gui import DataExtractorGUI

def main():
    """Main function to start the Data Extractor application."""
    try:
        # Create and run the GUI application
        app = DataExtractorGUI()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
    except Exception as e:
        print(f"An error occurred while starting the application: {e}")
        print("Please check that all required dependencies are installed:")
        print("- pandas")
        print("- tkinter (should be included with Python)")

if __name__ == "__main__":
    main() 