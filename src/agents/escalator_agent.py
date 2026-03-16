"""
Escalator agent - Creates support tickets for unresolved issues.

This agent is invoked when the RAG system cannot provide a satisfactory
answer, creating a support ticket and providing a helpful fallback response.
"""

from typing import Literal
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command
from src.state import AgentState
from src.models import get_model
from src.tools.support_ticket import create_support_ticket
from src.utils.prompts import ESCALATOR_PROMPT


async def escalator_agent_node(state: AgentState) -> Command[Literal["__end__"]]:
    """
    Escalator agent that proposes or creates support tickets.
    """
    model = get_model(state["config"])
    current_status = state.get("escalation_status", "none")
    
    # Phase 1: Propose escalation
    if current_status in ["none", "declined"]:
        if state.get("is_direct_escalation", False):
            response_content = (
                "I'd be happy to help you connect with a human representative. "
                "Should I create a support ticket for you so our team can follow up directly?"
            )
        else:
            response_content = (
                "I'm sorry, I'm having trouble finding a definitive answer for you. "
                "Would you like me to create a support ticket so a human representative can look into this for you?"
            )
            
        return Command(
            goto="__end__",
            update={
                "messages": [AIMessage(content=response_content)],
                "escalation_status": "proposed",
                "is_direct_escalation": False # Reset flag as it's been consumed
            }
        )
        
    # Phase 2: Handle response to proposal
    if current_status == "proposed":
        last_message = state["messages"][-1].content.lower()
        
        # Simple intent detection (could be improved with LLM)
        import re
        yes_words = [r"yes", r"yep", r"sure", r"please", r"ok", r"do it"]
        no_words = [r"no", r"nope", r"don't", r"stop", r"wait"]
        
        is_yes = any(re.search(rf"\b{word}\b", last_message) for word in yes_words)
        is_no = any(re.search(rf"\b{word}\b", last_message) for word in no_words)
        
        # Use LLM for more robust intent detection if unclear
        if not is_yes and not is_no:
            intent_prompt = f"User message: '{last_message}'\nDid the user agree to creating a support ticket? Respond with ONLY 'YES' or 'NO'."
            intent_resp = model.invoke([HumanMessage(content=intent_prompt)])
            is_yes = "YES" in intent_resp.content.upper()
        
        if is_yes:
            # Extract the issue from conversation
            issue_summary = _extract_issue(state)
            priority = _determine_priority(state)
            
            # Create support ticket
            ticket = create_support_ticket.invoke({
                "issue": issue_summary,
                "user_id": state["user_id"],
                "priority": priority
            })
            
            ticket_context = f"""
Ticket created:
- Ticket ID: {ticket['ticket_id']}
- Priority: {ticket['priority']}
- Estimated response time: {ticket['estimated_response_time']}
- Status: {ticket['status']}

Generate an empathetic response acknowledging the ticket creation and providing the details.
"""
            messages = ESCALATOR_PROMPT.format_messages(messages=state["messages"])
            messages[0].content += "\n\n" + ticket_context
            
            response = model.invoke(messages)
            
            print(f"✓ Created ticket {ticket['ticket_id']} for user {state['user_id']}")
            
            return Command(
                goto="__end__",
                update={
                    "messages": [AIMessage(content=response.content)],
                    "escalation_status": "confirmed"
                }
            )
        else:
            # Check if the user's message was just a simple "no" or a new question
            # If the user typed a longer message, they likely asked something new.
            just_no = re.match(r'^(no|nope|don\'t|stop|wait)[^\w]*$', last_message.strip())
            
            if just_no:
                return Command(
                    goto="__end__",
                    update={
                        "messages": [AIMessage(content="Understood. Let me know if you need anything else.")],
                        "escalation_status": "declined"
                    }
                )
            else:
                # User declined the ticket but asked a new question. Route back to supervisor to handle the new query.
                return Command(
                    goto="supervisor",
                    update={
                        "escalation_status": "declined"
                    }
                )
    
    # Fallback
    return Command(goto="__end__")


def _extract_issue(state: AgentState) -> str:
    """
    Extract a summary of the user's issue from the conversation.
    
    Args:
        state: Current agent state
    
    Returns:
        Issue summary string
    """
    # Get all user messages
    user_messages = [
        str(msg.content) for msg in state["messages"]
        if msg.type == "human"
    ]
    
    if not user_messages:
        return "User requires support assistance"
    
    # Combine user messages into issue summary
    if len(user_messages) == 1:
        return user_messages[0]
    else:
        return f"Multiple inquiries: {' | '.join(user_messages[-3:])}"  # Last 3 messages


def _determine_priority(state: AgentState) -> str:
    """
    Determine ticket priority based on context and sentiment.
    
    Args:
        state: Current agent state
    
    Returns:
        Priority level: low, medium, high, or urgent
    """
    # Check for urgent keywords in recent messages
    if state["messages"]:
        last_message = str(state["messages"][-1].content).lower()
        
        if any(word in last_message for word in ["urgent", "emergency", "critical", "asap"]):
            return "urgent"
        
        if any(word in last_message for word in ["frustrated", "angry", "disappointed"]):
            return "high"
    
    # Check relevance score - very low score indicates potential urgent issue
    if state.get("relevance_score", 1.0) < 0.2:
        return "high"
    
    # Default to medium priority
    return "medium"
