#!/bin/bash

# NEURA AI SaaS Factory - Unified Monorepo Startup Script
# This script starts all components of the NEURA AI SaaS Factory

set -e

echo "🚀 Starting NEURA AI SaaS Factory Monorepo..."

# Function to check if Python is available
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 is required but not installed."
        exit 1
    fi
    echo "✅ Python 3 found"
}

# Function to install dependencies
install_dependencies() {
    echo "📦 Installing dependencies..."
    if [ -f "pyproject.toml" ]; then
        pip install -e .
    else
        pip install -r requirements.txt
    fi
    echo "✅ Dependencies installed"
}

# Function to start the API server
start_api_server() {
    echo "🔧 Starting NEURA AI API Server..."
    python server.py &
    API_PID=$!
    echo "✅ API Server started (PID: $API_PID)"
}

# Function to start audit service
start_audit_service() {
    echo "🔍 LuxoraNova Audit Service is available"
    echo "   Run: python -m packages.audit.luxoranova_audit"
}

# Function to display service info
show_services() {
    echo ""
    echo "🌟 NEURA AI SaaS Factory - Services Status"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔧 API Server:         http://localhost:8000"
    echo "📊 Dashboard:          http://localhost:8000/dashboard"
    echo "📖 API Docs:           http://localhost:8000/docs"
    echo "💡 Health Check:       http://localhost:8000/health"
    echo ""
    echo "🔍 Audit Service:      python -m packages.audit.luxoranova_audit"
    echo "🎛️  Docker Services:    docker-compose -f docker/docker-compose.yml up"
    echo ""
    echo "📱 UI Components:"
    echo "   • SaaS Dashboard:   packages/ui/saas-dashboard/"
    echo "   • Mobile UI:        packages/ui/mobile/"
    echo "   • Admin Dashboard:  packages/ui/dashboard/"
    echo ""
    echo "Press Ctrl+C to stop all services"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
        echo "✅ API Server stopped"
    fi
    echo "👋 NEURA AI SaaS Factory stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    check_python
    install_dependencies
    start_api_server
    start_audit_service
    show_services
    
    # Keep script running
    wait
}

# Run main function
main
