#!/bin/bash

###############################################################################
# Redis Startup Script for BlackBox 5
#
# This script manages the Redis server lifecycle for the BlackBox 5 event bus.
# It checks if Redis is already running, starts it if needed, and provides
# status information.
#
# Usage:
#   ./start-redis.sh              # Start Redis
#   ./start-redis.sh status       # Check Redis status
#   ./start-redis.sh stop         # Stop Redis
#   ./start-redis.sh restart      # Restart Redis
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REDIS_PORT=${REDIS_PORT:-6379}
REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_CONF=${REDIS_CONF:-""}
REDIS_DIR=${REDIS_DIR:-"/tmp/redis-blackbox5"}
REDIS_PID_FILE="$REDIS_DIR/redis.pid"
REDIS_LOG_FILE="$REDIS_DIR/redis.log"
REDIS_DATA_DIR="$REDIS_DIR/data"

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Redis is installed
check_redis_installed() {
    if ! command -v redis-server &> /dev/null; then
        print_error "Redis is not installed"
        echo ""
        echo "Installation instructions:"
        echo "  macOS:   brew install redis"
        echo "  Ubuntu:  sudo apt-get install redis-server"
        echo "  CentOS:  sudo yum install redis"
        echo "  Windows: Download from https://redis.io/download"
        return 1
    fi
    return 0
}

