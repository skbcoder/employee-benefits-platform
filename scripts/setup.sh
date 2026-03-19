#!/usr/bin/env bash
#
# Employee Benefits Platform — Environment Setup Script
#
# Detects prerequisites, installs missing ones (with confirmation),
# and prepares the project for local development.
#
# Usage:
#   ./scripts/setup.sh              # interactive — prompts before installing
#   ./scripts/setup.sh --auto       # non-interactive — installs everything
#   ./scripts/setup.sh --check      # check only — no installs
#
# Supports: macOS (Homebrew), Ubuntu/Debian (apt), and generic Linux.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# --- Flags ---
AUTO=false
CHECK_ONLY=false
for arg in "$@"; do
  case "$arg" in
    --auto)  AUTO=true ;;
    --check) CHECK_ONLY=true ;;
  esac
done

# --- Helpers ---

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[MISS]${NC}  $*"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $*"; }

confirm() {
  if $AUTO; then return 0; fi
  if $CHECK_ONLY; then return 1; fi
  read -r -p "        Install $1? [Y/n] " response
  [[ -z "$response" || "$response" =~ ^[Yy] ]]
}

detect_os() {
  case "$(uname -s)" in
    Darwin*) echo "macos" ;;
    Linux*)
      if command -v apt-get &>/dev/null; then echo "debian"
      elif command -v yum &>/dev/null; then echo "rhel"
      else echo "linux"
      fi ;;
    *) echo "unknown" ;;
  esac
}

OS=$(detect_os)
MISSING=0
INSTALLED=0

echo ""
echo -e "${BOLD}Employee Benefits Platform — Setup${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "OS detected: ${BOLD}$OS${NC}"
echo ""

# ==========================================================================
# Prerequisite Checks
# ==========================================================================

echo -e "${BOLD}Checking prerequisites...${NC}"
echo ""

# --- Java 17+ ---
if command -v java &>/dev/null; then
  JAVA_VER=$(java -version 2>&1 | head -1 | sed -E 's/.*"([0-9]+).*/\1/')
  if [ "$JAVA_VER" -ge 17 ] 2>/dev/null; then
    ok "Java $JAVA_VER ($(which java))"
    INSTALLED=$((INSTALLED + 1))
  else
    warn "Java found but version $JAVA_VER < 17"
    MISSING=$((MISSING + 1))
    if confirm "Java 17 (Temurin)"; then
      case $OS in
        macos)  brew install --cask temurin@17 ;;
        debian) sudo apt-get update && sudo apt-get install -y openjdk-17-jdk ;;
        *)      fail "Please install Java 17+ manually: https://adoptium.net/" ;;
      esac
    fi
  fi
else
  warn "Java not found"
  MISSING=$((MISSING + 1))
  if confirm "Java 17 (Temurin)"; then
    case $OS in
      macos)  brew install --cask temurin@17 ;;
      debian) sudo apt-get update && sudo apt-get install -y openjdk-17-jdk ;;
      *)      fail "Please install Java 17+ manually: https://adoptium.net/" ;;
    esac
  fi
fi

# --- Docker ---
if command -v docker &>/dev/null; then
  DOCKER_VER=$(docker --version 2>/dev/null | sed -E 's/.*version ([0-9]+\.[0-9]+).*/\1/')
  ok "Docker $DOCKER_VER"
  INSTALLED=$((INSTALLED + 1))
else
  warn "Docker not found"
  MISSING=$((MISSING + 1))
  if confirm "Docker"; then
    case $OS in
      macos)  brew install --cask docker && info "Open Docker Desktop to finish setup" ;;
      debian) curl -fsSL https://get.docker.com | sh ;;
      *)      fail "Please install Docker: https://docs.docker.com/get-docker/" ;;
    esac
  fi
fi

# --- Docker Compose (v2 plugin) ---
if docker compose version &>/dev/null 2>&1; then
  COMPOSE_VER=$(docker compose version --short 2>/dev/null)
  ok "Docker Compose $COMPOSE_VER"
  INSTALLED=$((INSTALLED + 1))
