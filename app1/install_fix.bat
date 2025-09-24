@echo off
echo Fixing PyQt6 installation...

REM Uninstall existing PyQt6
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip -y

REM Clear pip cache
pip cache purge

REM Install compatible version
pip install PyQt6==6.4.2

echo PyQt6 installation fixed!
pause