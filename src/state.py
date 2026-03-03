"""
State definitions for the Multi-Agent RAG System.

This module defines the AgentState TypedDict that flows through the LangGraph,
containing conversation history, retrieved documents, memory, and configuration.
"""

from typing import TypedDict, Annotated, Dict, List, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    The state object that flows through all nodes in the graph.
    
    Attributes:
        messages: Conversation history with automatic message merging
        summary: Condensed conversation context for token efficiency
        retrieved_docs: Temporary storage for RAG results from vector store
        config: Dynamic configuration (model selection, prompt version, etc.)
        user_id: Unique identifier for the user (for long-term memory)
        thread_id: Unique identifier for the conversation thread
        relevance_score: Quality score from the retriever (0.0 to 1.0)
        needs_escalation: Flag indicating if the query should be escalated
        hallucination_retry_count: Tracks retries for hallucination correction
        next_agent: The next agent to route to (for Command pattern)
    """
    messages: Annotated[List[BaseMessage], add_messages]
    summary: str
    retrieved_docs: List[Dict[str, Any]]
    config: Dict[str, Any]
    user_id: str
    thread_id: str
    relevance_score: float
    needs_escalation: bool
    escalation_status: str  # "none", "proposed", "confirmed", "declined"
    is_direct_escalation: bool
    safety_violation: bool
    safety_message: str
    hallucination_retry_count: int
    next_agent: str


def create_initial_state(
    user_id: str,
    thread_id: str,
    config: Dict[str, Any] = None
) -> AgentState:
    """
    Create an initial state object with default values.
    
    Args:
        user_id: Unique user identifier
        thread_id: Unique conversation thread identifier
        config: Optional configuration overrides
    
    Returns:
        AgentState with default values
    """
    default_config = {
        "model_provider": "groq",
        "model_name": "llama-3.3-70b-versatile",
        "temperature": 0.7,
        "max_tokens": 1000,
        "relevance_threshold": 0.7,
        "escalation_threshold": 0.4,
        "max_retrieved_docs": 5,
        "enable_hallucination_check": True,
        "max_hallucination_retries": 2,
        "max_messages_before_summary": 10,
    }
    
    if config:
        default_config.update(config)
    
    return AgentState(
        messages=[],
        summary="",
        retrieved_docs=[],
        config=default_config,
        user_id=user_id,
        thread_id=thread_id,
        relevance_score=1.0,
        needs_escalation=False,
        escalation_status="none",
        is_direct_escalation=False,
        safety_violation=False,
        safety_message="",
        hallucination_retry_count=0,
        next_agent="supervisor"
    )


def should_summarize(state: AgentState) -> bool:
    """
    Check if the conversation should be summarized.
    
    Args:
        state: Current agent state
    
    Returns:
        True if message count exceeds the threshold
    """
    max_messages = state["config"].get("max_messages_before_summary", 10)
    return len(state["messages"]) > max_messages


def get_relevance_threshold(state: AgentState) -> float:
    """
    Get the relevance threshold from state configuration.
    
    Args:
        state: Current agent state
    
    Returns:
        Relevance threshold value
    """
    return state["config"].get("relevance_threshold", 0.7)


def increment_hallucination_retry(state: AgentState) -> AgentState:
    """
    Increment the hallucination retry counter.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with incremented counter
    """
    state["hallucination_retry_count"] += 1
    return state


def max_hallucination_retries_reached(state: AgentState) -> bool:
    """
    Check if maximum hallucination retries have been reached.
    
    Args:
        state: Current agent state
    
    Returns:
        True if max retries reached
    """
    max_retries = state["config"].get("max_hallucination_retries", 2)
    return state["hallucination_retry_count"] >= max_retries