else
  warn "Docker Compose v2 not found"
  MISSING=$((MISSING + 1))
  info "Docker Compose v2 is included with Docker Desktop."
  info "For standalone install: https://docs.docker.com/compose/install/"
fi

# --- Python 3.11+ (optional — for AI Platform) ---
if command -v python3 &>/dev/null; then
  PY_VER=$(python3 --version 2>&1 | sed -E 's/Python ([0-9]+\.[0-9]+).*/\1/')
  PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
  PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
  if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 11 ] 2>/dev/null; then
    ok "Python $PY_VER ($(which python3))"
    INSTALLED=$((INSTALLED + 1))
  else
    warn "Python found but version $PY_VER < 3.11 (needed for AI Platform)"
    MISSING=$((MISSING + 1))
    if confirm "Python 3.11+"; then
      case $OS in
        macos)  brew install python@3.11 ;;
        debian) sudo apt-get update && sudo apt-get install -y python3.11 python3.11-venv ;;
        *)      fail "Please install Python 3.11+: https://www.python.org/downloads/" ;;
      esac
    fi
  fi
else
  warn "Python 3 not found (needed for AI Platform — optional)"
  MISSING=$((MISSING + 1))
  if confirm "Python 3.11+"; then
    case $OS in
      macos)  brew install python@3.11 ;;
      debian) sudo apt-get update && sudo apt-get install -y python3.11 python3.11-venv ;;
      *)      fail "Please install Python 3.11+: https://www.python.org/downloads/" ;;
    esac
  fi
fi

# --- Node.js 20+ (optional — for Frontend) ---
if command -v node &>/dev/null; then
  NODE_VER=$(node --version 2>/dev/null | sed -E 's/v([0-9]+).*/\1/')
  if [ "$NODE_VER" -ge 20 ] 2>/dev/null; then
    ok "Node.js $NODE_VER ($(which node))"
    INSTALLED=$((INSTALLED + 1))
  else
    warn "Node.js found but version $NODE_VER < 20 (needed for Frontend)"
    MISSING=$((MISSING + 1))
    if confirm "Node.js 20"; then
      case $OS in
        macos)  brew install node@20 ;;
        debian) curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt-get install -y nodejs ;;
        *)      fail "Please install Node.js 20+: https://nodejs.org/" ;;
      esac
    fi
  fi
else
  warn "Node.js not found (needed for Frontend — optional)"
  MISSING=$((MISSING + 1))
  if confirm "Node.js 20"; then
    case $OS in
      macos)  brew install node@20 ;;
      debian) curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt-get install -y nodejs ;;
      *)      fail "Please install Node.js 20+: https://nodejs.org/" ;;
    esac
  fi
fi

# --- Ollama (optional — for AI chatbot) ---
if command -v ollama &>/dev/null; then
  ok "Ollama ($(which ollama))"
  INSTALLED=$((INSTALLED + 1))
else
  warn "Ollama not found (needed for AI chatbot — optional)"
  MISSING=$((MISSING + 1))
  if confirm "Ollama"; then
    case $OS in
      macos)  brew install ollama ;;
      *)      curl -fsSL https://ollama.com/install.sh | sh ;;
    esac
  fi
fi

echo ""

# ==========================================================================
# Project Setup
# ==========================================================================

if $CHECK_ONLY; then
  echo -e "${BOLD}Summary:${NC} $INSTALLED found, $MISSING missing"
  echo ""
  if [ "$MISSING" -gt 0 ]; then
    info "Run ./scripts/setup.sh to install missing prerequisites."
  fi
  exit 0
fi

echo -e "${BOLD}Setting up project...${NC}"
echo ""

# --- .env file ---
if [ ! -f "$PROJECT_ROOT/.env" ]; then
  cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
  ok "Created .env from .env.example"
else
  ok ".env already exists"
fi

