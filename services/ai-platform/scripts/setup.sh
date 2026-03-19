#!/usr/bin/env bash
set -euo pipefail

# AI Platform Setup Script
# Installs Python dependencies, pulls Ollama models, and creates DB schema.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AI_PLATFORM_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== AI Platform Setup ==="
echo ""

# ── Check prerequisites ─────────────────────────────────────────────

echo "Checking prerequisites..."

# Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3 not found. Install Python 3.11+ to continue."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "  Python: $PYTHON_VERSION"

# Ollama
if ! command -v ollama &>/dev/null; then
    echo "ERROR: Ollama not found. Install from https://ollama.com"
    exit 1
fi

OLLAMA_VERSION=$(ollama --version 2>&1 | head -1)
echo "  Ollama: $OLLAMA_VERSION"

# PostgreSQL (check via docker)
echo "  PostgreSQL: Checking via benefits platform docker-compose..."

echo ""

# ── Pull Ollama models ──────────────────────────────────────────────

echo "Pulling Ollama models..."

echo "  Pulling llama3.1:8b (chat model)..."
ollama pull llama3.1:8b

echo "  Pulling nomic-embed-text (embedding model)..."
ollama pull nomic-embed-text

echo "  Models ready."
echo ""

# ── Create Python virtual environments ──────────────────────────────

echo "Setting up Python virtual environments..."

for SERVICE in mcp-server ai-gateway knowledge-service; do
    SERVICE_DIR="$AI_PLATFORM_DIR/$SERVICE"
    echo "  Setting up $SERVICE..."

    if [ ! -d "$SERVICE_DIR/.venv" ]; then
        python3 -m venv "$SERVICE_DIR/.venv"
    fi

    source "$SERVICE_DIR/.venv/bin/activate"
    pip install --quiet --upgrade pip
    pip install --quiet -r "$SERVICE_DIR/requirements.txt"
    deactivate
done

echo "  Dependencies installed."
echo ""

# ── Run knowledge schema migration ─────────────────────────────────

echo "Running knowledge schema migration..."

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5433}"
DB_NAME="${DB_NAME:-employee_benefits_platform}"
DB_USER="${DB_USERNAME:-benefits_app}"
DB_PASS="${DB_PASSWORD:-benefits_app}"

MIGRATION_FILE="$AI_PLATFORM_DIR/knowledge-service/migrations/V1__create_knowledge_schema.sql"

if [ -f "$MIGRATION_FILE" ]; then
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -f "$MIGRATION_FILE" 2>/dev/null || echo "  (Migration may have already been applied)"
    echo "  Knowledge schema ready."
else
    echo "  WARNING: Migration file not found at $MIGRATION_FILE"
fi

echo ""

# ── Seed knowledge base (optional) ──────────────────────────────────

SEED_SCRIPT="$AI_PLATFORM_DIR/knowledge-service/seed-data/seed.py"

if [ "${SKIP_SEED:-}" = "true" ]; then
    echo "Skipping knowledge base seeding (SKIP_SEED=true)."
elif [ -f "$SEED_SCRIPT" ]; then
    echo "Seeding knowledge base with benefits documents..."
    echo "  (This requires the Knowledge Service to be running on port 8300)"
    echo "  If the Knowledge Service is not running, run seed separately later:"
    echo "    python3 $SEED_SCRIPT"
    echo ""

    if curl -sf http://localhost:8300/api/knowledge/health &>/dev/null; then
        python3 "$SEED_SCRIPT" --base-url http://localhost:8300
    else
        echo "  Knowledge Service not running — skipping seed."
        echo "  Start the services first, then seed:"
        echo "    python3 $SEED_SCRIPT"
    fi
else
    echo "  WARNING: Seed script not found at $SEED_SCRIPT"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Start the full platform (core + AI) with:"
echo "  ./scripts/run-local.sh --with-ai"
echo ""
echo "Or start AI Platform services only:"
echo "  cd $AI_PLATFORM_DIR && ./scripts/run-local.sh"
echo ""
echo "Or start services individually:"
echo "  cd mcp-server && .venv/bin/uvicorn src.main:app --port 8100 --reload"
echo "  cd ai-gateway && .venv/bin/uvicorn src.main:app --port 8200 --reload"
echo "  cd knowledge-service && .venv/bin/uvicorn src.main:app --port 8300 --reload"
echo ""
echo "To seed the knowledge base after services are running:"
echo "  python3 $AI_PLATFORM_DIR/knowledge-service/seed-data/seed.py"
