@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ========================================
echo   Power Trading Pipeline - Data Runner
echo ========================================
echo.

uv run python run.py

echo.
set /p choice="Launch dashboard? (Y/N): "
if /i "%choice%"=="Y" (
    uv run streamlit run dashboard.py
)

pause
