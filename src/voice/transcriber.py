"""
Voice transcription service using faster-whisper.

Converts audio files (voice messages) to text using the Whisper model
running locally — completely free, no API key required.
"""

import os
import logging
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

# Model size options: "tiny", "base", "small", "medium", "large-v3"
# "base" is a good balance of speed and accuracy (~150MB)
# "small" is better for Urdu/multilingual (~500MB)
MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")

# Compute type: "int8" for CPU, "float16" for GPU
COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

# Supported audio formats
SUPPORTED_FORMATS = {".mp3", ".mp4", ".m4a", ".wav", ".ogg", ".webm", ".flac", ".opus"}

# Singleton model instance (loaded once, reused)
_model = None


def _get_model() -> WhisperModel:
    """
    Get or initialize the Whisper model (singleton).
    The model is loaded once on first call and reused for all subsequent calls.
    """
    global _model
    if _model is None:
        logger.info(f"Loading Whisper model: {MODEL_SIZE} (compute_type={COMPUTE_TYPE})")
        _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type=COMPUTE_TYPE)
        logger.info("Whisper model loaded successfully.")
    return _model


def transcribe_audio(audio_path: str, language: str = None) -> dict:
    """
    Transcribe an audio file to text using faster-whisper.

    Args:
        audio_path: Path to the audio file.
        language: Optional language code (e.g., "en", "ur"). 
                  If None, auto-detects the language.

    Returns:
        dict with keys:
            - "text": The full transcribed text.
            - "language": Detected/specified language code.
            - "segments": List of segment dicts with start, end, text.

    Raises:
        ValueError: If the file format is not supported.
        FileNotFoundError: If the audio file does not exist.
        RuntimeError: If transcription fails.
    """
    # Validate file exists
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Validate file format
    ext = os.path.splitext(audio_path)[1].lower()
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported audio format: '{ext}'. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}"
        )

    try:
        model = _get_model()

        # Transcribe with a prompt to guide vocabulary toward "MakTek"
        transcribe_kwargs = {"initial_prompt": "MakTek"}
        if language:
            transcribe_kwargs["language"] = language

        segments, info = model.transcribe(audio_path, **transcribe_kwargs)

        # Collect segments
        segment_list = []
        full_text_parts = []

        for segment in segments:
            segment_list.append({
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": segment.text.strip()
            })
            full_text_parts.append(segment.text.strip())

        full_text = " ".join(full_text_parts)

        logger.info(
            f"Transcription complete: language={info.language}, "
            f"duration={info.duration:.1f}s, segments={len(segment_list)}"
        )

        return {
            "text": full_text,
            "language": info.language,
            "segments": segment_list
        }

    except (ValueError, FileNotFoundError):
        raise
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise RuntimeError(f"Failed to transcribe audio: {e}")