# Function to check if Redis is already running
is_redis_running() {
    if [ -f "$REDIS_PID_FILE" ]; then
        PID=$(cat "$REDIS_PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        fi
    fi

    # Also check using redis-cli
    if command -v redis-cli &> /dev/null; then
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping > /dev/null 2>&1; then
            return 0
        fi
    fi

    return 1
}

# Function to get Redis PID
get_redis_pid() {
    if [ -f "$REDIS_PID_FILE" ]; then
        cat "$REDIS_PID_FILE"
    else
        # Try to find Redis process
        pgrep -f "redis-server.*:$REDIS_PORT" || echo ""
    fi
}

# Function to check if port is in use
is_port_in_use() {
    if command -v lsof &> /dev/null; then
        lsof -i ":$REDIS_PORT" > /dev/null 2>&1
    elif command -v netstat &> /dev/null; then
        netstat -an | grep ":$REDIS_PORT" | grep LISTEN > /dev/null 2>&1
    else
        return 1
    fi
}

# Function to create Redis directories
create_directories() {
    print_info "Creating Redis directories..."
    mkdir -p "$REDIS_DIR"
    mkdir -p "$REDIS_DATA_DIR"
    print_success "Directories created: $REDIS_DIR"
}

# Function to start Redis
start_redis() {
    print_info "Starting Redis server..."

    # Check if Redis is installed
    if ! check_redis_installed; then
        exit 1
    fi

    # Check if already running
    if is_redis_running; then
        print_warning "Redis is already running on port $REDIS_PORT"
        PID=$(get_redis_pid)
        echo "PID: $PID"
        return 0
    fi

    # Check if port is in use
    if is_port_in_use; then
        print_error "Port $REDIS_PORT is already in use"
        if command -v lsof &> /dev/null; then
            echo "Process using port:"
            lsof -i ":$REDIS_PORT" | head -n 5
        fi
        exit 1
    fi

    # Create directories
    create_directories

    # Build Redis command
    REDIS_CMD="redis-server"

    if [ -n "$REDIS_CONF" ]; then
        print_info "Using config file: $REDIS_CONF"
        REDIS_CMD="$REDIS_CMD $REDIS_CONF"
    else
        # Use default configuration
        REDIS_CMD="$REDIS_CMD --port $REDIS_PORT"
        REDIS_CMD="$REDIS_CMD --dir $REDIS_DATA_DIR"
        REDIS_CMD="$REDIS_CMD --daemonize yes"
        REDIS_CMD="$REDIS_CMD --pidfile $REDIS_PID_FILE"
        REDIS_CMD="$REDIS_CMD --logfile $REDIS_LOG_FILE"
        REDIS_CMD="$REDIS_CMD --appendonly yes"
        REDIS_CMD="$REDIS_CMD --appendfilename appendonly.aof"
        REDIS_CMD="$REDIS_CMD --databases 16"
        REDIS_CMD="$REDIS_CMD --maxmemory 256mb"
        REDIS_CMD="$REDIS_CMD --maxmemory-policy allkeys-lru"
    fi

    # Start Redis
    print_info "Executing: $REDIS_CMD"
    if $REDIS_CMD; then
        # Wait a moment for Redis to start
        sleep 1

        if is_redis_running; then
            PID=$(get_redis_pid)
            print_success "Redis started successfully (PID: $PID)"
            echo ""
            echo "Connection details:"
            echo "  Host: $REDIS_HOST"
            echo "  Port: $REDIS_PORT"
            echo "  PID:  $PID"
            echo "  Log:  $REDIS_LOG_FILE"

            # Test connection
            if command -v redis-cli &> /dev/null; then
                echo ""
                print_info "Testing connection..."
                if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>/dev/null; then
                    print_success "Connection test successful"
                else
                    print_warning "Connection test failed (Redis may still be starting)"
                fi
            fi
        else
            print_error "Failed to start Redis (check log: $REDIS_LOG_FILE)"
            exit 1
        fi
    else
        print_error "Failed to execute Redis command"
        exit 1
    fi
}

# Function to stop Redis
stop_redis() {
    print_info "Stopping Redis server..."

    if ! is_redis_running; then
        print_warning "Redis is not running"
        return 0
    fi

    PID=$(get_redis_pid)

    if [ -n "$PID" ]; then
        print_info "Stopping Redis (PID: $PID)..."

        # Try graceful shutdown first
        if command -v redis-cli &> /dev/null; then
            redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" shutdown 2>/dev/null || true
            sleep 2
        fi

        # Check if still running
        if ps -p "$PID" > /dev/null 2>&1; then
            print_warning "Graceful shutdown failed, forcing..."
            kill "$PID" 2>/dev/null || true
            sleep 1

            # Final check
            if ps -p "$PID" > /dev/null 2>&1; then
                print_error "Failed to stop Redis (PID: $PID)"
                exit 1
            fi
        fi

        # Clean up PID file
        [ -f "$REDIS_PID_FILE" ] && rm -f "$REDIS_PID_FILE"

        print_success "Redis stopped successfully"
    else
        print_warning "Redis PID not found"
    fi
}

# Function to restart Redis
restart_redis() {
    print_info "Restarting Redis server..."
    stop_redis
    sleep 1
    start_redis
}

# Function to show Redis status
status_redis() {
    print_info "Checking Redis status..."

    if is_redis_running; then
        print_success "Redis is running"
        PID=$(get_redis_pid)
        echo "PID: $PID"
        echo "Port: $REDIS_PORT"

        # Get detailed info if redis-cli is available
        if command -v redis-cli &> /dev/null; then
            echo ""
            print_info "Redis Info:"
            redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" INFO server 2>/dev/null | grep -E "redis_version|process_id|uptime" || true
        fi
    else
        print_warning "Redis is not running"
        echo ""
        echo "To start Redis, run: $0 start"
    fi

    # Show log file location
    if [ -f "$REDIS_LOG_FILE" ]; then
        echo ""
        echo "Log file: $REDIS_LOG_FILE"
        echo "Last 5 log entries:"
        tail -n 5 "$REDIS_LOG_FILE" 2>/dev/null || true
    fi
}

# Function to show usage
show_usage() {
    echo "Redis Startup Script for BlackBox 5"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  (no args)  Start Redis (default)"
    echo "  start      Start Redis server"
    echo "  stop       Stop Redis server"
    echo "  restart    Restart Redis server"
    echo "  status     Show Redis status"
    echo "  help       Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  REDIS_PORT   Redis port (default: 6379)"
    echo "  REDIS_HOST   Redis host (default: localhost)"
    echo "  REDIS_CONF   Path to Redis configuration file (optional)"
    echo "  REDIS_DIR    Redis working directory (default: /tmp/redis-blackbox5)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Start Redis with defaults"
    echo "  REDIS_PORT=6380 $0    # Start Redis on port 6380"
    echo "  $0 status             # Check Redis status"
}

# Main script logic
main() {
    local command="${1:-start}"

    case "$command" in
        start)
            start_redis
            ;;
        stop)
            stop_redis
            ;;
        restart)
            restart_redis
            ;;
        status)
            status_redis
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown command: $command"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
