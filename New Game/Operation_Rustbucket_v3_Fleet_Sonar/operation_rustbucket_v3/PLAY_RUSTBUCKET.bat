@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 operation_rustbucket.py
) else (
    python operation_rustbucket.py
)
if errorlevel 1 (
  echo.
  echo A Python runtime could not start the game.
  echo Install Python from https://www.python.org/downloads/ and enable PATH.
  pause
)
