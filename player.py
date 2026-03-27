"""
Reproduz arquivo MP3 usando mpg123.
"""

import logging
import os
import subprocess

logger = logging.getLogger(__name__)


def play(audio_path: str) -> bool:
    """
    Plays an MP3 file via mpg123.
    Returns True on success, False on failure.
    """
    if not os.path.isfile(audio_path):
        logger.error("Audio file not found: %s", audio_path)
        return False

    try:
        result = subprocess.run(
            ["mpg123", "-q", "-o", "alsa", audio_path],
            check=True,
            timeout=300,  # 5 min max
        )
        return True
    except FileNotFoundError:
        logger.error("mpg123 not found. Install with: sudo apt install mpg123")
        return False
    except subprocess.TimeoutExpired:
        logger.error("mpg123 playback timed out")
        return False
    except subprocess.CalledProcessError as exc:
        logger.error("mpg123 exited with error: %s", exc)
        return False
