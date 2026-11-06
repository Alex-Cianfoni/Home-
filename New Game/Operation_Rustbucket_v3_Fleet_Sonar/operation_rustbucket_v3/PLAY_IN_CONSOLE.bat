@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 operation_rustbucket.py --console
) else (
    python operation_rustbucket.py --console
)
pause
