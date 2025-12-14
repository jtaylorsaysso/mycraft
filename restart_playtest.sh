#!/bin/bash

# restart_playtest.sh
# Quickly restart server and clients for MyCraft playtesting

# Default to 1 client
CLIENTS=1

# Determine Python interpreter
PYTHON="python3"
if [ -f "./venv/bin/python" ]; then
    PYTHON="./venv/bin/python"
elif [ -f "./venv/bin/python3" ]; then
    PYTHON="./venv/bin/python3"
fi

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --clients) CLIENTS="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

echo "🛑 Stopping existing MyCraft processes..."
pkill -f "run_server.py"
pkill -f "run_client.py"
# Wait a moment for ports to free up
sleep 1

echo "🚀 Starting Server..."
$PYTHON run_server.py > logs/server_latest.log 2>&1 &
SERVER_PID=$!

# Wait for server to initialize
echo "Waiting for server to be ready..."
sleep 2

# Check if server is still running
if ! ps -p $SERVER_PID > /dev/null; then
    echo "❌ Server failed to start! Check logs/server_latest.log"
    exit 1
fi

echo "🎮 Starting $CLIENTS Client(s)..."
for (( i=1; i<=CLIENTS; i++ ))
do
    echo "  - Launching Client $i..."
    $PYTHON run_client.py --host localhost > logs/client_${i}_latest.log 2>&1 &
    # Stagger starts slightly to prevent race conditions in resource loading
    sleep 1
done

echo "✅ Playtest session started with 1 Server and $CLIENTS Client(s)!"
echo "   Server PID: $SERVER_PID"
echo "   Logs available in logs/"
