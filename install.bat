@echo off
:: ══════════════════════════════════════════════════════════════
:: Project Janus — Windows Installation Script
:: Sovereign Archival Intelligence
:: ══════════════════════════════════════════════════════════════
setlocal enabledelayedexpansion

title Project Janus — Installation

echo.
echo  ================================================================
echo   Project Janus — Sovereign Archival Intelligence
echo   Windows Installation Script
echo  ================================================================
echo.

:: ─── Check Python ───────────────────────────────────────────
echo [*] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] Python is not installed or not in PATH.
    echo  Please install Python 3.10+ from https://python.org
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo [+] Python %PYTHON_VER% found.

:: ─── Check Python version (3.10+) ──────────────────────────
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VER%") do (
    set PY_MAJOR=%%a
    set PY_MINOR=%%b
)
if %PY_MAJOR% LSS 3 (
    echo [ERROR] Python 3.10+ required. Found: %PYTHON_VER%
    pause
    exit /b 1
)
if %PY_MAJOR% EQU 3 if %PY_MINOR% LSS 10 (
    echo [ERROR] Python 3.10+ required. Found: %PYTHON_VER%
    pause
    exit /b 1
)

:: ─── Create Virtual Environment ────────────────────────────
if not exist ".venv" (
    echo.
    echo [*] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [+] Virtual environment created in .venv/
) else (
    echo [+] Virtual environment already exists.
)

:: ─── Activate Virtual Environment ──────────────────────────
echo [*] Activating virtual environment...
call .venv\Scripts\activate.bat

:: ─── Upgrade pip ────────────────────────────────────────────
echo [*] Upgrading pip...
python -m pip install --upgrade pip --quiet 2>nul

:: ─── Install Requirements ──────────────────────────────────
echo [*] Installing dependencies from requirements.txt...
echo     This may take a few minutes on first install.
echo.
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [WARNING] Some packages may have failed to install.
    echo The setup wizard will identify any missing dependencies.
    echo.
)

:: ─── Launch Setup Wizard ───────────────────────────────────
echo.
echo ================================================================
echo [*] Launching Interactive Setup Wizard...
echo ================================================================
echo.
python scripts/setup_wizard.py

:: ─── Done ───────────────────────────────────────────────────
echo.
echo ================================================================
echo [+] Installation complete!
echo.
echo   Quick launch:    run.bat
echo   Reconfigure:     python scripts/setup_wizard.py --config
echo   Health check:    python scripts/setup_wizard.py --check
echo ================================================================
echo.
pause
