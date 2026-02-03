#!/bin/bash
# RALF VPS Deployment Script
# Sets up autonomous agent system on VPS

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[DEPLOY]${NC} $1"; }
success() { echo -e "${GREEN}[DEPLOY]${NC} $1"; }
warning() { echo -e "${YELLOW}[DEPLOY]${NC} $1"; }
error() { echo -e "${RED}[DEPLOY]${NC} $1"; }

# =============================================================================
# CONFIGURATION
# =============================================================================

RALF_DIR="/opt/ralf"
DATA_DIR="/var/ralf/data"
PROJECT_DIR="/var/ralf/project"
LOG_DIR="/var/log/ralf"

# =============================================================================
# PRE-FLIGHT CHECKS
# =============================================================================

log "Starting RALF VPS deployment..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root (use sudo)"
    exit 1
fi

# Check for required tools
for cmd in docker docker-compose git curl; do
    if ! command -v $cmd &> /dev/null; then
        error "$cmd is required but not installed"
        exit 1
    fi
done

# Check for .env file
if [ ! -f ".env" ]; then
    warning ".env file not found, copying from .env.example"
    cp .env.example .env
    error "Please edit .env with your API keys and configuration"
    exit 1
fi

# Source environment variables
source .env

# Verify required variables
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$GLM_API_KEY" ]; then
    error "Either ANTHROPIC_API_KEY or GLM_API_KEY must be set in .env"
    exit 1
fi

success "Pre-flight checks passed"

# =============================================================================
# SETUP DIRECTORIES
# =============================================================================

log "Setting up directories..."

mkdir -p $RALF_DIR $DATA_DIR $PROJECT_DIR $LOG_DIR
mkdir -p $DATA_DIR/communications
mkdir -p $PROJECT_DIR/5-project-memory/blackbox5
mkdir -p $PROJECT_DIR/.git

# Create queue.yaml if not exists
if [ ! -f "$DATA_DIR/communications/queue.yaml" ]; then
cat > "$DATA_DIR/communications/queue.yaml" << 'EOF'
queue: []

metadata:
  version: "1.0"
  last_updated: ""
  updated_by: ""
  queue_depth_target: 3-5
  current_depth: 0
EOF
fi

# Create events.yaml if not exists
if [ ! -f "$DATA_DIR/communications/events.yaml" ]; then
cat > "$DATA_DIR/communications/events.yaml" << 'EOF'
events: []
EOF
fi

# Create verify.yaml if not exists
if [ ! -f "$DATA_DIR/communications/verify.yaml" ]; then
cat > "$DATA_DIR/communications/verify.yaml" << 'EOF'
verifications: []
EOF
fi

success "Directories created"

# =============================================================================
# CLONE REPOSITORY
# =============================================================================

log "Setting up project repository..."

if [ -n "$GIT_REPO_URL" ]; then
    if [ -d "$PROJECT_DIR/.git" ]; then
        log "Repository exists, pulling latest..."
        cd $PROJECT_DIR
        git pull origin ${GIT_BRANCH:-main}
    else
        log "Cloning repository..."
        git clone $GIT_REPO_URL $PROJECT_DIR
        cd $PROJECT_DIR
        git checkout ${GIT_BRANCH:-main}
    fi
    success "Repository ready"
else
    warning "No GIT_REPO_URL set, using empty project directory"
fi

# =============================================================================
# BUILD AND START
# =============================================================================

log "Building Docker images..."

docker-compose build

success "Docker images built"

log "Starting RALF services..."

docker-compose up -d

success "Services started"

# =============================================================================
# WAIT FOR HEALTH
# =============================================================================

log "Waiting for services to be healthy..."

sleep 5

# Check API health
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        success "API is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        error "API failed to start"
        docker-compose logs api
        exit 1
    fi
    sleep 2
done

# Check agent health
for agent in planner executor verifier; do
    if docker-compose ps $agent | grep -q "healthy"; then
        success "$agent agent is healthy"
    else
        warning "$agent agent may still be starting"
    fi
done

# =============================================================================
# SUMMARY
# =============================================================================

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  RALF VPS Deployment Complete"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Services:"
echo "  API:        http://localhost:8000"
echo "  Grafana:    http://localhost:3000"
echo "  Prometheus: http://localhost:9090"
echo ""
echo "Agent Status:"
docker-compose ps
echo ""
echo "Logs:"
echo "  docker-compose logs -f [service]"
echo ""
echo "Commands:"
echo "  Stop:    docker-compose down"
echo "  Restart: docker-compose restart"
echo "  Update:  docker-compose pull && docker-compose up -d"
echo ""
echo "═══════════════════════════════════════════════════════════════"
