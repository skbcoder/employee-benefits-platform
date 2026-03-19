#!/usr/bin/env bash
#
# One-command local startup for the Employee Benefits Platform.
#
# Usage:
#   ./scripts/run-local.sh                # core services only
#   ./scripts/run-local.sh --with-ai      # core + AI platform services
#   ./scripts/run-local.sh --with-ui      # core + frontend
#   ./scripts/run-local.sh --all          # core + AI + frontend (everything)
#   DB_PORT=55432 ./scripts/run-local.sh --all
#
# Prerequisites: Java 17+, Docker
# AI Platform also requires: Python 3.11+, Ollama
# Frontend also requires: Node.js 18+
#
# This script will:
#   1. Start PostgreSQL via Docker Compose (pgvector/pgvector:pg16)
#   2. Build the project with the Maven Wrapper
#   3. Start the Processing Service (port 8081)
#   4. Start the Enrollment Service (port 8080)
#   5. Wait for both services to be healthy
#   6. (--with-ai/--all) Start MCP Server (8100), Knowledge Service (8300), AI Gateway (8200)
#   7. (--with-ui/--all) Start Next.js Frontend (3000)
#
# Press Ctrl+C to stop everything.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- Parse flags ---

WITH_AI=false
WITH_UI=false
for arg in "$@"; do
  case "$arg" in
    --with-ai)  WITH_AI=true ;;
    --with-ui)  WITH_UI=true ;;
    --all)      WITH_AI=true; WITH_UI=true ;;
  esac
done

# --- Pre-flight checks ---

if ! command -v java &> /dev/null; then
  echo "ERROR: Java is not installed or not on PATH."
  echo "       This project requires Java 17 or newer."
  exit 1
fi

JAVA_MAJOR_VERSION=$(java -version 2>&1 | head -1 | sed -E 's/.*"([0-9]+).*/\1/')
if [ "$JAVA_MAJOR_VERSION" -lt 17 ] 2>/dev/null; then
  echo "ERROR: Java 17 or newer is required, but found Java $JAVA_MAJOR_VERSION."
  echo "       Current java: $(which java)"
  echo "       Set JAVA_HOME to a JDK 17+ installation and ensure it is on PATH."
  exit 1
fi

if ! command -v docker &> /dev/null; then
  echo "ERROR: Docker is not installed or not on PATH."
  exit 1
fi

if ! docker compose version &> /dev/null; then
  echo "ERROR: 'docker compose' is not available. Install Docker Compose v2."
  exit 1
fi

if [ "$WITH_AI" = true ]; then
  if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed. Required for AI Platform services."
    exit 1
  fi
  if ! command -v ollama &> /dev/null; then
    echo "ERROR: Ollama is not installed. Required for AI Platform services."
    echo "       Install from https://ollama.com"
    exit 1
  fi
  AI_PLATFORM_DIR="$PROJECT_ROOT/services/ai-platform"
  for SERVICE in mcp-server ai-gateway knowledge-service; do
    if [ ! -d "$AI_PLATFORM_DIR/$SERVICE/.venv" ]; then
      echo "ERROR: Virtual environment not found for $SERVICE."
      echo "       Run: cd services/ai-platform && ./scripts/setup.sh"
      exit 1
    fi
  done
fi

if [ "$WITH_UI" = true ]; then
  if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed. Required for the frontend."
    echo "       Install Node.js 18+ from https://nodejs.org"
    exit 1
  fi
  NODE_MAJOR=$(node -v | sed -E 's/v([0-9]+).*/\1/')
  if [ "$NODE_MAJOR" -lt 18 ] 2>/dev/null; then
    echo "ERROR: Node.js 18+ is required, but found $(node -v)."
    exit 1
  fi
  FRONTEND_DIR="$PROJECT_ROOT/frontend"
  if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "==> Installing frontend dependencies..."
    (cd "$FRONTEND_DIR" && npm install --silent)
  fi
fi

export DB_PORT="${DB_PORT:-5433}"
export POSTGRES_HOST_PORT="$DB_PORT"

cleanup() {
  echo ""
  echo "Shutting down services..."
  jobs -p 2>/dev/null | xargs -r kill 2>/dev/null || true
  echo "Services stopped. PostgreSQL is still running."
  echo "To stop PostgreSQL:  docker compose -f infrastructure/docker-compose.yml down"
  echo "To remove all data:  docker compose -f infrastructure/docker-compose.yml down -v"
}

