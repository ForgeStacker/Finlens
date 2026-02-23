#!/bin/bash

# FinLens Startup Script
# Fast startup with immediate API server

set -e

CMD_PREFIX=()
DOCKER_COMPOSE_BIN=()
COMPOSE_DISPLAY_CMD="docker compose"

# Check if we need to restart with sg docker to activate docker group
if ! docker info >/dev/null 2>&1; then
    if groups "$USER" | grep -q docker; then
        # User is in docker group but it's not active in current session
        echo "🔄 Activating docker group and restarting script..."
        exec sg docker -c "$0 $*"
    fi
fi

ensure_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        echo "❌ Docker not found. Please install Docker first:"
        echo "   curl -fsSL https://get.docker.com -o get-docker.sh"
        echo "   sh get-docker.sh"
        echo "   sudo usermod -aG docker $USER"
        echo "   Then logout and login again."
        exit 1
    fi

    # Check if user is in docker group
    if ! groups "$USER" | grep -q docker; then
        echo "❌ User '$USER' is not in the docker group."
        echo "   Run: sudo usermod -aG docker $USER"
        echo "   Then logout and login again, or run: newgrp docker"
        exit 1
    fi

    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        echo "❌ Docker daemon is not running. Please start Docker:"
        echo "   sudo systemctl start docker"
        echo "   sudo systemctl enable docker"
        exit 1
    fi

    CMD_PREFIX=()
    DOCKER_COMPOSE_BIN=(docker compose)
    COMPOSE_DISPLAY_CMD="docker compose"
}

ensure_compose() {
    if docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE_BIN=(docker compose)
        COMPOSE_DISPLAY_CMD="docker compose"
        return
    fi

    if command -v docker-compose >/dev/null 2>&1; then
        DOCKER_COMPOSE_BIN=(docker-compose)
        COMPOSE_DISPLAY_CMD="docker-compose"
        return
    fi

    echo "❌ docker-compose not found. Please install it:"
    echo "   Docker Compose should come with modern Docker installations."
    echo "   If using older Docker, install: sudo apt-get install docker-compose"
    exit 1
}

compose() {
    "${DOCKER_COMPOSE_BIN[@]}" "$@"
}

docker_cmd() {
    docker "$@"
}

ensure_docker_environment() {
    ensure_docker
    ensure_compose
}

check_aws_credentials() {
    echo "🔐 Checking AWS credentials..."
    
    # Check if ~/.aws directory exists
    if [ ! -d "$HOME/.aws" ]; then
        echo "❌ AWS credentials not found!"
        echo ""
        echo "Please configure AWS credentials before running FinLens:"
        echo "  1. Run: aws configure --profile your-profile-name"
        echo "  2. Or manually create ~/.aws/credentials and ~/.aws/config"
        echo ""
        echo "See README.md for detailed setup instructions."
        exit 1
    fi
    
    # Check if credentials file exists and has content
    if [ ! -f "$HOME/.aws/credentials" ] || [ ! -s "$HOME/.aws/credentials" ]; then
        echo "❌ AWS credentials file is missing or empty!"
        echo ""
        echo "Please configure AWS credentials:"
        echo "  Run: aws configure --profile your-profile-name"
        echo ""
        echo "See README.md for detailed setup instructions."
        exit 1
    fi
    
    # Check if config file exists
    if [ ! -f "$HOME/.aws/config" ]; then
        echo "⚠️  Warning: ~/.aws/config file not found"
        echo "   It's recommended to have both credentials and config files"
    fi
    
    echo "✅ AWS credentials found"
}

