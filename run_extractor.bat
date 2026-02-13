@echo off
setlocal

echo eBook Image Extractor
echo =====================
echo Supports: EPUB, MOBI, AZW, AZW3
echo.

set "PYTHON_CMD=python"
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"
)

%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found: %PYTHON_VERSION%

echo Checking dependencies...
%PYTHON_CMD% -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

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

%PYTHON_CMD% "%~dp0main.py" extract "%~dp0" --recursive --format auto --manifest

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
endlocal
