"""
Persistent state manager for chat history and tickets.

This module manages saving and retrieving:
1. Chat history - all messages in a conversation
2. Tickets - support tickets created during conversations
3. User sessions - metadata about user interactions
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Represents a single chat message with metadata"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    message_id: str
    thread_id: str
    user_id: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChatSession:
    """Represents a chat conversation thread"""
    thread_id: str
    user_id: str
    created_at: str
    last_updated: str
    messages: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TicketRecord:
    """Represents a support ticket with full metadata"""
    ticket_id: str
    user_id: str
    thread_id: str
    issue: str
    priority: str
    status: str
    created_at: str
    updated_at: str
    assigned_to: str
    resolved_at: Optional[str] = None
    resolution: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PersistentStateManager:
    """
    Manages persistent storage of chat history and tickets.
    
    Directory structure:
    data/
    ├── chats/
    │   ├── user_{user_id}/
    │   │   ├── thread_{thread_id}.json
    │   │   └── sessions.json (index of all sessions)
    │   └── chat_index.jsonl (master index)
    ├── tickets/
    │   ├── user_{user_id}/
    │   │   ├── ticket_{ticket_id}.json
    │   │   └── tickets.json (index)
    │   ├── all_tickets.jsonl (master log)
    │   └── ticket_index.json (searchable index)
    └── sessions/
        ├── user_{user_id}.json
        └── active_sessions.jsonl
    """
    
    BASE_DIR = "data"
    CHATS_DIR = os.path.join(BASE_DIR, "chats")
    TICKETS_DIR = os.path.join(BASE_DIR, "tickets")
    SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
    
    def __init__(self):
        """Initialize directories"""
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        for directory in [self.CHATS_DIR, self.TICKETS_DIR, self.SESSIONS_DIR]:
            os.makedirs(directory, exist_ok=True)
    
    # ==================== CHAT HISTORY ====================
    
    def save_message(
        self,
        user_id: str,
        thread_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """
        Save a single message to chat history.
        
        Args:
            user_id: User identifier
            thread_id: Thread identifier
            role: Message role ("user" or "assistant")
            content: Message content
            metadata: Optional metadata (docs, scores, etc.)
        
        Returns:
            ChatMessage object
        """
        timestamp = datetime.now().isoformat()
        message_id = f"{thread_id}-{datetime.now().timestamp()}"
        
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=timestamp,
            message_id=message_id,
            thread_id=thread_id,
            user_id=user_id,
            metadata=metadata
        )
        
        # Save to user-specific thread file
        thread_file = self._get_thread_file(user_id, thread_id)
        self._append_to_json_list(thread_file, asdict(message))
        
        # Update session last_updated
        self._update_session_timestamp(user_id, thread_id)
        
        # Append to master chat index
        master_index = os.path.join(self.CHATS_DIR, "chat_index.jsonl")
        self._append_to_jsonl(master_index, asdict(message))
        
        logger.info(f"Saved message {message_id} to thread {thread_id}")
        return message
    
    def get_chat_history(
        self,
        user_id: str,
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[ChatMessage]:
        """
        Retrieve chat history for a thread.
        
        Args:
            user_id: User identifier
            thread_id: Thread identifier
            limit: Maximum number of messages to retrieve (None = all)
        
        Returns:
            List of ChatMessage objects
        """
        thread_file = self._get_thread_file(user_id, thread_id)
        
        if not os.path.exists(thread_file):
            return []
        
        try:
            with open(thread_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
        
        # Convert to ChatMessage objects
        messages = [ChatMessage(**msg) for msg in data]
        
        # Apply limit (most recent messages)
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def get_all_user_threads(self, user_id: str) -> List[ChatSession]:
        """
        Get all threads for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            List of ChatSession objects
        """
        user_sessions_file = os.path.join(self.SESSIONS_DIR, f"{user_id}.json")
        
        if not os.path.exists(user_sessions_file):
            return []
        
        try:
            with open(user_sessions_file, 'r', encoding='utf-8') as f:
                sessions_data = json.load(f)
            return [ChatSession(**s) for s in sessions_data]
        except (json.JSONDecodeError, IOError):
            return []
    
    def create_session(
        self,
        user_id: str,
        thread_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatSession:
        """
        Create a new chat session.
        
        Args:
            user_id: User identifier
            thread_id: Thread identifier
            metadata: Optional metadata
        
        Returns:
            ChatSession object
        """
        now = datetime.now().isoformat()
        
        session = ChatSession(
            thread_id=thread_id,
            user_id=user_id,
            created_at=now,
            last_updated=now,
            messages=[],
            metadata=metadata
        )
        
        # Save to user sessions file
        user_sessions_file = os.path.join(self.SESSIONS_DIR, f"{user_id}.json")
        sessions = self.get_all_user_threads(user_id)
        sessions.append(session)
        
        with open(user_sessions_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(s) for s in sessions], f, indent=2)
        
        # Append to active sessions log
        active_sessions_file = os.path.join(self.SESSIONS_DIR, "active_sessions.jsonl")
        self._append_to_jsonl(active_sessions_file, asdict(session))
        
        logger.info(f"Created session {thread_id} for user {user_id}")
        return session
    
    # ==================== TICKET MANAGEMENT ====================
    
    def save_ticket(
        self,
        ticket_id: str,
        user_id: str,
        thread_id: str,
        issue: str,
        priority: str = "medium",
        assigned_to: str = "support_team",
        metadata: Optional[Dict[str, Any]] = None
    ) -> TicketRecord:
        """
        Save a support ticket.
        
        Args:
            ticket_id: Ticket identifier
            user_id: User identifier
            thread_id: Thread identifier
            issue: Issue description
            priority: Priority level
            assigned_to: Assigned person/team
            metadata: Optional metadata
        
        Returns:
            TicketRecord object
        """
        now = datetime.now().isoformat()
        
        ticket = TicketRecord(
            ticket_id=ticket_id,
            user_id=user_id,
            thread_id=thread_id,
            issue=issue,
            priority=priority,
            status="open",
            created_at=now,
            updated_at=now,
            assigned_to=assigned_to,
            metadata=metadata
        )
        
        # Save to user-specific ticket file
        user_ticket_dir = os.path.join(self.TICKETS_DIR, f"user_{user_id}")
        os.makedirs(user_ticket_dir, exist_ok=True)
        
        ticket_file = os.path.join(user_ticket_dir, f"{ticket_id}.json")
        with open(ticket_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(ticket), f, indent=2)
        
        # Update user's ticket index
        self._add_to_user_tickets(user_id, ticket)
        
        # Append to master log
        all_tickets_log = os.path.join(self.TICKETS_DIR, "all_tickets.jsonl")
        self._append_to_jsonl(all_tickets_log, asdict(ticket))
        
        # Update searchable index
        self._update_ticket_index(ticket)
        
        logger.info(f"Saved ticket {ticket_id} for user {user_id}")
        return ticket
    
    def get_user_tickets(self, user_id: str) -> List[TicketRecord]:
        """
        Get all tickets for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            List of TicketRecord objects
        """
        user_ticket_dir = os.path.join(self.TICKETS_DIR, f"user_{user_id}")
        
        if not os.path.exists(user_ticket_dir):
            return []
        
        tickets = []
        for filename in os.listdir(user_ticket_dir):
            if filename.endswith('.json') and filename != 'tickets.json':
                filepath = os.path.join(user_ticket_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        tickets.append(TicketRecord(**data))
                except (json.JSONDecodeError, IOError, TypeError):
                    continue
        
        # Sort by created_at descending
        tickets.sort(key=lambda t: t.created_at, reverse=True)
        return tickets
    
    def get_ticket(self, user_id: str, ticket_id: str) -> Optional[TicketRecord]:
        """
        Get a specific ticket.
        
        Args:
            user_id: User identifier
            ticket_id: Ticket identifier
        
        Returns:
            TicketRecord or None
        """
        user_ticket_dir = os.path.join(self.TICKETS_DIR, f"user_{user_id}")
        ticket_file = os.path.join(user_ticket_dir, f"{ticket_id}.json")
        
        if not os.path.exists(ticket_file):
            return None
        
        try:
            with open(ticket_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return TicketRecord(**data)
        except (json.JSONDecodeError, IOError, TypeError):
            return None
    
    def update_ticket(
        self,
        user_id: str,
        ticket_id: str,
        status: Optional[str] = None,
        resolution: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[TicketRecord]:
        """
        Update a ticket status and/or resolution.
        
        Args:
            user_id: User identifier
            ticket_id: Ticket identifier
            status: New status (e.g., "resolved", "closed")
            resolution: Resolution description
            metadata: Additional metadata to merge
        
        Returns:
            Updated TicketRecord or None
        """
        ticket = self.get_ticket(user_id, ticket_id)
        if not ticket:
            return None
        
        now = datetime.now().isoformat()
        ticket.updated_at = now
        
        if status:
            ticket.status = status
        
        if resolution:
            ticket.resolution = resolution
            ticket.resolved_at = now
        
        if metadata:
            if ticket.metadata is None:
                ticket.metadata = {}
            ticket.metadata.update(metadata)
        
        # Save updated ticket
        user_ticket_dir = os.path.join(self.TICKETS_DIR, f"user_{user_id}")
        ticket_file = os.path.join(user_ticket_dir, f"{ticket_id}.json")
        
        with open(ticket_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(ticket), f, indent=2)
        
        logger.info(f"Updated ticket {ticket_id} status to {status}")
        return ticket
    
    # ==================== HELPER METHODS ====================
    
    def _get_thread_file(self, user_id: str, thread_id: str) -> str:
        """Get the file path for a thread"""
        user_dir = os.path.join(self.CHATS_DIR, f"user_{user_id}")
        os.makedirs(user_dir, exist_ok=True)
        return os.path.join(user_dir, f"thread_{thread_id}.json")
    
    def _append_to_json_list(self, filepath: str, item: Any):
        """Append item to JSON array file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        data = []
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                data = []
        
        data.append(item)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def _append_to_jsonl(self, filepath: str, item: Any):
        """Append item to JSONL file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(item) + '\n')
    
    def _update_session_timestamp(self, user_id: str, thread_id: str):
        """Update last_updated timestamp for a session"""
        sessions = self.get_all_user_threads(user_id)
        
        for session in sessions:
            if session.thread_id == thread_id:
                session.last_updated = datetime.now().isoformat()
                break
        
        user_sessions_file = os.path.join(self.SESSIONS_DIR, f"{user_id}.json")
        with open(user_sessions_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(s) for s in sessions], f, indent=2)
    
    def _add_to_user_tickets(self, user_id: str, ticket: TicketRecord):
        """Add ticket to user's ticket index"""
        user_ticket_dir = os.path.join(self.TICKETS_DIR, f"user_{user_id}")
        os.makedirs(user_ticket_dir, exist_ok=True)
        
        tickets_index_file = os.path.join(user_ticket_dir, "tickets.json")
        tickets = []
        
        if os.path.exists(tickets_index_file):
            try:
                with open(tickets_index_file, 'r', encoding='utf-8') as f:
                    tickets = json.load(f)
            except (json.JSONDecodeError, IOError):
                tickets = []
        
        # Add ticket reference
        tickets.append({
            "ticket_id": ticket.ticket_id,
            "created_at": ticket.created_at,
            "status": ticket.status,
            "priority": ticket.priority
        })
        
        with open(tickets_index_file, 'w', encoding='utf-8') as f:
            json.dump(tickets, f, indent=2)
    
    def _update_ticket_index(self, ticket: TicketRecord):
        """Update searchable ticket index"""
        index_file = os.path.join(self.TICKETS_DIR, "ticket_index.json")
        
        index = {}
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
            except (json.JSONDecodeError, IOError):
                index = {}
        
        # Index by user_id and ticket_id
        if ticket.user_id not in index:
            index[ticket.user_id] = {}
        
        index[ticket.user_id][ticket.ticket_id] = {
            "status": ticket.status,
            "priority": ticket.priority,
            "created_at": ticket.created_at,
            "thread_id": ticket.thread_id
        }
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)


# Global singleton
_persistent_state_manager: Optional[PersistentStateManager] = None


def get_persistent_state_manager() -> PersistentStateManager:
    """Get or create the persistent state manager"""
    global _persistent_state_manager
    if _persistent_state_manager is None:
        _persistent_state_manager = PersistentStateManager()
    return _persistent_state_manager
