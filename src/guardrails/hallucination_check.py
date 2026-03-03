"""
Hallucination check guardrail.

This module implements a self-correction loop that verifies generated
responses against source documents, preventing hallucinations.
"""

from typing import Literal
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from src.state import AgentState, increment_hallucination_retry, max_hallucination_retries_reached
from src.models import get_fast_model
from src.utils.prompts import HALLUCINATION_CHECK_TEMPLATE


async def hallucination_check_node(
    state: AgentState
) -> Command[Literal["generator_agent", "supervisor", "__end__"]]:
    """
    Hallucination check guardrail node.
    
    This node:
    1. Extracts the generated answer
    2. Compares it against retrieved source documents
    3. Uses an LLM to verify factual consistency
    4. Routes back to generator if hallucination detected
    5. Routes to supervisor if check passes
    
    Args:
        state: Current agent state
    
    Returns:
        Command with routing decision
    """
    # Check if hallucination checking is enabled
    if not state["config"].get("enable_hallucination_check", True):
        print("⏭️  Hallucination check disabled - proceeding to supervisor")
        return Command(goto="supervisor")
    
    # Get the generated answer (last AI message)
    if not state["messages"]:
        return Command(goto="supervisor")
    
    last_message = state["messages"][-1]
    if last_message.type != "ai":
        return Command(goto="supervisor")
    
    generated_answer = last_message.content
    
    # Get source documents
    retrieved_docs = state.get("retrieved_docs", [])
    
    if not retrieved_docs:
        # No source docs - can't check for hallucination
        print("⏭️  No source docs to check against - proceeding")
        return Command(goto="supervisor")
    
    # Format source documents
    source_docs_str = _format_source_docs(retrieved_docs)
    
    # Use fast model for efficiency
    model = get_fast_model()
    
    # Check for hallucination
    check_result = await _check_hallucination(
        model,
        source_docs_str,
        generated_answer
    )
    
    passed, explanation = check_result
    
    if passed:
        print(f"✓ Hallucination check PASSED: {explanation}")
        return Command(goto="supervisor")
    else:
        # Check if we've exceeded retry limit
        if max_hallucination_retries_reached(state):
            print(f"⚠ Max hallucination retries reached - escalating")
            return Command(
                goto="__end__",
                update={
                    "needs_escalation": True,
                    "messages": state["messages"][:-1]  # Remove hallucinated response
                }
            )
        
        print(f"⚠ Hallucination check FAILED: {explanation}")
        print("🔄 Retrying generation...")
        
        # Increment retry counter and route back to generator
        state = increment_hallucination_retry(state)
        
        # Remove the hallucinated response and add guidance
        messages_without_hallucination = state["messages"][:-1]
        guidance_message = HumanMessage(
            content=f"Please regenerate your response. "
                   f"IMPORTANT: Only use information from the provided context. "
                   f"Previous issue: {explanation}"
        )
        
        return Command(
            goto="generator_agent",
            update={
                "messages": messages_without_hallucination + [guidance_message],
                "hallucination_retry_count": state["hallucination_retry_count"]
            }
        )


async def _check_hallucination(
    model,
    source_docs: str,
    generated_answer: str
) -> tuple[bool, str]:
    """
    Use LLM to check if the generated answer contains hallucinations.
    
    Args:
        model: Language model to use for checking
        source_docs: Formatted source documents
        generated_answer: The generated response to check
    
    Returns:
        Tuple of (passed: bool, explanation: str)
    """
    messages = HALLUCINATION_CHECK_TEMPLATE.format_messages(
        source_docs=source_docs,
        generated_answer=generated_answer
    )
    
    response = model.invoke(messages)
    result = response.content.strip()
    
    # Parse result
    if result.upper().startswith("PASS"):
        return True, result
    elif result.upper().startswith("FAIL"):
        return False, result
    else:
        # Unclear result - be conservative and pass
        return True, "Unclear result - proceeding"


def _format_source_docs(retrieved_docs: list) -> str:
    """
    Format retrieved documents for hallucination checking.
    
    Args:
        retrieved_docs: List of retrieved document dictionaries
    
    Returns:
        Formatted source documents string
    """
    if not retrieved_docs:
        return "No source documents available."
    
    parts = []
    for idx, doc in enumerate(retrieved_docs, 1):
        question = doc.get("question", "")
        answer = doc.get("answer", "")
        
        parts.append(f"[Source {idx}]\nQ: {question}\nA: {answer}")
    
    return "\n\n".join(parts)
