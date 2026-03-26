# Persistent User State Implementation

## Overview

The chatbot now **persists all user state** including chat history and support tickets. When users refresh the page, all previous conversations and tickets are automatically restored.

## What's New

### 1. **Persistent State Manager** (`src/memory/persistent_state.py`)

A new comprehensive module that manages:
- **Chat History**: Every message (user & assistant) saved with timestamp
- **Chat Sessions**: Metadata about each conversation thread
- **Tickets**: All support tickets with status, priority, and resolution tracking

**Directory Structure:**
```
data/
├── chats/
│   ├── user_{user_id}/
│   │   ├── thread_{thread_id}.json (messages array)
│   │   └── sessions.json (session metadata)
│   └── chat_index.jsonl (master log)
├── tickets/
│   ├── user_{user_id}/
│   │   ├── TKT-*.json (individual tickets)
│   │   └── tickets.json (user's ticket index)
│   ├── all_tickets.jsonl (master log)
│   └── ticket_index.json (searchable index)
└── sessions/
    ├── user_{user_id}.json (all sessions for user)
    └── active_sessions.jsonl (active sessions log)
```

### 2. **Updated API** (`api.py`)

#### Modified Endpoints
- **POST `/chat`**: Now automatically saves both user message and assistant response

#### New Endpoints

**1. Get Chat History**
```
GET /chat-history/{user_id}/{thread_id}?limit=50

Response:
{
  "user_id": "test_user",
  "thread_id": "conv_123",
  "messages": [
    {
      "role": "user",
      "content": "What is your return policy?",
      "timestamp": "2026-03-18T12:30:45.123456",
      "metadata": {"config_overrides": null}
    },
    {
      "role": "assistant",
      "content": "Our return policy allows...",
      "timestamp": "2026-03-18T12:30:46.234567",
      "metadata": {"retrieved_docs_count": 3}
    }
  ]
}
```

**2. Get User Sessions**
```
GET /user-sessions/{user_id}

Response:
{
  "user_id": "test_user",
  "total_sessions": 5,
  "sessions": [
    {
      "thread_id": "conv_123",
      "created_at": "2026-03-18T10:00:00",
      "last_updated": "2026-03-18T12:30:46",
      "message_count": 8
    }
  ]
}
```

**3. Get User Tickets**
```
GET /user-tickets/{user_id}

Response:
{
  "user_id": "test_user",
  "total_tickets": 2,
  "tickets": [
    {
      "ticket_id": "TKT-20260318123045-test_use",
      "issue": "Payment not processed",
      "priority": "high",
      "status": "open",
      "created_at": "2026-03-18T12:30:45",
      "updated_at": "2026-03-18T12:30:45"
    }
  ]
}
```

**4. Get Ticket Details**
```
GET /ticket/{user_id}/{ticket_id}

Response:
{
  "ticket_id": "TKT-20260318123045-test_use",
  "user_id": "test_user",
  "thread_id": "conv_123",
  "issue": "Payment not processed",
  "priority": "high",
  "status": "open",
  "created_at": "2026-03-18T12:30:45",
  "updated_at": "2026-03-18T12:30:45",
  "assigned_to": "support_team",
  "resolved_at": null,
  "resolution": null,
  "metadata": {"estimated_response_time": "4-8 hours"}
}
```

**5. Initialize Session (Page Load)**
```
POST /init-session/{user_id}/{thread_id}

Response:
{
  "success": true,
  "user_id": "test_user",
  "thread_id": "conv_123",
  "session": {
    "created_at": "2026-03-18T10:00:00",
    "last_updated": "2026-03-18T12:30:46"
  },
  "chat_history": [
    {
      "role": "user",
      "content": "What is your return policy?",
      "timestamp": "2026-03-18T12:30:45.123456"
    },
    {
      "role": "assistant",
      "content": "Our return policy allows...",
      "timestamp": "2026-03-18T12:30:46.234567"
    }
  ],
  "tickets": [
    {
      "ticket_id": "TKT-20260318123045-test_use",
      "issue": "Payment not processed",
      "priority": "high",
      "status": "open",
      "created_at": "2026-03-18T12:30:45"
    }
  ]
}
```

### 3. **Updated Support Ticket Tool** (`src/tools/support_ticket.py`)

Now integrates with `PersistentStateManager`:
- Automatically saves tickets with full metadata
- Provides functions to retrieve user tickets
- Supports ticket status updates

```python
# Create ticket (automatic save)
ticket = create_support_ticket(
    issue="Order not received",
    user_id="test_user",
    priority="high",
    thread_id="conv_123"
)

# Get user's tickets
tickets = get_user_tickets("test_user")

# Get specific ticket
ticket = get_ticket_by_id("test_user", "TKT-20260318123045-test_use")
```

## Frontend Integration

### Page Load (Restoration)
When the page loads, call the init-session endpoint:

```javascript
// On page load
async function initSession(userId, threadId) {
  const response = await fetch(
    `/init-session/${userId}/${threadId}`,
    { method: 'POST' }
  );
  const data = await response.json();
  
  if (data.success) {
    // Restore chat history
    displayChatHistory(data.chat_history);
    
    // Restore tickets
    displayTickets(data.tickets);
  }
}
```

### Sending Messages
Messages are automatically saved by the `/chat` endpoint - no frontend changes needed!

```javascript
// Send message (auto-saves in backend)
const response = await fetch('/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "What's your return policy?",
    user_id: "test_user",
    thread_id: "conv_123"
  })
});
```

