#!/usr/bin/env python3
"""
Spreadsheet Lite - Tkinter Version
Fallback version using tkinter for PyQt6 compatibility issues.
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui_tkinter import main

if __name__ == "__main__":
    main()