check_profile_configuration() {
    echo "📋 Checking FinLens profile configuration..."
    
    if [ ! -f "config/profiles.yaml" ]; then
        echo "❌ config/profiles.yaml not found!"
        exit 1
    fi
    
    # Extract profile names from profiles.yaml (simple grep approach)
    local profiles=$(grep -E '^\s+-\s+name:' config/profiles.yaml | sed 's/.*name:\s*//' | tr '\n' ' ')
    
    if [ -z "$profiles" ]; then
        echo "❌ No profiles configured in config/profiles.yaml"
        echo "   Please add at least one profile with AWS credentials"
        exit 1
    fi
    
    echo "✅ Found configured profiles: $profiles"
    
    # Verify each profile exists in AWS credentials
    local missing_profiles=()
    for profile in $profiles; do
        if ! grep -q "\[$profile\]" "$HOME/.aws/credentials" 2>/dev/null; then
            missing_profiles+=("$profile")
        fi
    done
    
    if [ ${#missing_profiles[@]} -gt 0 ]; then
        echo "⚠️  Warning: The following profiles in profiles.yaml are not in ~/.aws/credentials:"
        for profile in "${missing_profiles[@]}"; do
            echo "   - $profile"
        done
        echo ""
        echo "To add missing profile(s), run:"
        for profile in "${missing_profiles[@]}"; do
            echo "   aws configure --profile $profile"
        done
        echo ""
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo "✅ All profiles have AWS credentials configured"
    fi
}

echo "🚀 FinLens Startup Script"
echo "========================="

# Check AWS credentials before starting
check_aws_credentials
check_profile_configuration

# Function to open browser
open_browser() {
    local url="http://localhost:5173"
    echo "🌐 Opening browser at $url"
    
    # Try different browser opening methods based on OS
    if command -v xdg-open > /dev/null; then
        xdg-open "$url" 2>/dev/null &  # Linux
    elif command -v open > /dev/null; then
        open "$url" 2>/dev/null &       # macOS
    elif command -v start > /dev/null; then
        start "$url" 2>/dev/null &      # Windows
    else
        echo "ℹ️  Please open your browser manually and go to: $url"
    fi
}

# Function to show LIVE processing logs
show_live_processing_logs() {
    echo "📊 AWS Data Collection Progress (LIVE):"
    echo "═══════════════════════════════════════════════════════"
    
    # Show ALL logs in real-time until completion
    compose logs -f backend | while IFS= read -r line; do
        echo "$line"
        
        # Stop when data collection finishes and API server starts
        if echo "$line" | grep -q "Data collection complete"; then
            echo "═══════════════════════════════════════════════════════"
            echo "✅ 100% PROCESSING COMPLETE! Starting frontend..."
            break
        fi
        
        # Also stop when uvicorn is up
        if echo "$line" | grep -q "Application startup complete\|Uvicorn running"; then
            echo "═══════════════════════════════════════════════════════"
            echo "✅ API server started! Starting frontend..."
            break
        fi
    done
}

# Function to start frontend after backend processing completes
start_frontend_after_processing() {
    echo "🚀 Backend processing complete! Starting frontend..."
    
    # Start the frontend container
    compose up -d frontend
    
    if [ $? -eq 0 ]; then
        echo "✅ Frontend container started successfully!"
    else
        echo "❌ Failed to start frontend container"
        return 1
    fi
}

# Function to wait for services
wait_for_services() {
    echo "⏳ Waiting for data processing to complete..."
    
    # Step 1: Wait for data collection to complete (API server responding with data)
    echo "📊 Waiting for 100% data processing completion..."
    local api_ready=false
    for i in {1..600}; do  # Wait up to 10 minutes for data collection + API startup
        # First check if API server is reachable
        if curl -s --connect-timeout 5 http://localhost:8000/api/discovery >/dev/null 2>&1; then
            # Then check if it has actual data
            local response=$(curl -s --connect-timeout 5 http://localhost:8000/api/discovery 2>/dev/null)
            if echo "$response" | grep -q "accounts\|profile" 2>/dev/null; then
                echo "✅ Data processing 100% complete! API server serving data!"
                api_ready=true
                break
            fi
        fi
        sleep 1
        # Show progress every 30 seconds
        if [ $((i % 30)) -eq 0 ]; then
            echo "⏳ Still processing AWS data... (${i}s elapsed)"
        fi
    done
    
    if [ "$api_ready" != "true" ]; then
        echo "❌ Data processing did not complete in time"
        return 1
    fi
    
    # Step 2: Wait for frontend to be ready  
    echo "🎨 Waiting for frontend server..."
    local frontend_ready=false
    for i in {1..60}; do  # Wait up to 1 minute for frontend
        if curl -s http://localhost:5173 > /dev/null 2>&1; then
            echo "✅ Frontend server ready!"
            frontend_ready=true
            break
        fi
        sleep 1
    done
    
    # Step 3: ONLY NOW open browser after EVERYTHING is complete
    if [ "$api_ready" = "true" ] && [ "$frontend_ready" = "true" ]; then
        echo ""
        echo "🎉 EVERYTHING READY! All processing complete, API serving data!"
        echo "🚀 NOW opening browser..."
        sleep 2  # Brief pause for emphasis
        open_browser
        return 0
    else
        echo "❌ Services not ready. Manual access: http://localhost:5173"
        return 1
    fi
}

# Ensure Docker and Docker Compose are ready to use
ensure_docker_environment

echo "🧹 Cleaning up previously created containers..."
# Remove existing project containers and any stopped leftovers so we always rebuild fresh
compose down --remove-orphans >/dev/null 2>&1 || true
docker_cmd container prune -f >/dev/null 2>&1 || true

echo "🧽 Clearing previous scan data..."
if [ -d "Data" ]; then
    if ! rm -rf Data/* >/dev/null 2>&1; then
        echo "⚠️  Direct cleanup failed due to permissions; retrying with Docker..."
        docker_cmd run --rm -v "$PWD/Data:/data" alpine sh -c "rm -rf /data/*" >/dev/null 2>&1 || true
    fi
fi

echo "🐳 Docker ready - Using containerized mode"
echo "📦 Building and starting all services..."

# Start ONLY backend first
echo "📦 Building and starting backend for data processing..."
compose build --no-cache backend
compose up -d backend

echo "🎉 Backend started! Following sequential processing:"
echo "  1️⃣  Backend collecting AWS data (live logs below)..."
echo "  2️⃣  API server will start after collection"
echo "  3️⃣  Frontend will start after API is ready"
echo "  4️⃣  Browser will open when everything is complete"
echo "═══════════════════════════════════════════════════════"

# Show LIVE processing logs
show_live_processing_logs

# Build frontend without cache first (to pick up any new files like lib/utils.ts)
echo "📦 Building frontend without cache..."
compose build --no-cache frontend

# Start frontend AFTER processing completes
start_frontend_after_processing

# Wait for services and open browser
wait_for_services

echo ""
echo "🎯 FinLens is running!"
echo "📊 Dashboard: http://localhost:5173"
echo "🔧 API:       http://localhost:8000"
echo "📋 View logs: $COMPOSE_DISPLAY_CMD logs -f"
echo "🛑 Stop:      $COMPOSE_DISPLAY_CMD down"
echo ""
echo "✅ Complete sequential processing finished successfully!"