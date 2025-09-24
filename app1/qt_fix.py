"""Qt compatibility fixes for Windows DLL issues."""

import sys
import os

def fix_qt_import():
    """Fix PyQt6 import issues on Windows."""
    try:
        # Try to fix DLL path issues
        if sys.platform == "win32":
            # Add Qt DLL path to environment
            import PyQt6
            qt_path = os.path.dirname(PyQt6.__file__)
            qt_bin_path = os.path.join(qt_path, "Qt6", "bin")
            if os.path.exists(qt_bin_path):
                os.environ["PATH"] = qt_bin_path + os.pathsep + os.environ.get("PATH", "")
    except ImportError:
        pass

# Apply fix before any Qt imports
fix_qt_import()