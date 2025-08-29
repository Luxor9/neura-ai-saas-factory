# NEURA AI SaaS Factory - Monorepo Makefile
# Provides unified commands for development, testing, and deployment

.PHONY: help install dev test lint format clean docker-build docker-up docker-down audit-run api-run

# Default target
help:
	@echo "🚀 NEURA AI SaaS Factory - Monorepo Commands"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "📦 Setup & Development:"
	@echo "  install     Install all dependencies"
	@echo "  dev         Start development server with hot reload"
	@echo "  server      Start production server"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  test        Run all tests"
	@echo "  test-unit   Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  lint        Run linting checks"
	@echo "  format      Auto-format code"
	@echo "  type-check  Run type checking"
	@echo ""
	@echo "🔧 Services:"
	@echo "  api-run     Start API server only"
	@echo "  audit-run   Run LuxoraNova audit tool"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  docker-build Build all Docker images"
	@echo "  docker-up   Start all Docker services"
	@echo "  docker-down Stop all Docker services"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  clean       Clean build artifacts and cache"
	@echo "  clean-all   Deep clean including dependencies"
	@echo ""
	@echo "📊 Info:"
	@echo "  deps-tree   Show dependency tree"
	@echo "  status      Show project status"

# Installation and setup
install:
	@echo "📦 Installing dependencies..."
	pip install -e .[dev,audit,voice,monitoring]
	@echo "✅ Installation complete"

install-prod:
	@echo "📦 Installing production dependencies..."
	pip install -e .
	@echo "✅ Production installation complete"

# Development
dev:
	@echo "🔧 Starting development server..."
	python server.py

server:
	@echo "🌐 Starting production server..."
	./start.sh

api-run:
	@echo "🔧 Starting API server only..."
	uvicorn packages.api.core.main:app --host 0.0.0.0 --port 8000 --reload

audit-run:
	@echo "🔍 Running LuxoraNova audit tool..."
	python -m packages.audit.luxoranova_audit

# Testing
test:
	@echo "🧪 Running all tests..."
	pytest

test-unit:
	@echo "🧪 Running unit tests..."
	pytest -m unit

test-integration:
	@echo "🧪 Running integration tests..."
	pytest -m integration

test-coverage:
	@echo "🧪 Running tests with coverage..."
	pytest --cov=packages --cov-report=html --cov-report=term

# Code quality
lint:
	@echo "🔍 Running linting checks..."
	flake8 packages/
	@echo "✅ Linting complete"

format:
	@echo "🎨 Formatting code..."
	black packages/
	isort packages/
	@echo "✅ Code formatting complete"

type-check:
	@echo "🔍 Running type checks..."
	mypy packages/
	@echo "✅ Type checking complete"

quality: format lint type-check
	@echo "✅ All quality checks complete"

# Docker operations
docker-build:
	@echo "🐳 Building Docker images..."
	docker-compose -f docker/docker-compose.yml build

docker-up:
	@echo "🐳 Starting Docker services..."
	docker-compose -f docker/docker-compose.yml up -d

docker-down:
	@echo "🐳 Stopping Docker services..."
	docker-compose -f docker/docker-compose.yml down

docker-logs:
	@echo "📄 Showing Docker logs..."
	docker-compose -f docker/docker-compose.yml logs -f

# Cleanup
clean:
	@echo "🧹 Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/ .mypy_cache/
	@echo "✅ Cleanup complete"

clean-all: clean
	@echo "🧹 Deep cleaning..."
	rm -rf .venv/ venv/ node_modules/
	@echo "✅ Deep cleanup complete"

# Information
deps-tree:
	@echo "📊 Dependency tree:"
	pip list --format=tree

status:
	@echo "📊 Project Status:"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "📂 Project: NEURA AI SaaS Factory"
	@echo "🏗️  Structure: Monorepo"
	@echo "📦 Packages:"
	@echo "   • API Server (FastAPI)"
	@echo "   • Audit System (LuxoraNova)"
	@echo "   • UI Components"
	@echo "   • Shared Libraries"
	@echo ""
	@echo "🔧 Development URLs:"
	@echo "   • API Server: http://localhost:8000"
	@echo "   • Dashboard: http://localhost:8000/dashboard"
	@echo "   • API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "📁 Directory Structure:"
	@ls -la packages/

# Git hooks setup
setup-hooks:
	@echo "🔧 Setting up git hooks..."
	echo '#!/bin/sh\nmake format lint' > .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
	@echo "✅ Git hooks setup complete"

# Quick start for new developers
quickstart: install setup-hooks
	@echo "🚀 Quick start complete!"
	@echo "Run 'make dev' to start development server"