"""
Abuse and Bad Words Detector Guardrail.

This module detects and handles abusive language, profanity, harassment,
and toxic behavior by filtering messages and initiating protocols.
"""

import re
from datetime import datetime
from typing import Literal, Tuple, List, Dict, Any
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command
from src.state import AgentState
from src.tools.support_ticket import create_support_ticket
from src.guardrails.config import GuardrailConfig, ABUSEDetectionConfig
from src.guardrails.abuse_monitor import AbuseMonitor, AbuseIncident


# Get configuration
config = GuardrailConfig()
abuse_config = ABUSEDetectionConfig()
monitor = AbuseMonitor()

# Use patterns from config
BAD_WORDS = abuse_config.PROFANITY_PATTERNS + abuse_config.HATE_SPEECH_PATTERNS
HARASSMENT_PATTERNS = abuse_config.HARASSMENT_PATTERNS
SPAM_PATTERNS = abuse_config.SPAM_PATTERNS


def detect_abuse(text: str) -> Tuple[bool, str, str, int]:
    """
    Detect abusive content in user message.
    
    Args:
        text: The user message to check
        
    Returns:
        Tuple of (has_abuse, abuse_type, severity, count)
        - has_abuse: Whether abuse was detected
        - abuse_type: Type of abuse detected
        - severity: "low", "medium", "high", "critical"
        - count: Number of violations found
    """
    text_lower = text.lower()
    violations = []
    
    # Check for profanity
    for pattern in abuse_config.PROFANITY_PATTERNS:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            violations.append(("profanity", matches))
    
    # Check for hate speech
    for pattern in abuse_config.HATE_SPEECH_PATTERNS:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            violations.append(("hate_speech", matches))
    
    # Check for harassment
    for pattern in abuse_config.HARASSMENT_PATTERNS:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            violations.append(("harassment", matches))
    
    # Check for spam
    for pattern in abuse_config.SPAM_PATTERNS:
        matches = re.findall(pattern, text_lower)
        if matches:
            violations.append(("spam", matches))
    
    # Determine severity based on type and frequency
    if not violations:
        return False, "none", "none", 0
    
    violation_types = [v[0] for v in violations]
    violation_count = len(violations)
    
    # Determine severity
    if "hate_speech" in violation_types:
        severity = "critical"
    elif "profanity" in violation_types:
        if "harassment" in violation_types:
            severity = "critical"
        else:
            severity = "high"
    elif "harassment" in violation_types:
        severity = "high"
    elif "spam" in violation_types:
        if violation_count > 2:
            severity = "high"
        else:
            severity = "medium"
    else:
        severity = "low"
    
    primary_type = violations[0][0]
    
    return True, primary_type, severity, violation_count


def _create_abuse_ticket(
    state: AgentState,
    abuse_type: str,
    severity: str,
    violation_text: str,
    pattern_matched: str
) -> str:
    """
    Create a support ticket for abuse/harassment incidents.
    
    Args:
        state: Current agent state
        abuse_type: Type of abuse detected
        severity: Severity level
        violation_text: The actual text that violated
        pattern_matched: What pattern was matched
        
    Returns:
        Ticket ID
    """
    ticket_data = {
        "type": "ABUSE_REPORT",
        "severity": severity.upper(),
        "abuse_type": abuse_type,
        "user_id": state.get("user_id", "UNKNOWN"),
        "thread_id": state.get("thread_id", "UNKNOWN"),
        "violation_text": violation_text[:200],  # Truncate for safety
        "pattern_matched": pattern_matched,
        "description": f"User ({state.get('user_id', 'UNKNOWN')}) sent a message containing {abuse_type}. Severity: {severity}. This message has been flagged and requires review.",
        "category": "Safety/Abuse",
        "priority": "HIGH" if severity in ["high", "critical"] else "MEDIUM",
    }
    
    try:
        ticket_id = create_support_ticket(ticket_data)
        return ticket_id
    except Exception as e:
        print(f"⚠️  Failed to create abuse ticket: {e}")
        return "TICKET_CREATION_FAILED"


