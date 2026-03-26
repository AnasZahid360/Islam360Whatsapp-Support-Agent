"""
Support ticket creation tool.

This module provides the create_support_ticket tool that can be used
by the Escalator agent to create support tickets for unresolved issues.

Now integrated with persistent state manager for proper ticket tracking.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any
from langchain_core.tools import tool
from src.memory.persistent_state import get_persistent_state_manager


@tool
def create_support_ticket(
    issue: str,
    user_id: str,
    priority: str = "medium",
    thread_id: str = "unknown"
) -> Dict[str, Any]:
    """
    Create a support ticket for issues that cannot be resolved automatically.
    
    Args:
        issue: Description of the customer's issue
        user_id: Unique identifier for the user
        priority: Priority level (low, medium, high, urgent)
        thread_id: Thread ID for this conversation
    
    Returns:
        Dictionary with ticket information
    """
    # Generate ticket ID
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    ticket_id = f"TKT-{timestamp}-{user_id[:8]}"
    
    # Use persistent state manager
    state_manager = get_persistent_state_manager()
    
    # Save ticket with persistence
    ticket_record = state_manager.save_ticket(
        ticket_id=ticket_id,
        user_id=user_id,
        thread_id=thread_id,
        issue=issue,
        priority=priority,
        assigned_to="support_team",
        metadata={
            "estimated_response_time": _get_response_time(priority),
            "created_from_chat": True
        }
    )
    
    # Return as dict for backward compatibility
    return {
        "ticket_id": ticket_record.ticket_id,
        "user_id": ticket_record.user_id,
        "issue": ticket_record.issue,
        "priority": ticket_record.priority,
        "status": ticket_record.status,
        "created_at": ticket_record.created_at,
        "assigned_to": ticket_record.assigned_to,
        "estimated_response_time": ticket_record.metadata.get("estimated_response_time") if ticket_record.metadata else _get_response_time(priority)
    }


def _get_response_time(priority: str) -> str:
    """
    Get estimated response time based on priority.
    
    Args:
        priority: Ticket priority level
    
    Returns:
        Estimated response time string
    """
    response_times = {
        "low": "3-5 business days",
        "medium": "1-2 business days",
        "high": "4-8 hours",
        "urgent": "1-2 hours"
    }
    return response_times.get(priority, "1-2 business days")


def get_user_tickets(user_id: str) -> Dict[str, Any]:
    """
    Get all tickets for a user.
    
    Args:
        user_id: User identifier
    
    Returns:
        Dictionary with user tickets
    """
    state_manager = get_persistent_state_manager()
    tickets = state_manager.get_user_tickets(user_id)
    
    return {
        "user_id": user_id,
        "total_tickets": len(tickets),
        "tickets": [
            {
                "ticket_id": t.ticket_id,
                "issue": t.issue,
                "priority": t.priority,
                "status": t.status,
                "created_at": t.created_at,
                "updated_at": t.updated_at
            }
            for t in tickets
        ]
    }


def get_ticket_by_id(user_id: str, ticket_id: str) -> Dict[str, Any]:
    """
    Retrieve a ticket by its ID.
    
    Args:
        user_id: User identifier
        ticket_id: Ticket identifier
    
    Returns:
        Ticket data or error message
    """
    state_manager = get_persistent_state_manager()
    ticket = state_manager.get_ticket(user_id, ticket_id)
    
    if not ticket:
        return {"error": f"Ticket {ticket_id} not found"}
    
    return {
        "ticket_id": ticket.ticket_id,
        "user_id": ticket.user_id,
        "issue": ticket.issue,
        "priority": ticket.priority,
        "status": ticket.status,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "assigned_to": ticket.assigned_to,
        "resolved_at": ticket.resolved_at,
        "resolution": ticket.resolution
    }

