@echo off
REM BlackBook Event Feed Service startup script for Windows

echo.
echo 🏆 BlackBook Event Feed Service
echo 📍 Starting on http://localhost:8000
echo.

REM Install dependencies using UV
echo Installing dependencies with uv...
uv pip install -r requirements.txt

REM Start the service
echo.
echo Starting FastAPI event service...
echo Press Ctrl+C to stop
echo.

uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload

pause
