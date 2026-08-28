@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title Saint Demiana Monastery - Retreat System Live

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" run_live.py
) else (
    python run_live.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ====================================================================
    echo [!] An error occurred while running the application.
    echo ====================================================================
)
pause


