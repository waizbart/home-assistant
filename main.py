#!/usr/bin/env python3
"""
Daily Alarm Assistant — Entry Point
Executado via cron às 7h–8h no Raspberry Pi 4B.

Pipeline:
  1. Coleta dados (clima, agenda, mercado, notícias)
  2. Monta prompt
  3. Gera texto via gpt-4o-mini
  4. Sintetiza voz via OpenAI TTS
  5. Toca o MP3 via mpg123
  6. Fallback: toca fallback.mp3 se qualquer etapa falhar
"""

import logging
import os
import sys

import config
import llm
import player
import prompt_builder
import tts
from collectors import calendar_events, market, news, weather

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run():
    logger.info("=== Daily Alarm Assistant starting ===")

    # Step 1: Collect data (failures are non-fatal — blocks are omitted gracefully)
    logger.info("Collecting weather data...")
    weather_data = weather.collect()

    logger.info("Collecting calendar events...")
    events_data = calendar_events.collect()

    logger.info("Collecting market data...")
    market_data = market.collect()

    logger.info("Collecting news...")
    news_data = news.collect()

    # Step 2: Build prompt
    logger.info("Building prompt...")
    system_prompt, user_prompt = prompt_builder.build(
        weather=weather_data,
        events=events_data,
        market=market_data,
        news=news_data,
    )

    # Step 3: Generate briefing text
    logger.info("Generating briefing text via %s...", config.LLM_MODEL)
    briefing_text = llm.generate_briefing(system_prompt, user_prompt)
    if not briefing_text:
        logger.error("LLM generation failed — playing fallback")
        _play_fallback()
        return

    # Step 4: Synthesize speech
    output_path = config.OUTPUT_AUDIO_PATH
    logger.info("Synthesizing speech to %s...", output_path)
    success = tts.synthesize(briefing_text, output_path)
    if not success:
        logger.error("TTS synthesis failed — playing fallback")
        _play_fallback()
        return

    # Step 5: Play audio
    logger.info("Playing briefing audio...")
    played = player.play(output_path)
    if not played:
        logger.error("Audio playback failed — playing fallback")
        _play_fallback()
        return

    logger.info("=== Daily Alarm Assistant completed successfully ===")


def _play_fallback():
    fallback_path = config.FALLBACK_AUDIO_PATH
    if os.path.isfile(fallback_path):
        logger.info("Playing fallback audio: %s", fallback_path)
        player.play(fallback_path)
    else:
        logger.warning("Fallback audio not found at %s — no audio played", fallback_path)


if __name__ == "__main__":
    run()
