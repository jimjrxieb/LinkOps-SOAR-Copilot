#!/bin/bash

# Whis Frontend Deployment Script
echo "🚀 Starting Whis Frontend..."

# Set environment variables if not already set
export FLASK_SECRET_KEY=${FLASK_SECRET_KEY:-$(python3 -c "import secrets; print(secrets.token_hex(32))")}
export WHIS_API_URL=${WHIS_API_URL:-"http://localhost:8003"}
export LIMACHARLIE_API_KEY=${LIMACHARLIE_API_KEY:-""}
export LIMACHARLIE_ORG=${LIMACHARLIE_ORG:-""}
export SPLUNK_HOST=${SPLUNK_HOST:-""}
export SPLUNK_USERNAME=${SPLUNK_USERNAME:-""}
export SPLUNK_PASSWORD=${SPLUNK_PASSWORD:-""}

echo "📋 Configuration:"
echo "  • Whis API: $WHIS_API_URL"
echo "  • LimaCharlie: $([ -n "$LIMACHARLIE_API_KEY" ] && echo "✅ Configured" || echo "❌ Not configured")"
echo "  • Splunk: $([ -n "$SPLUNK_HOST" ] && echo "✅ Configured" || echo "❌ Not configured")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create static directories if they don't exist
mkdir -p static/css static/js static/img

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "
import sys
sys.path.append('.')
from app import init_db
init_db()
print('Database initialized successfully')
"

# Run the application
echo "🌐 Starting Whis Frontend on http://localhost:5000"
echo "🔐 Default login: any username/password combination"
echo "📊 Press Ctrl+C to stop"
echo ""

# Start with gunicorn for production or flask for development
if [ "$1" = "prod" ]; then
    echo "🏭 Starting in production mode..."
    gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
else
    echo "🔧 Starting in development mode..."
    python3 app.py
fi