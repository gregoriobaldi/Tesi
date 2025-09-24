#!/usr/bin/env python3
"""
Spreadsheet Lite - Main Entry Point

A desktop spreadsheet application built with PyQt6.
Features formula engine, dependency tracking, and file persistence.
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Apply Qt compatibility fixes first
try:
    from qt_fix import fix_qt_import
    fix_qt_import()
except ImportError:
    pass

from ui import main

if __name__ == "__main__":
    main()