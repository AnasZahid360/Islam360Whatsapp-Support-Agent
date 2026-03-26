# 🚀 Quick Start: LiveKit Voice Agent for MakTek

## What's Been Set Up

✅ **LiveKit Agent SDK** - Real-time voice conversations
✅ **Dual OpenAI Keys** - One for chat, one for TTS
✅ **Token Generation** - Secure frontend access
✅ **Persistent State** - Chat history preserved
✅ **Auto-scaling** - Multiple agents supported

---

## 🎯 Start Everything in 3 Steps

### Step 1: Verify Setup

```bash
cd /Users/anaszahid/Desktop/New Chatbot AntiGravity
source .venv/bin/activate
python verify-setup.py
```

This checks:
- ✅ All environment variables set
- ✅ All Python packages installed
- ✅ Docker available

### Step 2: Make Startup Script Executable

```bash
chmod +x start-all.sh
```

### Step 3: Start All Services

```bash
./start-all.sh
```

This will start:
1. 🟢 **LiveKit Server** (Docker) - `ws://localhost:7880`
2. 🟢 **Backend API** - `http://127.0.0.1:8000`
3. 🟢 **Frontend** - `http://127.0.0.1:5176`
4. 🟢 **Agent Worker** - Listening for connections

---

## 🌐 Access the Chatbot

**Open your browser to:** http://127.0.0.1:5176

You'll see:
- 💬 Text chat interface
- 🎙️ Voice button (coming soon - frontend integration)
- 📝 Chat history (auto-saved)
- 🎫 Tickets panel

---

## 📊 What's Running

| Service | Port | Purpose |
|---------|------|---------|
| LiveKit | 7880 | Real-time voice server |
| Backend | 8000 | API & token generation |
| Frontend | 5176 | Web interface |
| Agent | (Internal) | Voice processing |

---

## 🎙️ How Voice Works

1. **User connects** → Frontend requests LiveKit token from `/livekit-token` endpoint
2. **Agent joins room** → LiveKit agent worker listens
3. **User speaks** → Audio captured and transcribed (Silero STT)
4. **Text sent to backend** → `/chat` endpoint processes
5. **Response generated** → OpenAI GPT-4 creates reply
6. **Audio generated** → OpenAI TTS speaks response back
7. **Chat persisted** → Saved to database for recovery

---

## 🔌 API Endpoints

### Get LiveKit Token
```bash
curl -X POST http://127.0.0.1:8000/livekit-token \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "room_name": "support-agent"
  }'
```

Response:
```json
{
  "token": "jwt_token_here",
  "url": "ws://localhost:7880",
  "room": "support-agent",
  "identity": "user_123"
}
```

### Chat (Text or Voice)
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, I need help",
    "user_id": "user_123",
    "thread_id": "thread_456"
  }'
```

---

## 📝 Your Configuration

```
LIVEKIT_API_KEY=APIMWLu85uDn3Uk
LIVEKIT_API_SECRET=9I6kNs6IdjioIQuYK0sIkzh6N6IWGfeCKWNZD0C8iOh
LIVEKIT_API_URL=ws://localhost:7880

OPENAI_API_KEY=sk-proj-ZP2SnIA-...    (Chat/LLM)
OPENAI_TTS_API_KEY=sk-proj-z1HTxRte... (Voice output)
```

---

## 🧪 Testing

### Test Backend
```bash
curl http://127.0.0.1:8000/health
# Response: {"status":"healthy"}
```

### Test Token Generation
```bash
curl -X POST http://127.0.0.1:8000/livekit-token \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_user"}'
```

### View Logs
```bash
# Backend logs
tail -f /tmp/backend.log

# Frontend logs
tail -f /tmp/frontend.log

# Agent logs
tail -f /tmp/agent.log
```

---

## 🛑 Stop Everything

```bash
# From the script, it shows PIDs:
kill $LIVEKIT_PID $BACKEND_PID $FRONTEND_PID $AGENT_PID

# Or manually:
pkill -f "python api.py"
pkill -f "npm run dev"
pkill -f "start_livekit_agent"
docker kill $(docker ps -q --filter "ancestor=livekit/livekit-server")
```

---

## ⚠️ Troubleshooting

### "Port already in use"
```bash
# Kill the process using the port
lsof -i :7880  # LiveKit
lsof -i :8000  # Backend
lsof -i :5176  # Frontend
```

### "OpenAI API error"
- Verify API keys in `.env`
- Check API key has billing enabled
- Verify API key permissions

### "No transcription happening"
- Check microphone access in browser
- Verify Silero STT installed: `pip install livekit-agents-silero`
- Check agent logs: `tail -f /tmp/agent.log`

### "Agent not responding"
- Verify backend is running: `curl http://127.0.0.1:8000/health`
- Check agent logs for errors
- Ensure OpenAI API key is valid

---

## 📚 Files Reference

```
/src/voice/
├── livekit_agent.py              ← Main agent
├── livekit_token_manager.py      ← Token generation
└── transcriber.py                ← Fallback transcription

/frontend/
├── livekit-integration.js        ← Voice client
└── main.js                       ← Chat UI

/
├── api.py                        ← Added /livekit-token endpoint
├── start-all.sh                  ← Start everything
├── start_livekit_agent.py        ← Agent worker
├── verify-setup.py               ← Verify setup
└── .env                          ← Credentials
```

---

## ✨ Next Steps

1. ✅ Run `./start-all.sh`
2. ✅ Open http://127.0.0.1:5176
3. ✅ Test text chat first
4. ✅ Test voice (button will be added to UI)
5. ✅ Check chat history persists on refresh

---

## 🎉 You're All Set!

All credentials are configured. Services are ready to start.

**Just run:**
```bash
cd /Users/anaszahid/Desktop/New Chatbot AntiGravity
./start-all.sh
```

Then open: **http://127.0.0.1:5176**

Enjoy your live voice chatbot! 🚀
