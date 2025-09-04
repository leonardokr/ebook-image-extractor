@echo off
REM Script to run EPUB Image Extractor on Windows
REM Place this file in the folder where your EPUBs are located

echo EPUB Image Extractor
echo ==================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+ first.
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import bs4, lxml" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install beautifulsoup4 lxml
)

REM Run the extractor
python "%~dp0main.py" "%~dp0"

echo.
echo Extraction completed! Press any key to exit...
pause >nul