# --- Detect available PostgreSQL port ---
DB_PORT="${DB_PORT:-}"
if [ -z "$DB_PORT" ]; then
  # Check which port PostgreSQL is actually on
  PG_PORT=$(docker ps --filter name=employee-benefits-postgres --format "{{.Ports}}" 2>/dev/null | grep -oE '[0-9]+->5432' | cut -d'-' -f1 || true)
  if [ -n "$PG_PORT" ]; then
    DB_PORT="$PG_PORT"
    ok "PostgreSQL already running on port $DB_PORT"
  else
    DB_PORT=5433
  fi
fi

# --- Start PostgreSQL ---
if ! docker ps --filter name=employee-benefits-postgres --format "{{.Names}}" 2>/dev/null | grep -q employee-benefits-postgres; then
  info "Starting PostgreSQL (port $DB_PORT)..."
  POSTGRES_HOST_PORT="$DB_PORT" docker compose -f "$PROJECT_ROOT/infrastructure/docker-compose.yml" up -d postgres
  info "Waiting for PostgreSQL to be ready..."
  for i in $(seq 1 30); do
    if docker exec employee-benefits-postgres pg_isready -U benefits_app -d employee_benefits_platform &>/dev/null; then
      ok "PostgreSQL is ready"
      break
    fi
    sleep 1
  done
else
  ok "PostgreSQL already running"
fi

# --- Build Java services ---
if command -v java &>/dev/null; then
  info "Building Java services..."
  (cd "$PROJECT_ROOT" && ./mvnw clean install -DskipTests -q)
  ok "Java build complete"
fi

# --- Setup Python venvs for AI Platform ---
if command -v python3 &>/dev/null; then
  for svc in ai-gateway knowledge-service mcp-server; do
    SVC_DIR="$PROJECT_ROOT/services/ai-platform/$svc"
    if [ -d "$SVC_DIR" ] && [ -f "$SVC_DIR/requirements.txt" ]; then
      if [ ! -d "$SVC_DIR/.venv" ]; then
        info "Creating Python venv for $svc..."
        python3 -m venv "$SVC_DIR/.venv"
        "$SVC_DIR/.venv/bin/pip" install -q -r "$SVC_DIR/requirements.txt"
        ok "Python venv ready for $svc"
      else
        ok "Python venv already exists for $svc"
      fi
    fi
  done
fi

# --- Install frontend dependencies ---
if command -v node &>/dev/null && [ -d "$PROJECT_ROOT/frontend" ]; then
  if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
    info "Installing frontend dependencies..."
    (cd "$PROJECT_ROOT/frontend" && npm install -q)
    ok "Frontend dependencies installed"
  else
    ok "Frontend dependencies already installed"
  fi
fi

# --- Pull Ollama models ---
if command -v ollama &>/dev/null; then
  if ! ollama list 2>/dev/null | grep -q "llama3.1:8b"; then
    info "Pulling Ollama model llama3.1:8b (this may take a few minutes)..."
    ollama pull llama3.1:8b
    ok "llama3.1:8b model ready"
  else
    ok "Ollama llama3.1:8b already available"
  fi
  if ! ollama list 2>/dev/null | grep -q "nomic-embed-text"; then
    info "Pulling Ollama model nomic-embed-text..."
    ollama pull nomic-embed-text
    ok "nomic-embed-text model ready"
  else
    ok "Ollama nomic-embed-text already available"
  fi
fi

# ==========================================================================
# Summary
# ==========================================================================

echo ""
echo -e "${BOLD}Setup complete!${NC}"
echo "━━━━━━━━━━━━━━━"
echo ""
echo "To start the platform:"
echo ""
echo "  ./scripts/run-local.sh              # Core services (enrollment + processing)"
echo "  ./scripts/run-local.sh --with-ai    # Core + AI chatbot"
echo "  ./scripts/run-local.sh --with-ui    # Core + frontend"
echo "  ./scripts/run-local.sh --all        # Everything"
echo ""
echo "Service URLs:"
echo "  Enrollment Service:  http://localhost:8080"
echo "  Processing Service:  http://localhost:8081"
echo "  Frontend:            http://localhost:3000"
echo "  AI Gateway:          http://localhost:8200"
echo "  Swagger UI:          http://localhost:8080/swagger-ui/index.html"
echo ""
