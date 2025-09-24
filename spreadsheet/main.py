#!/usr/bin/env python3
"""
Spreadsheet Lite - Main Application Entry Point

A lightweight desktop spreadsheet application built with Python and tkinter.
Features formula evaluation, dependency tracking, undo/redo, and file I/O.
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui import SpreadsheetUI


def main():
    """Main application entry point"""
    try:
        app = SpreadsheetUI()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()