trap cleanup EXIT

cd "$PROJECT_ROOT"

# --- PostgreSQL ---

echo "==> Starting PostgreSQL on port $DB_PORT..."
docker compose -f infrastructure/docker-compose.yml up -d postgres

echo "==> Waiting for PostgreSQL to be healthy..."
until docker inspect --format='{{.State.Health.Status}}' employee-benefits-postgres 2>/dev/null | grep -q "healthy"; do
  sleep 1
done
echo "    PostgreSQL is ready."

# --- Core services ---

echo "==> Building project..."
./mvnw clean install -DskipTests -q

echo "==> Starting Processing Service (port 8081)..."
DB_PORT="$DB_PORT" ./mvnw -f services/processing-service/pom.xml spring-boot:run -q &
PROCESSING_PID=$!

echo "==> Waiting for Processing Service to be healthy..."
until curl -sf http://localhost:8081/actuator/health > /dev/null 2>&1; do
  if ! kill -0 $PROCESSING_PID 2>/dev/null; then
    echo "    ERROR: Processing Service failed to start. Check logs above."
    exit 1
  fi
  sleep 2
done
echo "    Processing Service is ready."

echo "==> Starting Enrollment Service (port 8080)..."
DB_PORT="$DB_PORT" PUBLISHER_TRANSPORT=http PROCESSING_SERVICE_URL=http://localhost:8081 \
  ./mvnw -f services/enrollment-service/pom.xml spring-boot:run -q &
ENROLLMENT_PID=$!

echo "==> Waiting for Enrollment Service to be healthy..."
until curl -sf http://localhost:8080/actuator/health > /dev/null 2>&1; do
  if ! kill -0 $ENROLLMENT_PID 2>/dev/null; then
    echo "    ERROR: Enrollment Service failed to start. Check logs above."
    exit 1
  fi
  sleep 2
done
echo "    Enrollment Service is ready."

# --- AI Platform (optional) ---

if [ "$WITH_AI" = true ]; then
  echo ""
  echo "==> Starting AI Platform services..."

  # Check Ollama is running
  if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
    echo "    WARNING: Ollama does not appear to be running on localhost:11434."
    echo "    Start Ollama before using the AI Gateway or Knowledge Service."
  fi

  echo "==> Starting MCP Server (port 8100)..."
  cd "$AI_PLATFORM_DIR/mcp-server"
  .venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8100 --reload 2>&1 | sed 's/^/    [mcp] /' &

  echo "==> Starting Knowledge Service (port 8300)..."
  cd "$AI_PLATFORM_DIR/knowledge-service"
  DB_PORT="$DB_PORT" .venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8300 --reload 2>&1 | sed 's/^/    [rag] /' &

  sleep 2

  echo "==> Starting AI Gateway (port 8200)..."
  cd "$AI_PLATFORM_DIR/ai-gateway"
  .venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8200 --reload 2>&1 | sed 's/^/    [gw]  /' &

  cd "$PROJECT_ROOT"
fi

# --- Frontend (optional) ---

if [ "$WITH_UI" = true ]; then
  echo ""
  echo "==> Starting Frontend (port 3000)..."
  cd "$FRONTEND_DIR"
  npx next dev 2>&1 | sed 's/^/    [ui]  /' &
  cd "$PROJECT_ROOT"
fi

# --- Summary ---

echo ""
echo "============================================"
echo "  Platform is running!"
echo ""
echo "  Core Services:"
echo "    Enrollment Service:  http://localhost:8080"
echo "    Processing Service:  http://localhost:8081"
echo "    Swagger UI:          http://localhost:8080/swagger-ui/index.html"
echo "    PostgreSQL:          localhost:$DB_PORT"
if [ "$WITH_AI" = true ]; then
echo ""
echo "  AI Platform:"
echo "    MCP Server:          http://localhost:8100"
echo "    AI Gateway:          http://localhost:8200"
echo "    Knowledge Service:   http://localhost:8300"
echo "    AI Gateway Docs:     http://localhost:8200/docs"
fi
if [ "$WITH_UI" = true ]; then
echo ""
echo "  Frontend:"
echo "    UI:                  http://localhost:3000"
echo "    Enroll:              http://localhost:3000/enroll"
echo "    Check Status:        http://localhost:3000/status"
echo "    MCP Tools:           http://localhost:3000/mcp-tools"
fi
echo ""
echo "  Press Ctrl+C to stop services."
echo "============================================"
echo ""

wait
