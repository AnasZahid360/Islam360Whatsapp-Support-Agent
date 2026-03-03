"""
Summarizer agent - Condenses conversation history to save tokens.

This agent triggers when the message count exceeds a threshold,
creating a concise summary and pruning the message list.
"""

from langchain_core.messages import SystemMessage
from src.state import AgentState, should_summarize
from src.models import get_model
from src.utils.prompts import SUMMARIZER_PROMPT


async def summarizer_node(state: AgentState) -> dict:
    """
    Summarizer middleware that condenses conversation history.
    
    This node checks if summarization is needed and, if so:
    1. Creates a concise summary of the conversation
    2. Prunes old messages
    3. Keeps only recent messages + summary
    
    Args:
        state: Current agent state
    
    Returns:
        Dictionary with updated summary and pruned messages
    """
    # Check if summarization is needed
    if not should_summarize(state):
        return {}  # No update needed
    
    print("📝 Message threshold exceeded - creating summary...")
    
    # Get model
    model = get_model(state["config"])
    
    # Generate summary
    messages = SUMMARIZER_PROMPT.format_messages(messages=state["messages"])
    response = model.invoke(messages)
    new_summary = response.content.strip()
    
    # Combine with existing summary if present
    if state.get("summary"):
        combined_summary = f"{state['summary']}\n\nRecent update: {new_summary}"
    else:
        combined_summary = new_summary
    
    # Keep only the last N messages (e.g., last 5)
    keep_last_n = 5
    pruned_messages = state["messages"][-keep_last_n:]
    
    print(f"✓ Summary created. Messages pruned from {len(state['messages'])} to {len(pruned_messages)}")
    
    return {
        "summary": combined_summary,
        "messages": pruned_messages
    }


def check_and_summarize(state: AgentState) -> AgentState:
    """
    Synchronous wrapper to check and apply summarization.
    
    This can be used as a graph node or middleware.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with summary if needed
    """
    import asyncio
    
    # Run async summarizer
    update = asyncio.run(summarizer_node(state))
    
    if update:
        state.update(update)
    
    return state
