@echo off
REM Script to run eBook Image Extractor on Windows
REM Supports EPUB and MOBI/AZW files
REM Place this file in the folder where your eBooks are located

echo eBook Image Extractor
echo =====================
echo Supports: EPUB, MOBI, AZW, AZW3
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Display Python version
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found: %PYTHON_VERSION%

REM Check if dependencies are installed
echo Checking dependencies...
python -c "import bs4" >nul 2>&1
if errorlevel 1 (
    echo Installing BeautifulSoup4 for EPUB support...
    pip install beautifulsoup4
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies.
        pause
        exit /b 1
    )
)

REM Check for available eBook files
echo.
echo Scanning for eBook files...
set FOUND_FILES=0

for %%f in (*.epub) do (
    set FOUND_FILES=1
    goto :found
)
for %%f in (*.mobi) do (
    set FOUND_FILES=1
    goto :found
)
for %%f in (*.azw) do (
    set FOUND_FILES=1
    goto :found
)
for %%f in (*.azw3) do (
    set FOUND_FILES=1
    goto :found
)

:found
if %FOUND_FILES%==0 (
    echo WARNING: No eBook files found in current directory.
    echo Supported formats: .epub, .mobi, .azw, .azw3
    echo.
    echo Continuing anyway...
)

echo.
echo Starting extraction...
echo =====================

REM Run the extractor
python "%~dp0main.py" "%~dp0"

REM Check if extraction was successful
if errorlevel 1 (
    echo.
    echo ERROR: Extraction failed. Check the error messages above.
) else (
    echo.
    echo SUCCESS: Image extraction completed!
    echo Check the folders created in this directory.
)

echo.
echo Press any key to exit...
pause >nul