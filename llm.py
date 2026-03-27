"""
Gera o texto do briefing via OpenAI gpt-4o-mini.
"""

import logging
from typing import Optional

from openai import OpenAI

import config

logger = logging.getLogger(__name__)


def generate_briefing(system_prompt: str, user_prompt: str) -> Optional[str]:
    """
    Calls the OpenAI chat completion API and returns the generated text,
    or None on failure.
    """
    try:
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=700,
        )
        text = response.choices[0].message.content
        logger.info("Generated briefing: %d chars", len(text))
        return text
    except Exception as exc:
        logger.error("LLM generation failed: %s", exc)
        return None
