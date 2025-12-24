#!/bin/bash
# 🚀 Quick Setup Script for BlackBook URL Scraper
# Run this if you need to reinstall dependencies

echo "============================================"
echo "BlackBook URL Scraper - Installation"
echo "============================================"
echo ""

# Check Python version
echo "📍 Step 1: Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 not found. Please install Python 3.8+ first."
    exit 1
fi
echo "✅ Python is installed"
echo ""

# Install/upgrade pip
echo "📍 Step 2: Upgrading pip..."
python3 -m pip install --upgrade pip
echo ""

# Install dependencies
echo "📍 Step 3: Installing dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo "✅ All dependencies installed"
echo ""

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📍 Step 4: Creating .env file..."
    cp .env.example .env 2>/dev/null || echo "# Environment variables" > .env
    echo "BLOCKCHAIN_API_URL=http://localhost:3000" >> .env
    echo "AGENT_PORT=8082" >> .env
    echo "ALLOW_CREATE_MARKET=1" >> .env
    echo "✅ .env file created"
else
    echo "📍 Step 4: .env file already exists"
fi
echo ""

# Create logs directory
echo "📍 Step 5: Creating logs directory..."
mkdir -p logs
echo "✅ Logs directory ready"
echo ""

# Test the installation
echo "📍 Step 6: Testing installation..."
echo "Running test scrape with mock AI..."
python3 serve_frontend.py --url "https://example.com" --ai-mock > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Installation test passed!"
else
    echo "⚠️  Installation test had issues (this might be ok if example.com is blocked)"
fi
echo ""

echo "============================================"
echo "✅ Installation Complete!"
echo "============================================"
echo ""
echo "🎯 Quick Start Commands:"
echo ""
echo "  # Scrape a URL with mock AI:"
echo "  python3 serve_frontend.py --url 'https://yoursite.com' --ai-mock"
echo ""
echo "  # Scrape and post to blockchain:"
echo "  python3 serve_frontend.py --url 'https://yoursite.com' --create-market --enable-blockchain"
echo ""
echo "  # Test blockchain connection:"
echo "  python3 serve_frontend.py --test-blockchain"
echo ""
echo "📚 See INSTALL_GUIDE.md for more details"
echo ""
