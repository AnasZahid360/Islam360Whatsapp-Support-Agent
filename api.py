"""
FastAPI backend for the MakTek Multi-Agent RAG System.
"""

import os
import sys
import base64
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.graph import create_graph_with_store
from src.state import create_initial_state
from src.memory.memory_manager import get_memory_manager
from src.memory.persistent_state import get_persistent_state_manager
from src.voice.livekit_token_manager import get_token_manager
from livekit.api import agent_dispatch_service, LiveKitAPI
from src.guardrails.abuse_monitor import abuse_monitor
from src.guardrails.abuse_detector import detect_abuse

# Load environment variables
load_dotenv()

app = FastAPI(title="MakTek Support API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize graph and memory manager
graph, memory_manager = create_graph_with_store()
persistent_state = get_persistent_state_manager()

class ChatRequest(BaseModel):
    message: str
    user_id: str
    thread_id: str
    config_overrides: Optional[Dict[str, Any]] = None
    return_tts: bool = False

class ChatResponse(BaseModel):
    response: str
    sender: str = "assistant"
    thread_id: str
    user_id: str
    docs: Optional[List[Dict[str, Any]]] = None
    tts_audio_base64: Optional[str] = None
    tts_audio_mime_type: Optional[str] = None

class AbuseDetectionResult(BaseModel):
    has_abuse: bool
    abuse_type: str
    severity: str
    violation_count: int

class UserAbuseReport(BaseModel):
    user_id: str
    total_violations: int
    severity_breakdown: Dict[str, int]
    type_breakdown: Dict[str, int]
    should_block: bool
    recent_incidents: Optional[List[Dict[str, Any]]] = None

class SystemAbuseReport(BaseModel):
    total_incidents: int
    unique_users: int
    unique_sessions: int
    severity_breakdown: Dict[str, int]
    type_breakdown: Dict[str, int]

class ChatHistoryMessage(BaseModel):
    role: str
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None

class ChatHistoryResponse(BaseModel):
    user_id: str
    thread_id: str
    messages: List[ChatHistoryMessage]

class ChatSessionInfo(BaseModel):
    thread_id: str
    created_at: str
    last_updated: str
    message_count: int

class UserSessionsResponse(BaseModel):
    user_id: str
    total_sessions: int
    sessions: List[ChatSessionInfo]

class TicketInfo(BaseModel):
    ticket_id: str
    issue: str
    priority: str
    status: str
    created_at: str
    updated_at: str

class UserTicketsResponse(BaseModel):
    user_id: str
    total_tickets: int
    tickets: List[TicketInfo]

class CreateTicketRequest(BaseModel):
    user_id: str
    thread_id: str = "voice_thread"
    issue: str
    priority: str = "medium"

class LiveKitTokenRequest(BaseModel):
    user_id: str
    room_name: str = "support-agent"
    duration_minutes: int = 60

class LiveKitTokenResponse(BaseModel):
    token: str
    url: str
    room: str
    identity: str

def _serialize_message(msg: BaseMessage) -> Dict[str, Any]:
    return {
        "type": msg.type,
        "content": msg.content
    }


def _synthesize_tts_base64(text: str) -> Optional[str]:
    use_separate_tts_key = os.getenv("USE_SEPARATE_OPENAI_TTS_KEY", "false").lower() == "true"
    tts_key = os.getenv("OPENAI_API_KEY")
    if use_separate_tts_key and os.getenv("OPENAI_TTS_API_KEY"):
        tts_key = os.getenv("OPENAI_TTS_API_KEY")

    if not tts_key or not text.strip():
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=tts_key)
        speech = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=text[:4000],
            response_format="mp3",
        )
        audio_bytes = speech.read()
        return base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as tts_error:
        print(f"TTS generation failed: {tts_error}")
        return None

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Expose the chatbot logic as an API endpoint.
    Automatically saves chat history for persistence.
    """
    try:
        # Ensure session exists
        persistent_state.create_session(request.user_id, request.thread_id)
        
        # Save user message
        persistent_state.save_message(
            user_id=request.user_id,
            thread_id=request.thread_id,
            role="user",
            content=request.message,
            metadata={"config_overrides": request.config_overrides}
        )
        
        # Configuration for the graph
        config = {
            "configurable": {
                "thread_id": request.thread_id,
                "user_id": request.user_id
            }
        }
        
        # Increment interaction count for user preferences
        await memory_manager.increment_interaction_count(request.user_id)
        
        # Only pass the new message — LangGraph restores all other state
        # (escalation_status, thread_id, etc.) from its checkpoint automatically.
        # Passing a full state would overwrite the checkpoint and break multi-turn flows.
        state = {
            "messages": [HumanMessage(content=request.message)],
            "user_id": request.user_id,
            "thread_id": request.thread_id,
            "config": request.config_overrides or {},
        }
        
        final_response = ""
        retrieved_docs = []
        
        # Execute the graph
        async for event in graph.astream(state, config, stream_mode="values"):
            if "messages" in event and event["messages"]:
                last_msg = event["messages"][-1]
                if last_msg.type == "ai":
                    final_response = last_msg.content
                
                # Capture retrieved docs if available in state
                if "retrieved_docs" in event:
                    retrieved_docs = event["retrieved_docs"]

        if not final_response:
            raise HTTPException(status_code=500, detail="Failed to generate a response")

        # Save assistant response
        persistent_state.save_message(
            user_id=request.user_id,
            thread_id=request.thread_id,
            role="assistant",
            content=final_response,
            metadata={"retrieved_docs_count": len(retrieved_docs)}
        )

        tts_audio_base64 = _synthesize_tts_base64(final_response) if request.return_tts else None

        return ChatResponse(
            response=final_response,
            thread_id=request.thread_id,
            user_id=request.user_id,
            docs=retrieved_docs,
            tts_audio_base64=tts_audio_base64,
            tts_audio_mime_type="audio/mpeg" if tts_audio_base64 else None,
        )

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice-chat")
async def voice_chat_endpoint(
    audio: UploadFile = File(..., description="Audio file (mp3, wav, ogg, m4a, webm, etc.)"),
    user_id: str = Form(...),
    thread_id: str = Form(...),
):
    """
    Deprecated endpoint. Voice is now handled via LiveKit rooms.
    """
    _ = audio
    _ = user_id
    _ = thread_id
    raise HTTPException(
        status_code=410,
        detail="/voice-chat is deprecated. Use LiveKit flow: request token from /livekit-token and connect through frontend/livekit-integration.js"
    )


@app.post("/abuse/detect", response_model=AbuseDetectionResult)
async def detect_abuse_endpoint(message: str):
    """
    Detect abuse in a given message.
    
    Returns:
    - has_abuse: Whether abuse was detected
    - abuse_type: Type of abuse (profanity, harassment, hate_speech, spam)
    - severity: Severity level (low, medium, high, critical)
    - violation_count: Number of violations found
    """
    has_abuse, abuse_type, severity, violation_count = detect_abuse(message)
    
    return AbuseDetectionResult(
        has_abuse=has_abuse,
        abuse_type=abuse_type,
        severity=severity,
        violation_count=violation_count
    )


@app.get("/abuse/user/{user_id}", response_model=UserAbuseReport)
async def get_user_abuse_report(user_id: str):
    """
    Get abuse violation report for a specific user.
    
    Returns:
    - total_violations: Total number of violations
    - severity_breakdown: Count by severity level
    - type_breakdown: Count by abuse type
    - should_block: Whether user should be blocked
    - recent_incidents: Last 5 incidents
    """
    report = abuse_monitor.generate_user_report(user_id)
    
    return UserAbuseReport(
        user_id=user_id,
        total_violations=report["total_violations"],
        severity_breakdown=report["severity_breakdown"],
        type_breakdown=report["type_breakdown"],
        should_block=report["should_block"],
        recent_incidents=report["incidents"][-5:] if report["incidents"] else None
    )


@app.get("/abuse/session/{thread_id}")
async def get_session_abuse_report(thread_id: str):
    """
    Get abuse violations for a specific session/thread.
    
    Returns list of abuse incidents in the thread.
    """
    violations = abuse_monitor.get_session_violations(thread_id)
    
    return {
        "thread_id": thread_id,
        "total_violations": len(violations),
        "incidents": [
            {
                "timestamp": v.timestamp,
                "abuse_type": v.abuse_type,
                "severity": v.severity,
                "message_preview": v.message_preview,
                "ticket_id": v.ticket_id,
                "action_taken": v.action_taken,
            }
            for v in violations
        ]
    }


@app.get("/abuse/system-report", response_model=SystemAbuseReport)
async def get_system_abuse_report():
    """
    Get system-wide abuse report.
    
    Returns aggregate statistics across all users and sessions.
    """
    report = abuse_monitor.generate_system_report()
    
    return SystemAbuseReport(
        total_incidents=report["total_incidents"],
        unique_users=report["unique_users"],
        unique_sessions=report["unique_sessions"],
        severity_breakdown=report["severity_breakdown"],
        type_breakdown=report["type_breakdown"]
    )


@app.get("/abuse/user/{user_id}/violations")
async def get_user_violations(user_id: str, severity: Optional[str] = None):
    """
    Get violation count for a user, optionally filtered by severity.
    """
    count = abuse_monitor.get_user_violation_count(user_id, severity)
    
    return {
        "user_id": user_id,
        "severity_filter": severity or "all",
        "violation_count": count,
        "should_block": abuse_monitor.should_block_user(user_id)
    }


@app.get("/abuse/user/{user_id}/status")
async def get_user_abuse_status(user_id: str):
    """
    Get quick status check for a user.
    """
    violations = abuse_monitor.get_user_violations(user_id)
    
    # Summarize recent violations
    recent_types = {}
    for v in violations[-5:]:  # Last 5
        recent_types[v.abuse_type] = recent_types.get(v.abuse_type, 0) + 1
    
    return {
        "user_id": user_id,
        "total_violations": len(violations),
        "should_block": abuse_monitor.should_block_user(user_id),
        "recent_violation_types": recent_types,
        "latest_incident": {
            "timestamp": violations[-1].timestamp,
            "severity": violations[-1].severity,
            "type": violations[-1].abuse_type,
        } if violations else None
    }


@app.post("/abuse/check-and-flag")
async def check_and_flag_message(user_id: str, thread_id: str, message: str):
    """
    Check a message for abuse and automatically flag/escalate if needed.
    
    Returns both detection result and user status.
    """
    # Detect abuse
    has_abuse, abuse_type, severity, violation_count = detect_abuse(message)
    
    if has_abuse:
        # Check user status
        user_violations = abuse_monitor.get_user_violation_count(user_id)
        session_violations = abuse_monitor.get_session_violation_count(thread_id)
        should_escalate = abuse_monitor.should_escalate_to_human(thread_id)
        should_block = abuse_monitor.should_block_user(user_id)
    
    return {
        "abuse_detected": has_abuse,
        "abuse_type": abuse_type,
        "severity": severity,
        "violations_in_message": violation_count,
        "user_total_violations": abuse_monitor.get_user_violation_count(user_id) if has_abuse else 0,
        "session_violations": abuse_monitor.get_session_violation_count(thread_id) if has_abuse else 0,
        "should_escalate_to_human": abuse_monitor.should_escalate_to_human(thread_id) if has_abuse else False,
        "should_block_user": abuse_monitor.should_block_user(user_id) if has_abuse else False,
        "action_recommended": _get_recommended_action(severity, abuse_monitor.get_session_violation_count(thread_id)) if has_abuse else "none"
    }


# ==================== PERSISTENT STATE ENDPOINTS ====================

@app.get("/chat-history/{user_id}/{thread_id}", response_model=ChatHistoryResponse)
async def get_chat_history(user_id: str, thread_id: str, limit: Optional[int] = None):
    """
    Retrieve chat history for a specific thread.
    
    Args:
        user_id: User identifier
        thread_id: Thread identifier
        limit: Optional limit on number of messages (default: all)
    
    Returns:
        Chat history with messages
    """
    messages = persistent_state.get_chat_history(user_id, thread_id, limit=limit)
    
    return ChatHistoryResponse(
        user_id=user_id,
        thread_id=thread_id,
        messages=[
            ChatHistoryMessage(
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp,
                metadata=msg.metadata
            )
            for msg in messages
        ]
    )


@app.get("/user-sessions/{user_id}", response_model=UserSessionsResponse)
async def get_user_sessions(user_id: str):
    """
    Get all chat sessions for a user.
    
    Args:
        user_id: User identifier
    
    Returns:
        List of chat sessions with metadata
    """
    sessions = persistent_state.get_all_user_threads(user_id)
    
    return UserSessionsResponse(
        user_id=user_id,
        total_sessions=len(sessions),
        sessions=[
            ChatSessionInfo(
                thread_id=session.thread_id,
                created_at=session.created_at,
                last_updated=session.last_updated,
                message_count=len(session.messages)
            )
            for session in sessions
        ]
    )


@app.post("/create-ticket")
async def create_ticket_endpoint(request: CreateTicketRequest):
    """
    Directly create a support ticket — used by the voice agent.
    """
    from src.tools.support_ticket import create_support_ticket as _create_ticket
    from datetime import datetime
    ticket_id = f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{request.user_id[:8]}"
    persistent_state.create_session(request.user_id, request.thread_id)
    ticket = _create_ticket.invoke({
        "issue": request.issue,
        "user_id": request.user_id,
        "priority": request.priority,
        "thread_id": request.thread_id,
    })
    return {
        "ticket_id": ticket["ticket_id"],
        "issue": ticket["issue"],
        "priority": ticket["priority"],
        "status": ticket["status"],
        "created_at": ticket["created_at"],
        "estimated_response_time": ticket["estimated_response_time"],
    }


@app.get("/user-tickets/{user_id}", response_model=UserTicketsResponse)
async def get_user_tickets(user_id: str):
    """
    Get all support tickets for a user.
    
    Args:
        user_id: User identifier
    
    Returns:
        List of tickets with status
    """
    tickets = persistent_state.get_user_tickets(user_id)
    
    return UserTicketsResponse(
        user_id=user_id,
        total_tickets=len(tickets),
        tickets=[
            TicketInfo(
                ticket_id=ticket.ticket_id,
                issue=ticket.issue,
                priority=ticket.priority,
                status=ticket.status,
                created_at=ticket.created_at,
                updated_at=ticket.updated_at
            )
            for ticket in tickets
        ]
    )


@app.get("/ticket/{user_id}/{ticket_id}")
async def get_ticket_details(user_id: str, ticket_id: str):
    """
    Get detailed information about a specific ticket.
    
    Args:
        user_id: User identifier
        ticket_id: Ticket identifier
    
    Returns:
        Complete ticket information
    """
    ticket = persistent_state.get_ticket(user_id, ticket_id)
    
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    
    return {
        "ticket_id": ticket.ticket_id,
        "user_id": ticket.user_id,
        "thread_id": ticket.thread_id,
        "issue": ticket.issue,
        "priority": ticket.priority,
        "status": ticket.status,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "assigned_to": ticket.assigned_to,
        "resolved_at": ticket.resolved_at,
        "resolution": ticket.resolution,
        "metadata": ticket.metadata
    }


@app.post("/init-session/{user_id}/{thread_id}")
async def initialize_session(user_id: str, thread_id: str):
    """
    Initialize a new chat session (called on page load).
    
    Args:
        user_id: User identifier
        thread_id: Thread identifier
    
    Returns:
        Session info with previous chat history
    """
    # Create or retrieve session
    session = persistent_state.create_session(user_id, thread_id)
    
    # Get chat history
    messages = persistent_state.get_chat_history(user_id, thread_id)
    
    # Get tickets
    tickets = persistent_state.get_user_tickets(user_id)
    
    return {
        "success": True,
        "user_id": user_id,
        "thread_id": thread_id,
        "session": {
            "created_at": session.created_at,
            "last_updated": session.last_updated
        },
        "chat_history": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp
            }
            for msg in messages
        ],
        "tickets": [
            {
                "ticket_id": t.ticket_id,
                "issue": t.issue,
                "priority": t.priority,
                "status": t.status,
                "created_at": t.created_at
            }
            for t in tickets
        ]
    }

def _get_recommended_action(severity: str, session_violations: int) -> str:
    """Recommend an action based on severity and session history."""
    if severity == "critical":
        return "terminate_conversation"
    elif severity == "high":
        return "escalate_to_human"
    elif severity == "medium":
        if session_violations > 2:
            return "escalate_to_human"
        return "warn_user"
    else:  # low
        return "warn_user"


@app.post("/livekit-token", response_model=LiveKitTokenResponse)
async def get_livekit_token(request: LiveKitTokenRequest):
    """
    Generate a LiveKit access token for the frontend to join a room,
    and explicitly dispatch the maktek-support agent to that room.
    
    Args:
        request: LiveKitTokenRequest containing user_id and room_name
        
    Returns:
        LiveKitTokenResponse with the token and connection details
    """
    try:
        token_manager = get_token_manager()

        token = token_manager.create_token(
            user_id=request.user_id,
            room_name=request.room_name,
            duration_minutes=request.duration_minutes,
            can_publish=True,
            can_subscribe=True,
        )

        livekit_url = os.getenv("LIVEKIT_API_URL", "ws://localhost:7880")
        api_key = os.getenv("LIVEKIT_API_KEY")
        api_secret = os.getenv("LIVEKIT_API_SECRET")

        # Explicitly dispatch the maktek-support agent to this room
        try:
            async with LiveKitAPI(
                url=livekit_url,
                api_key=api_key,
                api_secret=api_secret,
            ) as lk:
                dispatch_req = agent_dispatch_service.CreateAgentDispatchRequest(
                    agent_name="maktek-support",
                    room=request.room_name,
                )
                dispatch = await lk.agent_dispatch.create_dispatch(dispatch_req)
                print(f"✓ Agent dispatched: {dispatch.agent_name} → room '{request.room_name}'")
        except Exception as dispatch_err:
            # Don't fail the token request if dispatch has an error
            print(f"⚠ Agent dispatch warning (agent may already be in room): {dispatch_err}")

        return LiveKitTokenResponse(
            token=token,
            url=livekit_url,
            room=request.room_name,
            identity=request.user_id,
        )
    except Exception as e:
        print(f"Error generating LiveKit token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
