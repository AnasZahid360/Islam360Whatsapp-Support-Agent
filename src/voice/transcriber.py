"""Deprecated local transcription module.

Voice transcription now runs through LiveKit Agent SDK.
"""


def transcribe_audio(audio_path: str, language: str = None) -> dict:
    _ = audio_path
    _ = language
    raise RuntimeError(
        "Local transcription is removed. Use LiveKit voice flow: request token from /livekit-token and connect via frontend/livekit-integration.js"
    )
