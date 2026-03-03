"""
Retriever agent - RAG implementation with relevance checking.

This agent queries the vector store, scores results, and determines
if the retrieval quality is sufficient or if escalation is needed.
"""

from typing import Literal
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command
from src.state import AgentState
from src.models import get_model
from src.rag.retriever import Retriever
from src.utils.prompts import RETRIEVER_PROMPT


def retriever_agent_node(state: AgentState) -> Command[Literal["generator_agent", "escalator_agent"]]:
    """
    Retriever agent that performs RAG and relevance checking.
    
    This agent:
    1. Extracts the user's query
    2. Optionally reformulates it using an LLM
    3. Searches the vector store
    4. Scores the results
    5. Routes to generator if quality is good, else escalates
    
    Args:
        state: Current agent state
    
    Returns:
        Command with updated state and routing decision
    """
    # Get the latest user message
    if not state["messages"]:
        return Command(
            goto="escalator_agent",
            update={"needs_escalation": True}
        )
    
    last_message = state["messages"][-1]
    user_query = last_message.content if hasattr(last_message, 'content') else str(last_message)
    
    # Optionally use LLM to reformulate query for better retrieval
    reformulated_query = _reformulate_query(user_query, state)
    
    # Initialize retriever with config from state
    relevance_threshold = state["config"].get("relevance_threshold", 0.7)
    max_docs = state["config"].get("max_retrieved_docs", 5)
    escalation_threshold = state["config"].get("escalation_threshold", 0.4)
    
    retriever = Retriever(
        relevance_threshold=relevance_threshold,
        max_docs=max_docs,
        escalation_threshold=escalation_threshold
    )
    
    # Perform retrieval
    result = retriever.retrieve(reformulated_query)
    
    # Update state with retrieval results
    update_dict = {
        "retrieved_docs": result.to_dict(),
        "relevance_score": result.relevance_score,
        "needs_escalation": result.should_escalate
    }
    
    # Check if we should escalate based on relevance
    if result.should_escalate:
        print(f"⚠ Low relevance score: {result.relevance_score:.2f} - Escalating to human support")
        return Command(
            goto="escalator_agent",
            update=update_dict
        )
    
    print(f"✓ Retrieved {len(result.documents)} documents (avg score: {result.relevance_score:.2f})")
    
    # Route to generator with retrieved documents
    return Command(
        goto="generator_agent",
        update=update_dict
    )


def _reformulate_query(query: str, state: AgentState) -> str:
    """
    Use LLM to reformulate the user's query for better retrieval.
    
    Args:
        query: Original user query
        state: Current agent state
    
    Returns:
        Reformulated search query
    """
    try:
        model = get_model(state["config"])
        
        messages = RETRIEVER_PROMPT.format_messages(query=query)
        response = model.invoke(messages)
        
        reformulated = response.content.strip()
        print(f"🔍 Query: '{query}' → '{reformulated}'")
        
        return reformulated
    except Exception as e:
        print(f"⚠ Query reformulation failed: {e}. Using original query.")
        return query