async def abuse_detector_node(
    state: AgentState
) -> Command[Literal["__end__", "supervisor"]]:
    """
    Abuse detector guardrail node.
    
    This node checks for abusive language, profanity, harassment, and
    initiates appropriate protocols when abuse is detected.
    
    Protocols:
    1. LOW severity: Warning message, continue conversation
    2. MEDIUM severity: Warning with note to support team
    3. HIGH severity: Create ticket, warn user, offer escalation
    4. CRITICAL severity: Create ticket, stop interaction, require escalation
    
    Args:
        state: Current agent state
        
    Returns:
        Command with routing decision
    """
    if not state["messages"]:
        return Command(goto="supervisor")
    
    last_message = state["messages"][-1]
    
    # Skip if not a human message
    if last_message.type != "ai" and not isinstance(last_message, HumanMessage):
        return Command(goto="supervisor")
    
    # Get message content
    text = last_message.content if hasattr(last_message, 'content') else str(last_message)
    
    # Check for abuse
    has_abuse, abuse_type, severity, violation_count = detect_abuse(text)
    
    if not has_abuse:
        # No abuse detected - proceed normally
        return Command(goto="supervisor")
    
    # Log the incident
    print(f"🚨 ABUSE DETECTED: Type={abuse_type}, Severity={severity}, Count={violation_count}")
    print(f"   Message: {text[:100]}...")
    
    # Create incident record
    incident = AbuseIncident(
        timestamp=datetime.now().isoformat(),
        user_id=state.get("user_id", "UNKNOWN"),
        thread_id=state.get("thread_id", "UNKNOWN"),
        abuse_type=abuse_type,
        severity=severity,
        message_preview=text[:200],
    )
    
    # Get abuse ticket if applicable
    ticket_id = None
    if severity in ["high", "critical"]:
        ticket_id = _create_abuse_ticket(
            state,
            abuse_type,
            severity,
            text,
            "abuse_detector"
        )
        incident.ticket_id = ticket_id
        incident.action_taken = "escalated"
        print(f"📋 Abuse report ticket created: {ticket_id}")
    
    # Log the incident
    monitor.log_incident(incident)
    
    # Check if user should be blocked
    if monitor.should_block_user(state.get("user_id", "UNKNOWN")):
        print(f"🚫 User {state.get('user_id')} blocked due to repeated abuse violations")
        return Command(
            goto="__end__",
            update={
                "messages": [AIMessage(content="Your account has been temporarily suspended due to repeated violations of our community guidelines. Please contact support.")],
                "safety_violation": True,
                "safety_message": "User blocked - repeated abuse violations",
                "abuse_violation": True,
                "abuse_type": abuse_type,
                "abuse_severity": severity,
            }
        )
    
    # Determine response based on severity
    if severity == "low":
        # Low severity: gentle warning
        warning_msg = config.LOW_SEVERITY_WARNING
        return Command(
            goto="supervisor",
            update={
                "messages": state["messages"][:-1] + [AIMessage(content=warning_msg)],
                "safety_violation": True,
                "safety_message": f"Low severity {abuse_type} detected",
                "abuse_violation": True,
                "abuse_type": abuse_type,
                "abuse_severity": severity,
                "abuse_count": monitor.get_session_violation_count(state.get("thread_id", "")),
            }
        )
    
    elif severity == "medium":
        # Medium severity: warning and note to support
        warning_msg = config.MEDIUM_SEVERITY_WARNING
        
        return Command(
            goto="supervisor",
            update={
                "messages": state["messages"][:-1] + [AIMessage(content=warning_msg)],
                "safety_violation": True,
                "safety_message": f"{abuse_type} detected - support notified",
                "abuse_violation": True,
                "abuse_type": abuse_type,
                "abuse_severity": severity,
                "abuse_count": monitor.get_session_violation_count(state.get("thread_id", "")),
            }
        )
    
    elif severity == "high":
        # High severity: warning and escalation offer
        escalation_msg = config.HIGH_SEVERITY_ESCALATION
        
        return Command(
            goto="__end__",
            update={
                "messages": [AIMessage(content=escalation_msg)],
                "safety_violation": True,
                "safety_message": f"High severity {abuse_type} - ticket {ticket_id} created",
                "abuse_violation": True,
                "abuse_type": abuse_type,
                "abuse_severity": severity,
                "needs_escalation": True,
                "escalation_status": "proposed",
                "is_direct_escalation": True,
            }
        )
    
    elif severity == "critical":
        # Critical severity: immediate escalation and termination
        critical_msg = config.CRITICAL_SEVERITY_TERMINATION
        
        return Command(
            goto="__end__",
            update={
                "messages": [AIMessage(content=critical_msg)],
                "safety_violation": True,
                "safety_message": f"CRITICAL: {abuse_type} - ticket {ticket_id} created - conversation terminated",
                "abuse_violation": True,
                "abuse_type": abuse_type,
                "abuse_severity": severity,
                "needs_escalation": True,
                "escalation_status": "proposed",
                "is_direct_escalation": True,
            }
        )
