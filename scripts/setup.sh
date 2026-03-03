#!/usr/bin/env bash
# Cross-platform setup script for AlphaStream
# Supports: macOS, Linux, Windows (via WSL/Git Bash)

set -euo pipefail

# Detect OS
OS="unknown"
case "$(uname -s)" in
    Linux*)     OS="linux";;
    Darwin*)    OS="macos";;
    CYGWIN*)    OS="windows";;
    MINGW*)     OS="windows";;
    MSYS*)      OS="windows";;
    *)          OS="unknown";;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output (disable on Windows if not supported)
if [ "$OS" = "windows" ] || ! tty -s 2>/dev/null; then
    GREEN=''
    YELLOW=''
    RED=''
    BLUE=''
    CYAN=''
    NC=''
else
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    RED='\033[0;31m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    NC='\033[0m'
fi

log_info() { echo -e "${YELLOW}$1${NC}"; }
log_success() { echo -e "${GREEN}$1${NC}"; }
log_error() { echo -e "${RED}$1${NC}"; }
log_debug() { echo -e "${BLUE}$1${NC}"; }
log_progress() { echo -e "${CYAN}$1${NC}"; }

# Spinner function - works on all platforms
spinner_pid=""
start_spinner() {
    local message="$1"
    local delay=0.1
    local spinstr='|/-\'
    echo -ne "${CYAN}${message} ${NC}"
    (
        while true; do
            for (( i=0; i<${#spinstr}; i++ )); do
                printf "\r${CYAN}${message} ${spinstr:$i:1} ${NC}"
                sleep $delay
            done
        done
    ) &
    spinner_pid=$!
}

stop_spinner() {
    local status=$1
    if [ -n "$spinner_pid" ] && kill -0 "$spinner_pid" 2>/dev/null; then
        kill "$spinner_pid" 2>/dev/null || true
        wait "$spinner_pid" 2>/dev/null || true
    fi
    spinner_pid=""
    if [ $status -eq 0 ]; then
        printf "\r\033[K" 2>/dev/null || printf "\r"
    fi
}

# Function to run command with spinner
run_with_spinner() {
    local message="$1"
    shift
    start_spinner "$message"
    if "$@" > /dev/null 2>&1; then
        stop_spinner 0
        return 0
    else
        stop_spinner 1
        return 1
    fi
}

# Cross-platform command check
check_command() {
    if command -v "$1" > /dev/null 2>&1; then
        log_success "✓ $1 found"
        return 0
    else
        log_error "✗ $1 not found - please install it"
        return 1
    fi
}

# Check Python version
check_python_version() {
    if command -v python3 > /dev/null 2>&1; then
        local version
        version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        local major minor
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [[ "$major" -eq 3 && "$minor" -ge 12 ]]; then
            log_success "✓ Python $version (>= 3.12)"
            return 0
        else
            log_error "✗ Python $version found, but 3.12+ is required"
            return 1
        fi
    else
        log_error "✗ python3 not found"
        return 1
    fi
}

# Check if port is accessible (cross-platform)
check_port_accessible() {
    local host=$1
    local port=$2
    local service=$3
    
    if [ "$OS" = "macos" ] || [ "$OS" = "linux" ]; then
        if timeout 3 bash -c "echo > /dev/tcp/$host/$port" 2>/dev/null; then
            log_success "✓ $service is accessible at $host:$port"
            return 0
        fi
    elif command -v nc > /dev/null 2>&1; then
        if nc -z -w 3 "$host" "$port" 2>/dev/null; then
            log_success "✓ $service is accessible at $host:$port"
            return 0
        fi
    fi
    
    log_info "⚠ $service is NOT accessible at $host:$port"
    return 1
}

# Print header
echo "========================================="
echo "  AlphaStream India - Setup Script"
echo "  Platform: $OS"
echo "========================================="

echo ""
log_info "=== Step 1: Checking Prerequisites ==="

missing_prereqs=0

check_command uv || ((missing_prereqs++))
check_command bun || ((missing_prereqs++))
check_command docker || ((missing_prereqs++))
check_python_version || ((missing_prereqs++))

if [[ "$missing_prereqs" -gt 0 ]]; then
    log_error "Missing required prerequisites. Please install them and try again."
    echo ""
    echo "Installation guides:"
    echo "  - uv:     https://docs.astral.sh/uv/getting-started/installation/"
    echo "  - bun:    https://bun.sh/docs/installation"
    echo "  - docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker daemon is running
if ! docker info > /dev/null 2>&1; then
    log_error "✗ Docker daemon is not running. Please start Docker."
    exit 1
fi
log_success "✓ Docker daemon is running"

echo ""
log_info "=== Step 2: Environment Setup ==="

if [ ! -f "$PROJECT_DIR/.env" ]; then
    if [ -f "$PROJECT_DIR/.env.example" ]; then
        log_info "Creating .env from .env.example..."
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
        log_success "✓ .env created. Please edit it with your API keys."
    else
        log_error "✗ .env.example not found - cannot create .env"
        exit 1
    fi
else
    log_success "✓ .env already exists"
fi

# Source .env for validation
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    # shellcheck source=/dev/null
    source "$PROJECT_DIR/.env"
    set +a
fi

log_info "Validating critical environment variables..."

CRITICAL_VARS=(
    "GEMINI_API_KEYS"
    "DATABASE_URL"
    "REDIS_URL"
    "NEXT_PUBLIC_API_URL"
    "NEXT_PUBLIC_WS_URL"
)

missing_vars=()
for var in "${CRITICAL_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    log_error "Missing critical environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    echo ""
    read -p "Would you like to edit .env now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-vi} "$PROJECT_DIR/.env"
        # Re-source after editing
        set -a
        # shellcheck source=/dev/null
        source "$PROJECT_DIR/.env"
        set +a
        
        missing_vars=()
        for var in "${CRITICAL_VARS[@]}"; do
            if [ -z "${!var:-}" ]; then
                missing_vars+=("$var")
            fi
        done
        
        if [ ${#missing_vars[@]} -gt 0 ]; then
            log_error "Still missing critical variables: ${missing_vars[*]}"
            log_error "Setup cannot continue without these. Please update .env and run again."
            exit 1
        fi
    else
        log_error "Setup cannot continue without critical environment variables."
        exit 1
    fi
fi

log_success "✓ All critical environment variables are set"

echo ""
log_info "=== Step 3: Dependency Installation ==="

# Backend dependencies
log_info "Installing backend dependencies with uv..."
cd "$PROJECT_DIR/backend"
if run_with_spinner "  → Syncing backend packages..." uv sync; then
    log_success "✓ Backend dependencies installed"
else
    log_error "✗ Failed to install backend dependencies"
    exit 1
fi

# Pipeline dependencies
log_info "Installing pipeline dependencies with uv..."
cd "$PROJECT_DIR/pipeline"
if run_with_spinner "  → Syncing pipeline packages..." uv sync; then
    log_success "✓ Pipeline dependencies installed"
else
    log_error "✗ Failed to install pipeline dependencies"
    exit 1
fi

# FinBERT/ML dependencies
log_info "Checking FinBERT runtime dependencies..."
if uv run python -c "import transformers" > /dev/null 2>&1; then
    log_success "✓ transformers already available"
else
    log_info "transformers not found. Installing ML extra (this may take a few minutes)..."
    log_progress "  → Downloading PyTorch and ML libraries (~2GB)..."
    
    if run_with_spinner "  → Installing ML packages..." uv sync --extra ml; then
        log_success "✓ ML packages installed"
        
        if uv run python -c "import transformers" > /dev/null 2>&1; then
            log_success "✓ FinBERT dependencies ready"
        else
            log_info "⚠ ML extra installed but transformers import still fails."
            log_info "  Run manually: cd pipeline && uv sync --extra ml"
        fi
    else
        log_error "✗ Failed to install ML extra"
        log_info "  Run manually: cd pipeline && uv sync --extra ml"
    fi
fi

# Frontend dependencies
log_info "Installing frontend dependencies with bun..."
cd "$PROJECT_DIR/frontend"
if run_with_spinner "  → Installing npm packages with bun..." bun install; then
    log_success "✓ Frontend dependencies installed"
else
    log_error "✗ Failed to install frontend dependencies"
    exit 1
fi

# spaCy model setup
log_info "Setting up spaCy model..."
cd "$PROJECT_DIR/pipeline"

# Check if model is already available
if uv run python -c "import spacy; spacy.load('en_core_web_sm')" > /dev/null 2>&1; then
    log_success "✓ spaCy model en_core_web_sm already installed"
else
    log_info "Downloading spaCy model..."
    
    # Install spaCy model using uv pip (cross-platform wheel URL)
    SPACY_WHEEL="https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl"
    
    if run_with_spinner "  → Downloading en_core_web_sm..." uv pip install "$SPACY_WHEEL"; then
        # Verify the model can be loaded
        log_info "Verifying spaCy model installation..."
        if uv run python -c "import spacy; nlp = spacy.load('en_core_web_sm')" > /dev/null 2>&1; then
            log_success "✓ spaCy model installed and verified"
        else
            log_error "✗ spaCy model installed but cannot be loaded"
            log_info "  Try running manually: cd pipeline && uv pip install $SPACY_WHEEL"
            exit 1
        fi
    else
        log_error "✗ Failed to download spaCy model"
        log_info "  Try running manually: cd pipeline && uv pip install $SPACY_WHEEL"
        exit 1
    fi
fi

echo ""
log_info "=== Step 4: Docker Infrastructure Check ==="

# Check container health
check_container_health() {
    local container_name=$1
    local service_name=$2
    
    if docker ps --format "{{.Names}}" 2>/dev/null | grep -q "^${container_name}$"; then
        local health_status
        health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "no-healthcheck")
        
        if [ "$health_status" = "healthy" ]; then
            log_success "✓ $service_name container is running and healthy"
            return 0
        elif [ "$health_status" = "no-healthcheck" ]; then
            log_success "✓ $service_name container is running"
            return 0
        elif [ "$health_status" = "starting" ]; then
            log_info "⚠ $service_name container is starting..."
            return 2
        else
            log_error "✗ $service_name container is unhealthy (status: $health_status)"
            return 1
        fi
    else
        log_info "⚠ $service_name container is not running"
        return 1
    fi
}

# Check Docker compose file exists
INFRA_COMPOSE="$PROJECT_DIR/docker-compose.infra.yml"
if [ ! -f "$INFRA_COMPOSE" ]; then
    log_error "✗ docker-compose.infra.yml not found at $INFRA_COMPOSE"
    exit 1
fi

postgres_container="alphastream-postgres"
redis_container="alphastream-redis"

postgres_ready=false
redis_ready=false

# Check PostgreSQL container
if check_container_health "$postgres_container" "PostgreSQL"; then
    postgres_ready=true
elif [ $? -eq 2 ]; then
    log_info "Waiting for PostgreSQL to finish starting..."
    sleep 5
    if check_container_health "$postgres_container" "PostgreSQL"; then
        postgres_ready=true
    fi
fi

# Check Redis container
if check_container_health "$redis_container" "Redis"; then
    redis_ready=true
elif [ $? -eq 2 ]; then
    log_info "Waiting for Redis to finish starting..."
    sleep 3
    if check_container_health "$redis_container" "Redis"; then
        redis_ready=true
    fi
fi

# Verify ports are accessible
if $postgres_ready; then
    if ! check_port_accessible localhost 5433 "PostgreSQL"; then
        log_error "✗ PostgreSQL container is running but port 5433 is not accessible"
        postgres_ready=false
    fi
fi

if $redis_ready; then
    if ! check_port_accessible localhost 6380 "Redis"; then
        log_error "✗ Redis container is running but port 6380 is not accessible"
        redis_ready=false
    fi
fi

# Start containers if not ready
if ! $postgres_ready || ! $redis_ready; then
    echo ""
    log_info "Docker infrastructure services are not fully ready."
    
    if docker ps -a --format "{{.Names}}" 2>/dev/null | grep -q "^${postgres_container}$"; then
        log_info "Existing containers found. They may need to be started."
    fi
    
    read -p "Would you like to start/restart infrastructure containers? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Starting infrastructure containers with Docker Compose..."
        cd "$PROJECT_DIR"
        
        docker compose -f docker-compose.infra.yml down 2>/dev/null || true
        
        log_progress "  → Pulling images and creating containers..."
        if docker compose -f docker-compose.infra.yml up -d; then
            log_info "Containers starting, waiting for health checks..."
            
            local max_wait=60
            local count=0
            local postgres_healthy=false
            local redis_healthy=false
            
            while [ $count -lt $max_wait ]; do
                if ! $postgres_healthy; then
                    if check_container_health "$postgres_container" "PostgreSQL" 2>/dev/null; then
                        postgres_healthy=true
                    fi
                fi
                
                if ! $redis_healthy; then
                    if check_container_health "$redis_container" "Redis" 2>/dev/null; then
                        redis_healthy=true
                    fi
                fi
                
                if $postgres_healthy && $redis_healthy; then
                    break
                fi
                
                sleep 2
                ((count++))
                echo -n "."
            done
            echo ""
            
            if $postgres_healthy && $redis_healthy; then
                log_success "✓ Infrastructure containers are running and healthy"
                postgres_ready=true
                redis_ready=true
            else
                log_error "✗ Containers failed to become healthy within ${max_wait}s"
                if ! $postgres_healthy; then
                    log_error "  - PostgreSQL is not healthy"
                    docker logs "$postgres_container" --tail 20 2>/dev/null || true
                fi
                if ! $redis_healthy; then
                    log_error "  - Redis is not healthy"
                    docker logs "$redis_container" --tail 20 2>/dev/null || true
                fi
                exit 1
            fi
        else
            log_error "✗ Failed to start infrastructure containers"
            exit 1
        fi
    else
        log_error "Setup cannot continue without PostgreSQL and Redis."
        log_error "Start them manually with: docker compose -f docker-compose.infra.yml up -d"
        exit 1
    fi
fi

# Final port verification
if ! check_port_accessible localhost 5433 "PostgreSQL"; then
    log_error "✗ PostgreSQL port 5433 is not accessible"
    exit 1
fi

if ! check_port_accessible localhost 6380 "Redis"; then
    log_error "✗ Redis port 6380 is not accessible"
    exit 1
fi

log_success "✓ Docker infrastructure is ready"

echo ""
log_info "=== Step 5: Database & Seeding ==="

# Database migrations
log_info "Running Alembic migrations..."
cd "$PROJECT_DIR/backend"
if run_with_spinner "  → Applying database migrations..." uv run alembic upgrade head; then
    log_success "✓ Database migrations complete"
else
    log_error "✗ Database migrations failed"
    exit 1
fi

# Seed stocks
log_info "Seeding stocks data..."
cd "$PROJECT_DIR/backend"
if run_with_spinner "  → Seeding Nifty 50 stocks..." uv run python scripts/seed_stocks.py; then
    log_success "✓ Stocks data seeded"
else
    log_error "✗ Failed to seed stocks"
    exit 1
fi

# Seed pipeline data
log_info "Checking for pipeline seed data..."

PIPELINE_SEED_SCRIPT="$PROJECT_DIR/pipeline/scripts/seed_pipeline.py"
if [ -f "$PIPELINE_SEED_SCRIPT" ]; then
    cd "$PROJECT_DIR/pipeline"
    if run_with_spinner "  → Seeding pipeline data..." uv run python scripts/seed_pipeline.py; then
        log_success "✓ Pipeline data seeded"
    else
        log_error "✗ Failed to seed pipeline data"
        exit 1
    fi
else
    log_info "⚠ No pipeline seed script found. Skipping pipeline seeding."
fi

echo ""
log_info "=== Step 6: Health Verification ==="

# Backend health check
log_info "Verifying backend can start..."
cd "$PROJECT_DIR/backend"
if timeout 10 uv run python -c "from app.main import app; print('OK')" > /dev/null 2>&1; then
    log_success "✓ Backend module loads correctly"
else
    log_info "⚠ Backend import had issues - you may need to check dependencies"
fi

# Frontend health check
log_info "Verifying frontend can start..."
cd "$PROJECT_DIR/frontend"
if timeout 10 bun run build --dry-run > /dev/null 2>&1; then
    log_success "✓ Frontend can start"
    # Clean up any started processes
    if [ "$OS" = "windows" ]; then
        taskkill /F /IM "node.exe" 2>/dev/null || true
    else
        pkill -f "next-server" 2>/dev/null || true
        pkill -f "next dev" 2>/dev/null || true
    fi
else
    log_info "⚠ Frontend had issues starting - you may need to check dependencies"
fi

# Final success message
echo ""
log_success "========================================="
log_success "  Setup complete!"
log_success "========================================="
echo ""
echo "  Platform: $OS"
echo "  Infrastructure:"
echo "    - PostgreSQL: localhost:5433"
echo "    - Redis:      localhost:6380"
echo ""
echo "  Next steps:"
echo "  1. Edit .env with your API keys (if not already done)"
echo "  2. Pick a run mode:"
echo "     - Local app + Docker infra: ./scripts/start-local.sh"
echo "     - Full Docker stack:        ./scripts/start-docker.sh"
echo "     - Full Docker dev mode:     ./scripts/start-docker.sh --dev"
echo "  3. Stop services when done:"
echo "     - Local mode:  ./scripts/stop-local.sh"
echo "     - Docker mode: ./scripts/stop-docker.sh"
echo "     - Infra only:  docker compose -f docker-compose.infra.yml down"
