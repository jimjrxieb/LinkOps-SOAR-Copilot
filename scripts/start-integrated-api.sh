#!/bin/bash
cd "$(dirname "$0")/.."
export WHIS_ENV=production
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "🚀 Starting WHIS Integrated API Server..."
python3 apps/api/whis_integrated_server.py \
    > logs/whis-integrated-api.log 2>&1 &

API_PID=$!
echo $API_PID > logs/whis-integrated-api.pid
echo "✅ WHIS Integrated API server started (PID: $API_PID)"
echo "🌐 Full WHIS Dashboard: http://localhost:8000"
echo "💬 Interactive Chat Interface: http://localhost:8000"
echo "📊 System Health: http://localhost:8000/health"
echo "🎯 Threat Hunting: http://localhost:8000/threat-hunt"
echo "🚨 Incident Management: http://localhost:8000/incident"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "📈 Live Metrics: http://localhost:8000/metrics"