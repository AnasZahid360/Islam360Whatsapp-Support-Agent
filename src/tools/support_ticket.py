"""
Support ticket creation tool.

This module provides the create_support_ticket tool that can be used
by the Escalator agent to create support tickets for unresolved issues.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any
from langchain_core.tools import tool


@tool
def create_support_ticket(issue: str, user_id: str, priority: str = "medium") -> Dict[str, Any]:
    """
    Create a support ticket for issues that cannot be resolved automatically.
    
    Args:
        issue: Description of the customer's issue
        user_id: Unique identifier for the user
        priority: Priority level (low, medium, high, urgent)
    
    Returns:
        Dictionary with ticket information
    """
    # Generate ticket ID
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    ticket_id = f"TKT-{timestamp}-{user_id[:8]}"
    
    # Create ticket data
    ticket = {
        "ticket_id": ticket_id,
        "user_id": user_id,
        "issue": issue,
        "priority": priority,
        "status": "open",
        "created_at": datetime.now().isoformat(),
        "assigned_to": "support_team",
        "estimated_response_time": _get_response_time(priority)
    }
    
    # Save ticket to file (mock persistence)
    _save_ticket(ticket)
    
    return ticket


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


def _save_ticket(ticket: Dict[str, Any]) -> None:
    """
    Save ticket to JSON file (mock ticket system).
    
    Args:
        ticket: Ticket data dictionary
    """
    tickets_dir = "data/tickets"
    os.makedirs(tickets_dir, exist_ok=True)
    
    ticket_file = os.path.join(tickets_dir, f"{ticket['ticket_id']}.json")
    
    with open(ticket_file, 'w', encoding='utf-8') as f:
        json.dump(ticket, f, indent=2)
    
    # Also append to master log
    log_file = os.path.join(tickets_dir, "tickets_log.jsonl")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(ticket) + '\n')
    
    print(f"✓ Ticket {ticket['ticket_id']} created and saved")


def get_ticket_by_id(ticket_id: str) -> Dict[str, Any]:
    """
    Retrieve a ticket by its ID.
    
    Args:
        ticket_id: Ticket identifier
    
    Returns:
        Ticket data or None if not found
    """
    ticket_file = f"data/tickets/{ticket_id}.json"
    
    if not os.path.exists(ticket_file):
        return None
    
    with open(ticket_file, 'r', encoding='utf-8') as f:
        return json.load(f)
