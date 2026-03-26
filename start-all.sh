#!/bin/bash
# MakTek Complete Startup Script
# Starts all three services needed for the chatbot with LiveKit voice

set -e  # Exit on error

PROJECT_DIR="/Users/anaszahid/Desktop/New Chatbot AntiGravity"
cd "$PROJECT_DIR"

echo "================================================"
echo "🚀 MakTek Chatbot with LiveKit Voice Startup"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found!${NC}"
    exit 1
fi

echo -e "${BLUE}Step 1: Starting LiveKit Server (Docker)${NC}"
echo "Running on: ws://localhost:7880"
echo ""
docker run --rm \
  -d \
  -p 7880:7880 \
  -p 7882:7882 \
  -e LIVEKIT_API_KEY=APIMWLu85uDn3Uk \
  -e LIVEKIT_API_SECRET=9I6kNs6IdjioIQuYK0sIkzh6N6IWGfeCKWNZD0C8iOh \
  livekit/livekit-server --dev > /dev/null 2>&1 &

LIVEKIT_PID=$!
echo -e "${GREEN}✓ LiveKit starting (PID: $LIVEKIT_PID)${NC}"
sleep 3

echo ""
echo -e "${BLUE}Step 2: Activating Python environment${NC}"
source "$PROJECT_DIR/.venv/bin/activate"
echo -e "${GREEN}✓ Python environment activated${NC}"

echo ""
echo -e "${BLUE}Step 3: Starting Backend API${NC}"
echo "Running on: http://127.0.0.1:8000"
python "$PROJECT_DIR/api.py" > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend starting (PID: $BACKEND_PID)${NC}"
sleep 3

echo ""
echo -e "${BLUE}Step 4: Starting Frontend${NC}"
echo "Running on: http://127.0.0.1:5176"
cd "$PROJECT_DIR/frontend"
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend starting (PID: $FRONTEND_PID)${NC}"
sleep 5

echo ""
echo -e "${BLUE}Step 5: Starting LiveKit Agent Worker${NC}"
cd "$PROJECT_DIR"
python "$PROJECT_DIR/start_livekit_agent.py" > /tmp/agent.log 2>&1 &
AGENT_PID=$!
echo -e "${GREEN}✓ Agent starting (PID: $AGENT_PID)${NC}"

echo ""
echo "================================================"
echo -e "${GREEN}✅ All Services Started!${NC}"
echo "================================================"
echo ""
echo -e "📊 Service Status:"
echo -e "  ${GREEN}✓ LiveKit Server${NC}  PID: $LIVEKIT_PID"
echo -e "  ${GREEN}✓ Backend API${NC}     PID: $BACKEND_PID"
echo -e "  ${GREEN}✓ Frontend${NC}        PID: $FRONTEND_PID"
echo -e "  ${GREEN}✓ Agent Worker${NC}    PID: $AGENT_PID"
echo ""
echo -e "🌐 Access URLs:"
echo -e "  Frontend: ${BLUE}http://127.0.0.1:5176${NC}"
echo -e "  Backend:  ${BLUE}http://127.0.0.1:8000${NC}"
echo -e "  LiveKit:  ${BLUE}ws://localhost:7880${NC}"
echo ""
echo -e "📝 Logs:"
echo -e "  Backend: tail -f /tmp/backend.log"
echo -e "  Frontend: tail -f /tmp/frontend.log"
echo -e "  Agent: tail -f /tmp/agent.log"
echo ""
echo -e "${YELLOW}To stop all services:${NC}"
echo -e "  kill $LIVEKIT_PID $BACKEND_PID $FRONTEND_PID $AGENT_PID"
echo ""
echo "================================================"
echo "Open http://127.0.0.1:5176 in your browser!"
echo "================================================"

# Keep script running
wait
