"""
Greeting agent - Handles pleasantries, introductions, and general conversation.

This agent ensures the bot responds naturally to greetings and non-support 
queries without triggering unnecessary retrieval or escalation.
"""

from typing import Literal
from langchain_core.messages import SystemMessage
from langgraph.types import Command
from src.state import AgentState
from src.models import get_model
from src.utils.prompts import GREETING_PROMPT


def greeting_agent_node(state: AgentState) -> Command[Literal["supervisor", "__end__"]]:
    """
    Greeting agent node that responds to pleasantries.
    
    Args:
        state: Current agent state
        
    Returns:
        Command to route back to supervisor or end
    """
    # Get the model
    model = get_model(state["config"])
    
    # Prepare messages for the LLM
    # We include the last few messages for context
    messages = GREETING_PROMPT.format_messages(
        messages=state["messages"][-3:] if len(state["messages"]) > 3 else state["messages"]
    )
    
    # Generate response
    response = model.invoke(messages)
    
    # Return command with update and routing
    return Command(
        update={"messages": [response]},
        goto="supervisor" # Go back to supervisor to see if there's more to do or just end
    )
