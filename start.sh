#!/bin/bash
# start.sh — Bot va API ni birgalikda ishga tushirish

echo "🚀 KategoryBot ishga tushmoqda..."

# Bot ishga tushirish (background)
cd bot && python main.py &
BOT_PID=$!
echo "✅ Bot ishga tushdi (PID: $BOT_PID)"

# API ishga tushirish
cd ..
uvicorn api:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!
echo "✅ API ishga tushdi (PID: $API_PID)"

echo "📡 API: http://localhost:8000"
echo "🌐 WebApp: http://localhost:8000"
echo "⚙️  Admin: http://localhost:8000/admin.html"

wait
