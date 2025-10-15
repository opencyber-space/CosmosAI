#!/bin/bash

# Block Metrics Monitor - Streamlit Dashboard Launcher
# This script sets up and runs the Streamlit dashboard for monitoring block metrics

echo "🚀 Starting Block Metrics Monitor Dashboard..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 first."
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

# Install requirements if needed
echo "📦 Installing dependencies..."
pip3 install -r requirements_streamlit.txt

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit installation failed. Please check the requirements."
    exit 1
fi

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo "❌ config.yaml not found. Please ensure config.yaml is in the current directory."
    exit 1
fi

echo "✅ All dependencies are ready."
echo "🌐 Starting Streamlit dashboard..."
echo "📊 Dashboard will be available at: http://localhost:8501"
echo ""
echo "To access from other machines, use:"
echo "streamlit run streamlit_monitor.py --server.address 0.0.0.0 --server.port 8501"
echo ""

# Start the Streamlit application
streamlit run streamlit_monitor.py
