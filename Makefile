# Makefile for Pokemon AI Agents

.PHONY: help install docker-build docker-up docker-down docker-logs lint test clean

# Default target
help:
	@echo "Pokemon AI Agents Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make install        Install dependencies locally"
	@echo "  make docker-build   Build Docker images"
	@echo "  make docker-up      Start Docker containers"
	@echo "  make docker-down    Stop Docker containers"
	@echo "  make docker-logs    View Docker logs"
	@echo "  make lint           Run linters"
	@echo "  make test           Run tests"
	@echo "  make clean          Clean up temporary files"

# Install dependencies locally
install:
	pip install -r requirements.txt

# Docker commands
docker-build:
	docker-compose build

# Start Docker containers
docker-up:
	docker-compose up -d
	@echo "Services started:"
	@echo "- API running at: http://localhost:8088"
	@echo "- Streamlit frontend running at: http://localhost:8501"

# Stop Docker containers
docker-down:
	docker-compose down

# View Docker logs
docker-logs:
	docker-compose logs -f

# Run linters
lint:
	black .
	isort .
	flake8 .

# Run tests
test:
	pytest

# Clean up temporary files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
