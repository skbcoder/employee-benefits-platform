#!/usr/bin/env bash
set -euo pipefail

# AI Platform Local Runner
# Starts all three AI services in the background.
# Prerequisites: Run setup.sh first.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AI_PLATFORM_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Starting AI Platform ==="
echo ""

# Check that venvs exist
for SERVICE in mcp-server ai-gateway knowledge-service; do
    if [ ! -d "$AI_PLATFORM_DIR/$SERVICE/.venv" ]; then
        echo "ERROR: Virtual environment not found for $SERVICE."
        echo "Run ./scripts/setup.sh first."
        exit 1
    fi
done

# Check Ollama is running
if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
    echo "WARNING: Ollama does not appear to be running on localhost:11434."
    echo "Start Ollama before using the AI Gateway or Knowledge Service."
    echo ""
fi

# Trap to kill background processes on exit
PIDS=()
cleanup() {
    echo ""
    echo "Shutting down AI Platform services..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null
    echo "Done."
}
trap cleanup EXIT INT TERM

# Start MCP Server
echo "Starting MCP Server on port 8100..."
cd "$AI_PLATFORM_DIR/mcp-server"
.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8100 --reload &
PIDS+=($!)

# Start Knowledge Service
echo "Starting Knowledge Service on port 8300..."
cd "$AI_PLATFORM_DIR/knowledge-service"
.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8300 --reload &
PIDS+=($!)

# Brief pause to let dependencies start
sleep 2

# Start AI Gateway
echo "Starting AI Gateway on port 8200..."
cd "$AI_PLATFORM_DIR/ai-gateway"
.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8200 --reload &
PIDS+=($!)

echo ""
echo "=== AI Platform Running ==="
echo ""
echo "  MCP Server:        http://localhost:8100"
echo "  AI Gateway:        http://localhost:8200"
echo "  Knowledge Service: http://localhost:8300"
echo ""
echo "  API Docs:"
echo "    MCP Server:        http://localhost:8100/docs"
echo "    AI Gateway:        http://localhost:8200/docs"
echo "    Knowledge Service: http://localhost:8300/docs"
echo ""
echo "  Health Checks:"
echo "    curl http://localhost:8100/health"
echo "    curl http://localhost:8200/api/ai/health"
echo "    curl http://localhost:8300/api/knowledge/health"
echo ""
echo "  Chat:"
echo "    curl -X POST http://localhost:8200/api/ai/chat \\"
echo "      -H 'Content-Type: application/json' \\"
echo "      -d '{\"message\": \"What enrollments are currently processing?\"}'"
echo ""
echo "Press Ctrl+C to stop all services."
echo ""

# Wait for any child to exit
wait
