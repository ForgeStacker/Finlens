#!/bin/bash

# Browser auto-opener for Docker mode
# This script detects when both services are ready and opens the browser

echo "🌐 Waiting for FinLens to be ready..."

# Wait for services to be healthy
while ! curl -s http://localhost:8083/api/discovery > /dev/null 2>&1 || ! curl -s http://localhost:5173 > /dev/null 2>&1; do
    echo "⏳ Services starting up..."
    sleep 2
done

echo "✅ FinLens is ready!"
echo "🌐 Opening browser at http://localhost:5173"

# Open browser
if command -v xdg-open >/dev/null 2>&1; then
    xdg-open http://localhost:5173
elif command -v open >/dev/null 2>&1; then
    open http://localhost:5173
elif command -v start >/dev/null 2>&1; then
    start http://localhost:5173
else
    echo "Please open your browser manually and go to: http://localhost:5173"
fi