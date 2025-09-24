@echo off
echo Building Spreadsheet Lite...

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Run tests
echo Running tests...
python -m pytest test_*.py -v

REM Build executable
echo Building executable...
pyinstaller spreadsheet.spec

echo Build complete! Executable is in dist/SpreadsheetLite.exe
pause