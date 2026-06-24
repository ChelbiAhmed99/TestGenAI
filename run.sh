#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Setup color outputs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== TestGenAI Development Environment Launcher ===${NC}"

# Check if .env file exists, copy example if not
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    echo -e "${YELLOW}[INFO] .env not found. Copying from .env.example...${NC}"
    cp .env.example .env
  else
    echo -e "${YELLOW}[INFO] Creating a basic .env file...${NC}"
    echo "GOOGLE_API_KEY=" > .env
  fi
fi

# Print usage helper
usage() {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  --docker       Run the application using Docker Compose (Recommended, runs in 1 command)"
  echo "  --local        Run backend and frontend locally in parallel"
  echo "  --help         Show this help message"
}

# Determine execution mode (default: Docker Compose if docker daemon is running, fallback to local)
MODE="docker"

if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
  usage
  exit 0
elif [ "$1" == "--local" ]; then
  MODE="local"
elif [ "$1" == "--docker" ]; then
  MODE="docker"
fi

if [ "$MODE" == "docker" ]; then
  if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${YELLOW}[WARNING] docker-compose not found. Falling back to local execution...${NC}"
    MODE="local"
  fi
fi

if [ "$MODE" == "docker" ]; then
  echo -e "${GREEN}[INFO] Launching TestGenAI via Docker Compose...${NC}"
  docker-compose up --build
else
  echo -e "${GREEN}[INFO] Launching TestGenAI locally...${NC}"
  
  # Setup Core AI Engine
  echo -e "${YELLOW}[1/6] Preparing Core AI Engine environment...${NC}"
  if [ ! -d "core/venv" ]; then
    python3 -m venv core/venv
  fi
  ./core/venv/bin/pip install -r requirements.txt

  # Setup Golden Path
  echo -e "${YELLOW}[2/6] Preparing Golden Path Template...${NC}"
  cd templates/golden_path
  npm install
  # Note: npx playwright install might be required but takes long, assuming standard setup or skipped for brevity.
  cd ../..

  # Setup Backend
  echo -e "${YELLOW}[3/6] Preparing Backend environment...${NC}"
  cd backend
  if [ ! -d "venv" ]; then
    python3 -m venv venv
  fi
  ./venv/bin/pip install -r requirements.txt
  cd ..

  # Setup Frontend
  echo -e "${YELLOW}[4/6] Preparing Frontend environment...${NC}"
  cd frontend
  npm install
  cd ..

  echo -e "${GREEN}[5/6] Launching Backend and Frontend in parallel...${NC}"
  
  # Trapping exit signals to kill background processes on Ctrl+C
  trap 'kill $(jobs -p)' EXIT

  # Run Backend
  cd backend
  PYTHONPATH=. ./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
  cd ..

  # Run Frontend
  cd frontend
  npm run dev &
  cd ..

  echo -e "${GREEN}[6/6] Application is running! Press Ctrl+C to stop.${NC}"
  echo -e "   - Backend API: http://localhost:8000"
  echo -e "   - Frontend UI: http://localhost:3000 or http://localhost:3001"
  
  # Keep script running to maintain background jobs
  wait
fi
