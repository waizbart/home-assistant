"""
Converte o texto do briefing em áudio MP3 via OpenAI TTS.
"""

import logging
import os
from typing import Optional

from openai import OpenAI

import config

logger = logging.getLogger(__name__)


def synthesize(text: str, output_path: str) -> bool:
    """
    Converts text to speech and saves as MP3 at output_path.
    Returns True on success, False on failure.
    """
    try:
        client = OpenAI(api_key=config.OPENAI_API_KEY)

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with client.audio.speech.with_streaming_response.create(
            model="tts-1-hd",
            voice=config.TTS_VOICE,
            input=text,
            response_format="mp3",
        ) as response:
            response.stream_to_file(output_path)

        logger.info("Audio saved to %s", output_path)
        return True
    except Exception as exc:
        logger.error("TTS synthesis failed: %s", exc)
        return False
