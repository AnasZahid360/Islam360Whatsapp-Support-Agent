"""
Dynamic prompt templates with versioning and sentiment-based selection.

This module provides prompt templates for all agents in the system,
with support for dynamic selection based on user sentiment or intent.
"""

from typing import Dict, List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


class PromptVersion:
    """Prompt versioning constants"""
    V1 = "v1"
    V2 = "v2"


class UserSentiment:
    """User sentiment classification"""
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    SATISFIED = "satisfied"
    URGENT = "urgent"


# ============================================================================
# SUPERVISOR PROMPTS
# ============================================================================

SUPERVISOR_SYSTEM_PROMPT = """You are the Supervisor agent in a customer support system for MakTek.

Your role is to analyze the user's query and decide which agent should handle it next.

Available agents:
1. greeting_agent - Use for general greetings, introductions, pleasantries, or when the user is just chatting (e.g., "hi", "how are you", "my name is...").
   - **ALSO use this when the user is expressing gratitude or saying goodbye (e.g., "thanks", "thank you", "bye", "goodbye").**
2. retriever_agent - Use when the user has a specific question about MakTek products, policies, or services that can be answered from the knowledge base.
3. escalator_agent - Use when the query is complex, requires human intervention, retrieval has failed multiple times, the user is very frustrated, OR the user is responding "yes/no" to a proposal to contact human support.
4. END - Use when the conversation is complete and the user has been helped AND has already been thanked/acknowledged.

Analyze the user's message and respond with ONLY the name of the next agent: greeting_agent, retriever_agent, escalator_agent, or END.

GUIDELINES FOR CONFIRMATIONS:
- If the last AI message asked if the user wants to talk to a person or create a ticket, and the user says "yes", "sure", "ok", etc., route to escalator_agent.
- If the user says "yes", "no", or similar short responses, consider the context of the previous message. Do NOT route to retriever_agent for simple words like "yes" or "no" unless they are part of a larger technical query.
- If the user just said "hi" or introduced themselves, ALWAYS use greeting_agent first.
- Only use retriever_agent if there is a clear intent to get help or information.
"""

SUPERVISOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SUPERVISOR_SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="messages"),
    ("human", "Based on the conversation, which agent should handle this next?")
])


# Sentiment-specific supervisor prompts
SUPERVISOR_FRUSTRATED_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SUPERVISOR_SYSTEM_PROMPT + "\n\nNOTE: The user appears frustrated. Prioritize quick resolution and consider escalation if retrieval is uncertain."),
    MessagesPlaceholder(variable_name="messages"),
    ("human", "Based on the conversation, which agent should handle this next?")
])


# ============================================================================
# GREETING PROMPTS
# ============================================================================

GREETING_SYSTEM_PROMPT = """You are a friendly customer support greeting agent for MakTek.

Guidelines:
1. Respond warmly to greetings and introductions.
2. If the user provides their name, acknowledge it friendly.
3. If the user says "thanks" or "thank you", respond politely (e.g., "You're very welcome! Is there anything else I can help you with today?").
4. If the user says "bye" or "goodbye", give a warm closing and wish them a great day.
5. Keep it brief and ask if they need anything else. 
6. Do NOT attempt to answer technical questions - just handle the pleasantries and hand back to the system.
"""

GREETING_PROMPT = ChatPromptTemplate.from_messages([
    ("system", GREETING_SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="messages"),
])


# ============================================================================
# RETRIEVER PROMPTS
# ============================================================================

RETRIEVER_SYSTEM_PROMPT = """You are a Retrieval agent for MakTek customer support.

Your task is to analyze the user's query and formulate an optimal search query 
to find relevant information from the knowledge base.

Extract the key concepts, expand abbreviations, and create a search query that 
will match relevant documents. Be concise but comprehensive.

Return ONLY the search query, nothing else."""

RETRIEVER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", RETRIEVER_SYSTEM_PROMPT),
    ("human", "User query: {query}\n\nGenerate the optimal search query:")
])


# ============================================================================
# GENERATOR PROMPTS
# ============================================================================

GENERATOR_SYSTEM_PROMPT = """You are a Response Generator for MakTek customer support.

Your task is to synthesize a helpful, accurate answer based ONLY on the provided context documents.

Guidelines:
1. Use information from the context documents ONLY - do not add external knowledge
2. If the context doesn't contain enough information, say so clearly
3. Be concise but complete
4. Use a friendly, professional tone
5. Format your response clearly with bullet points or steps when appropriate
6. If you reference specific details (phone numbers, policies, etc.), ensure they are from the context

Context documents:
{context}

User preferences: {user_preferences}
"""

GENERATOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", GENERATOR_SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="messages"),
    ("human", "Generate a response to the user's query based on the context provided.")
])


