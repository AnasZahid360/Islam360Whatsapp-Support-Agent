"""
Supervisor agent - The orchestrator of the multi-agent system.

The Supervisor analyzes user queries and routes to the appropriate agent
using the Command pattern. It considers sentiment, conversation history,
and retrieval success to make routing decisions.
"""

from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import Command
from src.state import AgentState
from src.models import get_model
from src.utils.prompts import get_supervisor_prompt, detect_sentiment


def supervisor_node(state: AgentState) -> Command[Literal["retriever_agent", "escalator_agent", "greeting_agent", "__end__"]]:
    """
    Supervisor node that routes to the appropriate agent.
    
    This is the brain of the system. It analyzes the conversation
    and decides whether to:
    - Route to retriever_agent for knowledge base lookup
    - Route to escalator_agent for human support
    - End the conversation
    
    Args:
        state: Current agent state
    
    Returns:
        Command object with routing decision
    """
    # Detect user sentiment from messages
    sentiment = detect_sentiment(state["messages"])
    
    # Get the appropriate prompt based on sentiment
    prompt = get_supervisor_prompt(sentiment)
    
    # Get the model
    model = get_model(state["config"])
    
    # Prepare prompt variables
    summary = state.get("summary", "No previous context")
    
    # 0. Check if turn is complete
    # If the last message is from the AI, the conversation turn is complete.
    # We should return to the user.
    if state["messages"] and state["messages"][-1].type == "ai":
        # BUT: Only end if there's no pending escalation or if we're not in a loop
        # Check if the last AI message was an escalation proposal
        last_ai_msg = state["messages"][-1].content.lower()
        is_escalation_proposal = "support ticket" in last_ai_msg or "human representative" in last_ai_msg
        
        # If it's an escalation proposal, wait for user response before ending
        if is_escalation_proposal and state.get("escalation_status") == "proposed":
            return Command(goto="escalator_agent")
        
        return Command(goto="__end__")
        
    # 1. Handle explicit escalation flags
    # If an escalation is already proposed, we MUST go to escalator_agent to handle user response
    if state.get("escalation_status") == "proposed":
        return Command(goto="escalator_agent")
        
    # If the retriever or guardrail flagged for escalation, and it hasn't been declined yet
    if state.get("needs_escalation", False) and state.get("escalation_status") != "declined":
        # Reset the flag so we don't loop, but the escalator node will handle the 'proposed' status
        return Command(
            goto="escalator_agent",
            update={"needs_escalation": False}
        )
        
    # 2. Detect direct request for human/support or confirmation
    if state["messages"]:
        last_msg = str(state["messages"][-1].content).lower().strip()
        human_keywords = ["human", "representative", "person", "support team", "customer service"]
        
        # Check for direct request
        if any(keyword in last_msg for keyword in human_keywords):
            return Command(
                goto="escalator_agent",
                update={"is_direct_escalation": True}
            )
            
        # Check for simple confirmation "yes/no" if the previous message was from AI
        if len(state["messages"]) >= 2:
            prev_msg = state["messages"][-2]
            if prev_msg.type == "ai":
                import re
                # Multi-word confirmation handling with word boundaries
                yes_words = [r"yes", r"yep", r"sure", r"ok", r"okay", r"y", r"yeah", r"please", r"do it"]
                no_words = [r"no", r"nope", r"n", r"don't", r"stop", r"wait"]
                
                is_yes = any(re.search(rf"\b{word}\b", last_msg) for word in yes_words)
                is_no = any(re.search(rf"\b{word}\b", last_msg) for word in no_words)
                
                # Only treat as yes/no response if message is SHORT (1-3 words)
                # If it's a longer message, treat it as a new question
                word_count = len(last_msg.split())
                is_short_response = word_count <= 3
                
                if (is_yes or is_no) and is_short_response:
                    # If AI proposed something (like a ticket or support help), go to escalator_agent
                    # We check for broader keywords to catch RAG-based support offers too.
                    prev_content = prev_msg.content.lower()
                    support_offer_keywords = [
                        "ticket", "representative", "support", "help you with", 
                        "billing", "refund", "confirm", "okay with you", "is that okay"
                    ]
                    
                    if any(word in prev_content for word in support_offer_keywords):
                        # Don't loop if we just handled this state
                        if state.get("escalation_status") not in ["declined", "confirmed", "proposed"]:
                            return Command(
                                goto="escalator_agent",
                                update={"escalation_status": "proposed"} 
                            )
    
    # If relevance score is very low from previous retrieval, escalate
    # Only check if retrieved_docs is populated (meaning a search was actually done)
    if state.get("retrieved_docs") and state.get("relevance_score", 1.0) < 0.3:
        if state.get("escalation_status") != "declined":
            return Command(goto="escalator_agent")
    
    # Build messages for the LLM using format_messages for robustness
    messages = prompt.format_messages(
        summary=summary,
        sentiment=sentiment,
        messages=state["messages"]
    )
    
    # Ask LLM for routing decision
    response = model.invoke(messages)
    decision = response.content.strip().lower()
    
    # Parse the decision
    decision_text = decision.lower()
    
    # Check for thanks/bye explicitly in case LLM missed it
    thanks_keywords = ["thanks", "thank you", "bye", "goodbye", "thx"]
    if any(word in last_msg for word in thanks_keywords):
        return Command(goto="greeting_agent")
        
    if "greeting" in decision_text:
        return Command(goto="greeting_agent")
    elif "retriever" in decision_text or "retrieve" in decision_text:
        return Command(goto="retriever_agent")
    elif "escalat" in decision_text:
        return Command(goto="escalator_agent")
    elif "end" in decision_text:
        return Command(goto="__end__")
    else:
        # Default to retriever if unclear
        return Command(goto="retriever_agent")