### Getting History On-Demand
Anytime retrieve chat history:

```javascript
async function getChatHistory(userId, threadId, limit = 50) {
  const response = await fetch(
    `/chat-history/${userId}/${threadId}?limit=${limit}`
  );
  return await response.json();
}
```

## Features

### Automatic Persistence
✅ Every message automatically saved when sent
✅ Both user messages and assistant responses captured
✅ Metadata (retrieved docs, config, etc.) stored
✅ Timestamps for all messages

### Session Management
✅ Multiple conversations per user
✅ Session metadata (creation time, last update)
✅ Message count per session
✅ Easy to list all user sessions

### Ticket Tracking
✅ Tickets created during escalation automatically saved
✅ Ticket status updates tracked
✅ Resolution information stored
✅ Full ticket history queryable

### Data Structure
✅ Organized by user_id and thread_id
✅ Easy to restore user state on login
✅ Master logs for analytics
✅ Searchable indexes

## Data Persistence Flow

```
User sends message
        ↓
/chat endpoint received
        ↓
Save user message to persistent storage
        ↓
Process through graph
        ↓
Generate response
        ↓
Save assistant response to persistent storage
        ↓
Return response to frontend
        ↓
--------
User refreshes page
        ↓
/init-session endpoint called
        ↓
Load all chat history from storage
        ↓
Load all tickets from storage
        ↓
Restore UI with previous state
```

## Storage Details

### Chat Messages
```json
{
  "role": "user|assistant",
  "content": "Message text",
  "timestamp": "2026-03-18T12:30:45.123456",
  "message_id": "conv_123-1710763845.123456",
  "thread_id": "conv_123",
  "user_id": "test_user",
  "metadata": {
    "config_overrides": null,
    "retrieved_docs_count": 3
  }
}
```

### Sessions
```json
{
  "thread_id": "conv_123",
  "user_id": "test_user",
  "created_at": "2026-03-18T10:00:00",
  "last_updated": "2026-03-18T12:30:46",
  "messages": [/* array of message objects */],
  "metadata": {}
}
```

### Tickets
```json
{
  "ticket_id": "TKT-20260318123045-test_use",
  "user_id": "test_user",
  "thread_id": "conv_123",
  "issue": "Payment not processed",
  "priority": "high",
  "status": "open",
  "created_at": "2026-03-18T12:30:45",
  "updated_at": "2026-03-18T12:30:45",
  "assigned_to": "support_team",
  "resolved_at": null,
  "resolution": null,
  "metadata": {
    "estimated_response_time": "4-8 hours",
    "created_from_chat": true
  }
}
```

## Benefits

| Feature | Before | After |
|---------|--------|-------|
| **Chat History** | Lost on refresh | ✅ Persisted permanently |
| **Ticket Tracking** | Lost on refresh | ✅ All tickets saved |
| **Session Restoration** | Manual re-entry needed | ✅ Auto-restored on load |
| **Message Metadata** | Not tracked | ✅ Full context stored |
| **User History** | No per-user history | ✅ Complete user timeline |
| **Analytics Data** | Limited | ✅ Full audit trail |

## Testing

### Test 1: Send Message and Refresh
1. Open chat, send message
2. Verify message appears
3. Refresh page
4. Verify message still visible

### Test 2: Create Ticket and Refresh
1. Escalate to support (creates ticket)
2. Verify ticket shows in list
3. Refresh page
4. Verify ticket still appears

### Test 3: Multiple Sessions
1. Have conversation in Thread A
2. Start new conversation in Thread B
3. Switch back to Thread A
4. Verify Thread A history restored

### Test 4: API Endpoints
```bash
# Get chat history
curl http://localhost:8000/chat-history/test_user/thread_123

# Get user sessions
curl http://localhost:8000/user-sessions/test_user

# Get tickets
curl http://localhost:8000/user-tickets/test_user

# Init session (page load)
curl -X POST http://localhost:8000/init-session/test_user/thread_123
```

## Implementation Details

### Files Created
- ✅ `src/memory/persistent_state.py` (615 lines)
  - `PersistentStateManager` class
  - Chat, session, and ticket management
  - Helper methods for file operations

### Files Modified
- ✅ `src/memory/__init__.py` - Added exports
- ✅ `src/tools/support_ticket.py` - Integrated persistent state
- ✅ `api.py` - Updated chat endpoint + 5 new endpoints

### Classes & Dataclasses
- `ChatMessage` - Single message with metadata
- `ChatSession` - Thread with messages
- `TicketRecord` - Ticket with full details
- `PersistentStateManager` - Main manager class

### Key Methods
- `save_message()` - Save single message
- `get_chat_history()` - Retrieve messages
- `create_session()` - New conversation
- `get_all_user_threads()` - All user sessions
- `save_ticket()` - Create ticket
- `get_user_tickets()` - Get tickets
- `update_ticket()` - Update status

## Configuration

No configuration needed! The system automatically:
- Creates directories as needed
- Uses sensible defaults
- Handles errors gracefully
- Provides fallbacks

## Future Enhancements

Potential improvements:
1. **Database Backend**: Replace JSON files with PostgreSQL
2. **Search**: Full-text search across chats
3. **Export**: Download chat history as PDF
4. **Cleanup**: Archive old sessions
5. **Sync**: Sync across devices
6. **Encryption**: Encrypt sensitive data

---

**Status**: ✅ Complete - Full persistent state implementation with 5 new API endpoints