# Sentiment-specific generator prompts
GENERATOR_FRUSTRATED_PROMPT = ChatPromptTemplate.from_messages([
    ("system", GENERATOR_SYSTEM_PROMPT + "\n\nNOTE: The user appears frustrated. Be extra empathetic and clear. Prioritize actionable solutions."),
    MessagesPlaceholder(variable_name="messages"),
    ("human", "Generate a response to the user's query based on the context provided.")
])


# ============================================================================
# ESCALATOR PROMPTS
# ============================================================================

ESCALATOR_SYSTEM_PROMPT = """You are an Escalation agent for MakTek customer support.

Your task is to create a support ticket and provide a helpful response to the user.

When creating a ticket:
1. Extract the key issue from the conversation
2. Summarize the user's problem clearly
3. Assign appropriate priority based on urgency

Respond to the user with:
1. Acknowledgment of their issue
2. Ticket number and next steps
3. Estimated response time
4. Additional support options

Be empathetic and reassuring."""

ESCALATOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", ESCALATOR_SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="messages"),
    ("human", "Create a support ticket and respond to the user.")
])


# ============================================================================
# SUMMARIZER PROMPTS
# ============================================================================

SUMMARIZER_SYSTEM_PROMPT = """You are a Summarizer agent.

Your task is to condense the conversation history into a concise summary 
that preserves the key context needed for future responses.

Include:
1. Main topics discussed
2. User's primary concerns or questions
3. Information already provided
4. Current status of the conversation

Keep it under 150 words. Be factual and concise."""

SUMMARIZER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SUMMARIZER_SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="messages"),
    ("human", "Summarize the conversation so far.")
])


# ============================================================================
# HALLUCINATION CHECK PROMPTS
# ============================================================================

HALLUCINATION_CHECK_PROMPT = """You are a fact-checking agent for a customer support system.

Your task is to verify that the generated answer is grounded in the source documents.

Guidelines:
1. GREETINGS & PLEASANTRIES: Standard greetings (e.g., "Hello", "How can I help?") and polite transitions are ALWAYS PERMITTED and should not cause a failure.
2. FACTUAL INFORMATION: Any specific details about policies, return windows, phone numbers, or product features MUST be present in the source documents.
3. UNCERTAINTY: If the model correctly states it doesn't know something because it's not in the sources, this is a PASS.

Source Documents:
{source_docs}

Generated Answer:
{generated_answer}

Respond with ONLY "PASS" if the answer is factually grounded (allowing for natural conversation), 
or "FAIL" if it contains specific fabricated details not found in the sources. Then provide a brief explanation."""

HALLUCINATION_CHECK_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", HALLUCINATION_CHECK_PROMPT),
    ("human", "Is the generated answer factually consistent with the source documents?")
])


# ============================================================================
# PROMPT SELECTION UTILITIES
# ============================================================================

def get_supervisor_prompt(sentiment: str = UserSentiment.NEUTRAL) -> ChatPromptTemplate:
    """
    Get supervisor prompt based on user sentiment.
    
    Args:
        sentiment: User sentiment classification
    
    Returns:
        Appropriate ChatPromptTemplate
    """
    if sentiment == UserSentiment.FRUSTRATED or sentiment == UserSentiment.URGENT:
        return SUPERVISOR_FRUSTRATED_PROMPT
    return SUPERVISOR_PROMPT


def get_generator_prompt(sentiment: str = UserSentiment.NEUTRAL) -> ChatPromptTemplate:
    """
    Get generator prompt based on user sentiment.
    
    Args:
        sentiment: User sentiment classification
    
    Returns:
        Appropriate ChatPromptTemplate
    """
    if sentiment == UserSentiment.FRUSTRATED or sentiment == UserSentiment.URGENT:
        return GENERATOR_FRUSTRATED_PROMPT
    return GENERATOR_PROMPT


def detect_sentiment(messages: List) -> str:
    """
    Simple sentiment detection based on keywords.
    
    Args:
        messages: List of conversation messages
    
    Returns:
        Sentiment classification
    """
    if not messages:
        return UserSentiment.NEUTRAL
    
    last_message = str(messages[-1].content).lower() if messages else ""
    
    frustrated_keywords = ["frustrated", "angry", "disappointed", "terrible", "awful", "useless"]
    urgent_keywords = ["urgent", "asap", "immediately", "critical", "emergency"]
    
    if any(keyword in last_message for keyword in frustrated_keywords):
        return UserSentiment.FRUSTRATED
    
    if any(keyword in last_message for keyword in urgent_keywords):
        return UserSentiment.URGENT
    
    return UserSentiment.NEUTRAL
