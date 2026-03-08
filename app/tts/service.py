"""
Text-to-Speech service using Edge-TTS.
Converts text to audio (MP3) with configurable voice and rate.
"""

import logging
import edge_tts
from typing import Optional

logger = logging.getLogger(__name__)

class TTSService:
    """Service for generating speech from text using Edge-TTS."""

    # Default voice: "en-US-JennyNeural" is clear and friendly.
    # For Kenyan English, you might try "en-KE-AsiliaNeural" if available.
    DEFAULT_VOICE = "en-US-JennyNeural"
    # Slower rate helps comprehension for students.
    DEFAULT_RATE = "+0%"  # Can be "-10%" for slower, "+10%" for faster.

    async def synthesize(
        self,
        text: str,
        voice: str = DEFAULT_VOICE,
        rate: str = DEFAULT_RATE
    ) -> bytes:
        """
        Convert text to speech and return MP3 audio bytes.
        """
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            logger.info(f"TTS synthesized {len(text)} chars with voice {voice}")
            return audio_data
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            raise

# Singleton instance
tts_service = TTSService()