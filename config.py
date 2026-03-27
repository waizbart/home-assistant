import os
from dotenv import load_dotenv

load_dotenv()


def get(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


OPENAI_API_KEY = get("OPENAI_API_KEY")
OPENWEATHERMAP_API_KEY = get("OPENWEATHERMAP_API_KEY")

WEATHER_CITY = get("WEATHER_CITY", "Sorocaba")
WEATHER_LAT = float(get("WEATHER_LAT", "-23.5015"))
WEATHER_LON = float(get("WEATHER_LON", "-47.4526"))
WEATHER_UNITS = get("WEATHER_UNITS", "metric")
WEATHER_LANG = get("WEATHER_LANG", "pt_br")

TTS_VOICE = get("TTS_VOICE", "random")
LLM_MODEL = get("LLM_MODEL", "gpt-4o-mini")

FALLBACK_AUDIO_PATH = get("FALLBACK_AUDIO_PATH", "fallback/fallback.mp3")
OUTPUT_AUDIO_PATH = get("OUTPUT_AUDIO_PATH", "/tmp/alarm_briefing.mp3")
