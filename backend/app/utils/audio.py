"""
Audio Utilities
Helper functions for audio processing and format conversion
"""

import io
import base64
from typing import Tuple, Optional

from app.core.logging import get_logger
from app.models.voice import AudioFormat

logger = get_logger(__name__)

# Maximum audio file size (10MB)
MAX_AUDIO_SIZE = 10 * 1024 * 1024


def validate_audio_size(audio_data: bytes) -> bool:
    """Validate audio file size

    Args:
        audio_data: Audio file bytes

    Returns:
        True if valid size, False otherwise
    """
    size = len(audio_data)
    if size > MAX_AUDIO_SIZE:
        logger.warning(
            "audio_size_exceeded",
            extra_fields={"size_bytes": size, "max_bytes": MAX_AUDIO_SIZE}
        )
        return False
    return True


def detect_audio_format(audio_data: bytes) -> Optional[str]:
    """Detect audio format from file header

    Args:
        audio_data: Audio file bytes

    Returns:
        MIME type string or None if unknown
    """
    if not audio_data or len(audio_data) < 12:
        return None

    # Check file signatures
    if audio_data[:4] == b'RIFF' and audio_data[8:12] == b'WAVE':
        return AudioFormat.WAV
    elif audio_data[:3] == b'ID3' or audio_data[:2] == b'\xff\xfb':
        return AudioFormat.MP3
    elif audio_data[:4] == b'OggS':
        return AudioFormat.OGG
    elif audio_data[:4] == b'\x1a\x45\xdf\xa3':  # EBML/WebM header
        return AudioFormat.WEBM

    logger.warning("unknown_audio_format", extra_fields={"header": audio_data[:12].hex()})
    return None


def convert_to_base64(audio_data: bytes) -> str:
    """Convert audio bytes to base64 string

    Args:
        audio_data: Audio file bytes

    Returns:
        Base64 encoded string
    """
    return base64.b64encode(audio_data).decode('utf-8')


def convert_from_base64(base64_data: str) -> bytes:
    """Convert base64 string to audio bytes

    Args:
        base64_data: Base64 encoded string

    Returns:
        Audio file bytes
    """
    return base64.b64decode(base64_data)


def prepare_audio_for_gemini(audio_data: bytes, mime_type: Optional[str] = None) -> Tuple[bytes, str]:
    """Prepare audio data for Gemini API

    Args:
        audio_data: Raw audio bytes
        mime_type: Optional MIME type hint

    Returns:
        Tuple of (prepared_audio_bytes, mime_type)
    """
    try:
        # Validate size
        if not validate_audio_size(audio_data):
            raise ValueError(f"Audio file too large (max {MAX_AUDIO_SIZE} bytes)")

        # Detect format if not provided
        if not mime_type:
            mime_type = detect_audio_format(audio_data)

        if not mime_type:
            # Default to WAV if unknown
            mime_type = AudioFormat.WAV
            logger.warning("defaulting_to_wav_format")

        logger.info(
            "audio_prepared_for_gemini",
            extra_fields={"size_bytes": len(audio_data), "mime_type": mime_type}
        )

        return audio_data, mime_type

    except Exception as e:
        logger.error(
            "audio_preparation_failed",
            extra_fields={"error": str(e), "error_type": type(e).__name__},
            exc_info=True
        )
        raise


def get_supported_formats() -> list:
    """Get list of supported audio formats

    Returns:
        List of supported MIME types
    """
    return [AudioFormat.WAV, AudioFormat.MP3, AudioFormat.WEBM, AudioFormat.OGG]


def format_audio_duration(duration_seconds: float) -> str:
    """Format audio duration for display

    Args:
        duration_seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "1:23")
    """
    minutes = int(duration_seconds // 60)
    seconds = int(duration_seconds % 60)
    return f"{minutes}:{seconds:02d}"


def create_silence_wav(duration_seconds: float = 0.5) -> bytes:
    """Create a silent WAV file (useful for testing)

    Args:
        duration_seconds: Duration of silence

    Returns:
        WAV file bytes
    """
    import struct
    import wave

    # 16-bit, 16kHz mono
    sample_rate = 16000
    num_channels = 1
    sample_width = 2  # 16-bit
    num_samples = int(sample_rate * duration_seconds)

    # Create WAV in memory
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(num_channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)

        # Write silence (zeros)
        silence = struct.pack(f'{num_samples}h', *([0] * num_samples))
        wav_file.writeframes(silence)

    return wav_buffer.getvalue()
