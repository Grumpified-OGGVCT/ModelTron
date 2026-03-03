@echo off
:: ══════════════════════════════════════════════════════════════
:: Project Janus — Quick Launch (Windows)
:: Activates venv, runs health check, launches demo page
:: ══════════════════════════════════════════════════════════════
setlocal

title Project Janus — Launch

:: ─── Check venv exists ──────────────────────────────────────
if not exist ".venv\Scripts\activate.bat" (
    echo.
    echo  [!] Virtual environment not found.
    echo  Please run install.bat first.
    echo.
    pause
    exit /b 1
)

:: ─── Activate venv ──────────────────────────────────────────
call .venv\Scripts\activate.bat

:: ─── Quick Check and Launch ─────────────────────────────────
python scripts/setup_wizard.py --check

:: ─── Deactivate ─────────────────────────────────────────────
deactivate 2>nul
