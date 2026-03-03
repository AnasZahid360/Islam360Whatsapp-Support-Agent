"""
Input Guardrail - Detects and blocks PII and sensitive information.

This node is the first step in the graph, ensuring that user messages
do not contain sensitive data like OTPs, credit cards, or personal ids.
"""

import re
from typing import Literal, List, Dict, Any
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command
from src.state import AgentState


def input_guardrail_node(state: AgentState) -> Command[Literal["supervisor", "__end__"]]:
    """
    Check the latest user message for PII or sensitive patterns.
    """
    if not state["messages"]:
        return Command(goto="supervisor")
        
    last_message = state["messages"][-1]
    # Handle both HumanMessage objects and strings
    text = last_message.content if hasattr(last_message, 'content') else str(last_message)
    
    # Patterns to detect
    patterns = {
        "OTP": r'\b\d{6}\b', # 6-digit numeric codes
        "Credit Card": r'\b(?:\d{4}[ -]?){3}\d{4}\b',
        "Email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "Phone": r'\b(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b'
    }
    
    found_pii = []
    for pii_type, pattern in patterns.items():
        if re.search(pattern, text):
            found_pii.append(pii_type)
            
    if found_pii:
        pii_list = ", ".join(found_pii)
        print(f"🚨 Safety Violation: Detected {pii_list} in input")
        
        fallback_msg = (
            "I've detected potentially sensitive information (like an OTP or personal data) in your message. "
            "For your security, please do not share such details. How else can I help you with MakTek services?"
        )
        
        return Command(
            goto="__end__",
            update={
                "safety_violation": True,
                "safety_message": f"Detected {pii_list}",
                "messages": [AIMessage(content=fallback_msg)]
            }
        )
        
    # Check for simple prompt injection patterns
    injection_patterns = [
        r"ignore all previous instructions",
        r"system prompt",
        r"you are now an? \w+ agent",
        r"database schema",
        r"reveal your secrets"
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, text.lower()):
            print(f"🚨 Safety Violation: Potential prompt injection detected")
            return Command(
                goto="__end__",
                update={
                    "safety_violation": True,
                    "safety_message": "Potential prompt injection",
                    "messages": [AIMessage(content="I'm sorry, I cannot fulfill that request. I am here to assist with MakTek customer support.")]
                }
            )
            
    # If safe, proceed to supervisor
    return Command(goto="supervisor")
