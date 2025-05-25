#!/bin/bash

# Mermaid AI Diagram Generator Startup Script

echo "🚀 Starting Mermaid AI Diagram Generator..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY environment variable is not set."
    echo "   Please set it in your environment or in Streamlit secrets."
    echo "   Example: export OPENAI_API_KEY='your-api-key-here'"
fi

# Start the application
echo "🎨 Starting Streamlit application..."
streamlit run app.py

echo "✅ Application stopped."
