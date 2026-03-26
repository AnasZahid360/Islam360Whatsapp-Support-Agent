"""LiveKit Agent worker for real-time voice conversations.

Compatible with `livekit-agents` 1.5.x API.
Ticket creation is handled by calling the backend REST API so tickets
appear in the Active Tickets sidebar immediately.
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Annotated
import httpx
from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, function_tool
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, silero

logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


@function_tool
async def create_support_ticket(
    issue: Annotated[str, "Clear description of the user's problem"],
    priority: Annotated[str, "Ticket priority: low, medium, high, or urgent"] = "medium",
) -> str:
    """
    Create a support ticket for the user's issue so a human agent can follow up.
    Call this when the user asks to create a ticket or when you cannot resolve their issue.
    Always confirm the ticket ID back to the user after creation.
    """
    # user_id and thread_id are injected via closure in entrypoint
    return await _do_create_ticket(issue, priority)


# Will be set per-session in entrypoint
_session_user_id: str = "voice_user"
_session_thread_id: str = "voice_thread"


async def _do_create_ticket(issue: str, priority: str) -> str:
    global _session_user_id, _session_thread_id
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{BACKEND_URL}/create-ticket",
                json={
                    "user_id": _session_user_id,
                    "thread_id": _session_thread_id,
                    "issue": issue,
                    "priority": priority,
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                ticket_id = data.get("ticket_id", "unknown")
                logger.info(f"✓ Voice ticket created: {ticket_id} for {_session_user_id}")
                return (
                    f"Support ticket created successfully. "
                    f"Your ticket ID is {ticket_id}. "
                    f"Priority is {priority}. "
                    f"Our team will follow up within "
                    f"{'1-2 hours' if priority == 'urgent' else '4-8 hours' if priority == 'high' else '1-2 business days'}."
                )
            else:
                logger.error(f"Ticket creation failed: {resp.status_code} {resp.text}")
                return "I'm sorry, I wasn't able to create the ticket right now. Please try again or use the text chat."
    except Exception as e:
        logger.error(f"Ticket creation error: {e}")
        return "I'm sorry, there was a connection error creating your ticket. Please try using the text chat instead."


class MakTekAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions=(
                "You are MakTek Support Assistant — a helpful, concise voice agent. "
                "Help users with their support issues. "
                "When a user asks you to create a support ticket, or when you cannot resolve their issue, "
                "ALWAYS use the create_support_ticket function tool — do not just say you will create one. "
                "Ask for the issue details if not already clear, then call the tool immediately. "
                "After calling the tool, read out the ticket ID to the user."
            ),
            tools=[create_support_ticket],
        )


async def entrypoint(ctx: JobContext):
    global _session_user_id, _session_thread_id

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant joined: {participant.identity}")

    # Use participant identity as user_id so tickets link to the right user
    _session_user_id = participant.identity or "voice_user"
    _session_thread_id = f"voice_{ctx.room.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    llm_key = os.getenv("OPENAI_API_KEY")
    use_separate_tts_key = os.getenv("USE_SEPARATE_OPENAI_TTS_KEY", "false").lower() == "true"
    tts_key = llm_key
    if use_separate_tts_key and os.getenv("OPENAI_TTS_API_KEY"):
        tts_key = os.getenv("OPENAI_TTS_API_KEY")

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=openai.STT(api_key=llm_key, model="gpt-4o-mini-transcribe"),
        llm=openai.LLM(api_key=llm_key, model="gpt-4.1"),
        tts=openai.TTS(api_key=tts_key, model="gpt-4o-mini-tts", voice="ash"),
    )

    await session.start(agent=MakTekAgent(), room=ctx.room)
    await session.say(
        "Hello! I am your MakTek support agent. How can I help you today?",
        allow_interruptions=True,
    )


def run_agent() -> None:
    load_dotenv()

    ws_url = os.getenv("LIVEKIT_API_URL", "ws://localhost:7880")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not api_key or not api_secret:
        raise RuntimeError("Missing LIVEKIT_API_KEY or LIVEKIT_API_SECRET")

    opts = WorkerOptions(
        entrypoint_fnc=entrypoint,
        ws_url=ws_url,
        api_key=api_key,
        api_secret=api_secret,
        agent_name="maktek-support",
    )
    cli.run_app(opts)


if __name__ == "__main__":
    run_agent()
