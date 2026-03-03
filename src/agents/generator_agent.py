"""
Generator agent - Synthesizes responses from retrieved documents.

This agent takes the retrieved documents and generates a natural,
helpful response while ensuring it stays grounded in the source material.
"""

from typing import Literal
from langchain_core.messages import AIMessage
from langgraph.types import Command
from src.state import AgentState
from src.models import get_model
from src.utils.prompts import get_generator_prompt, detect_sentiment
from src.memory.memory_manager import get_memory_manager


async def generator_agent_node(state: AgentState) -> Command[Literal["hallucination_check"]]:
    """
    Generator agent that creates responses from retrieved context.
    
    This agent:
    1. Formats retrieved documents as context
    2. Retrieves user preferences from long-term memory
    3. Generates a response using the LLM
    4. Routes to hallucination check
    
    Args:
        state: Current agent state
    
    Returns:
        Command with generated response and routing to hallucination check
    """
    # Get retrieved documents
    retrieved_docs = state.get("retrieved_docs", [])
    
    if not retrieved_docs:
        # No documents to work with - should have been escalated
        return Command(
            goto="hallucination_check",
            update={
                "messages": [AIMessage(content="I apologize, but I don't have enough information to answer your question accurately.")]
            }
        )
    
    # Format context from retrieved documents
    context = _format_context(retrieved_docs)
    
    # Get user preferences from long-term memory
    memory_manager = get_memory_manager()
    user_preferences = await memory_manager.get_all_user_preferences(state["user_id"])
    
    # Format preferences for the prompt
    prefs_str = _format_preferences(user_preferences)
    
    # Detect sentiment for prompt selection
    sentiment = detect_sentiment(state["messages"])
    prompt = get_generator_prompt(sentiment)
    
    # Get model
    model = get_model(state["config"])
    
    # Build messages
    system_message = prompt.messages[0].prompt.template.format(
        context=context,
        user_preferences=prefs_str
    )
    
    messages = [
        {"role": "system", "content": system_message}
    ] + [
        {"role": "user" if msg.type == "human" else "assistant", "content": msg.content}
        for msg in state["messages"]
    ]
    
    # Generate response
    response = model.invoke(messages)
    generated_content = response.content
    
    print(f"✓ Generated response ({len(generated_content)} chars)")
    
    # Add response to messages
    return Command(
        goto="hallucination_check",
        update={
            "messages": [AIMessage(content=generated_content)]
        }
    )


def _format_context(retrieved_docs: list) -> str:
    """
    Format retrieved documents as context for the generator.
    
    Args:
        retrieved_docs: List of retrieved document dictionaries
    
    Returns:
        Formatted context string
    """
    if not retrieved_docs:
        return "No relevant information available."
    
    context_parts = []
    for idx, doc in enumerate(retrieved_docs, 1):
        question = doc.get("question", "")
        answer = doc.get("answer", "")
        score = doc.get("score", 0.0)
        
        context_parts.append(
            f"[Source {idx}] (Relevance: {score:.2f})\n"
            f"Q: {question}\n"
            f"A: {answer}\n"
        )
    
    return "\n".join(context_parts)


def _format_preferences(preferences: dict) -> str:
    """
    Format user preferences for inclusion in prompt.
    
    Args:
        preferences: User preferences dictionary
    
    Returns:
        Formatted preferences string
    """
    if not preferences:
        return "No specific user preferences recorded."
    
    pref_parts = []
    
    # Extract common preferences
    if "response_style" in preferences:
        pref_parts.append(f"Preferred style: {preferences['response_style']}")
    
    if "interaction_count" in preferences:
        count = preferences["interaction_count"]
        if count > 10:
            pref_parts.append("Returning user - can use more technical language")
        else:
            pref_parts.append("New user - use clear, simple explanations")
    
    return " | ".join(pref_parts) if pref_parts else "Standard interaction"
