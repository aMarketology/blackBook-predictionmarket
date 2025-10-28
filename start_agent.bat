@echo off
REM BlackBook URL Scraping AI Agent Startup Script

echo ============================================
echo BlackBook URL Scraping AI Agent
echo ============================================
echo.

REM Check if .env exists
if not exist .env (
    echo [WARNING] .env file not found!
    echo Please copy .env.example to .env and add your OPENAI_API_KEY
    echo.
    echo Creating .env from .env.example...
    copy .env.example .env
    echo.
    echo Please edit .env and add your OpenAI API key, then run this script again.
    pause
    exit /b 1
)

REM Check if venv exists
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet
echo.

REM Check if Rust backend is running
echo Checking if blockchain API is running on port 3000...
powershell -Command "$result = Test-NetConnection -ComputerName localhost -Port 3000 -InformationLevel Quiet; if (-not $result) { Write-Host '[WARNING] Blockchain API not detected on port 3000' -ForegroundColor Yellow; Write-Host 'Make sure to start your Rust backend with: cargo run' -ForegroundColor Yellow; Write-Host '' }"

REM Start the agent
echo.
echo Starting URL Scraping AI Agent...
echo.
python serve_frontend.py

pause
