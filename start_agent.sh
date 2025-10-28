#!/bin/bash
# BlackBook URL Scraping AI Agent Startup Script

echo "============================================"
echo "BlackBook URL Scraping AI Agent"
echo "============================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "[WARNING] .env file not found!"
    echo "Please copy .env.example to .env and add your OPENAI_API_KEY"
    echo ""
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "Please edit .env and add your OpenAI API key, then run this script again."
    exit 1
fi

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet
echo ""

# Check if Rust backend is running
echo "Checking if blockchain API is running on port 3000..."
if ! nc -z localhost 3000 2>/dev/null; then
    echo "[WARNING] Blockchain API not detected on port 3000"
    echo "Make sure to start your Rust backend with: cargo run"
    echo ""
fi

# Start the agent
echo ""
echo "Starting URL Scraping AI Agent..."
echo ""
python serve_frontend.py
