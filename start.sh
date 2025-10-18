#!/bin/bash

# BlackBook Prediction Market Startup Script

echo "🔮 Starting BlackBook Prediction Market..."
echo "================================================"

# Check if .env exists, if not copy from example
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before continuing"
    echo "   - Set your blockchain URL (default: http://localhost:8545)"
    echo "   - Configure your database settings"
    echo "   - Set your private keys and secrets"
    echo ""
    read -p "Press Enter to continue after editing .env file..."
fi

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo "❌ Rust/Cargo not found. Please install Rust from https://rustup.rs/"
    exit 1
fi

echo "🔧 Installing dependencies..."
cargo build --release

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo ""
    echo "🚀 Starting BlackBook Prediction Market server..."
    echo "   Server will be available at: http://localhost:3000"
    echo "   API endpoints at: http://localhost:3000/api/v1"
    echo "   Health check: http://localhost:3000/health"
    echo ""
    echo "📋 Make sure your local blockchain is running on the configured URL"
    echo "   (Ganache, Hardhat, or similar on http://localhost:8545)"
    echo ""
    echo "🛑 Press Ctrl+C to stop the server"
    echo "================================================"
    echo ""
    
    cargo run --release
else
    echo "❌ Build failed. Please check the errors above."
    exit 1
fi