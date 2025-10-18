@echo off
REM BlackBook Prediction Market Startup Script for Windows

echo 🔮 Starting BlackBook Prediction Market...
echo ================================================

REM Check if .env exists, if not copy from example
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ⚠️  Please edit .env file with your configuration before continuing
    echo    - Set your blockchain URL (default: http://localhost:8545)
    echo    - Configure your database settings
    echo    - Set your private keys and secrets
    echo.
    pause
)

REM Check if Rust is installed
cargo --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Rust/Cargo not found. Please install Rust from https://rustup.rs/
    pause
    exit /b 1
)

echo 🔧 Installing dependencies...
cargo build --release

if %errorlevel% equ 0 (
    echo ✅ Build successful!
    echo.
    echo 🚀 Starting BlackBook Prediction Market server...
    echo    Server will be available at: http://localhost:3000
    echo    API endpoints at: http://localhost:3000/api/v1
    echo    Health check: http://localhost:3000/health
    echo.
    echo 📋 Make sure your local blockchain is running on the configured URL
    echo    (Ganache, Hardhat, or similar on http://localhost:8545)
    echo.
    echo 🛑 Press Ctrl+C to stop the server
    echo ================================================
    echo.
    
    cargo run --release
) else (
    echo ❌ Build failed. Please check the errors above.
    pause
    exit /b 1
)