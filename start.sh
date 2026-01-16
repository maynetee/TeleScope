#!/bin/bash

# TeleScope - Local Development Server
# Usage: ./start.sh

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting TeleScope...${NC}"

# Find suitable Python version (3.11-3.13, not 3.14 which lacks pydantic wheels)
PYTHON_CMD=""
for py in python3.11 python3.12 python3.13; do
    if command -v $py &> /dev/null; then
        PYTHON_CMD=$py
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "Python 3.11-3.13 is required. Python 3.14 is not yet supported by pydantic."
    echo "Install with: brew install python@3.13"
    exit 1
fi

echo -e "${BLUE}Using $PYTHON_CMD${NC}"

# Check Node
if ! command -v node &> /dev/null; then
    echo "Node.js is required. Please install it."
    exit 1
fi

# Create data directory
mkdir -p "$ROOT_DIR/data"

# Install backend dependencies if needed
if [ ! -d "$BACKEND_DIR/.venv" ]; then
    echo -e "${BLUE}Setting up Python virtual environment...${NC}"
    $PYTHON_CMD -m venv "$BACKEND_DIR/.venv"
    source "$BACKEND_DIR/.venv/bin/activate"
    pip install -r "$BACKEND_DIR/requirements.txt"
else
    source "$BACKEND_DIR/.venv/bin/activate"
fi

# Install frontend dependencies if needed
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo -e "${BLUE}Installing frontend dependencies...${NC}"
    cd "$FRONTEND_DIR"
    npm install
fi

# Start backend
echo -e "${GREEN}Starting backend on http://localhost:8000${NC}"
cd "$BACKEND_DIR"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend
echo -e "${GREEN}Starting frontend on http://localhost:5173${NC}"
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

cd "$ROOT_DIR"

# Trap to cleanup on exit
cleanup() {
    echo -e "\n${BLUE}Shutting down...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

echo -e "\n${GREEN}TeleScope is running!${NC}"
echo -e "  Frontend: http://localhost:5173"
echo -e "  Backend:  http://localhost:8000"
echo -e "  API Docs: http://localhost:8000/docs"
echo -e "\nPress Ctrl+C to stop.\n"

# Wait for processes
wait
