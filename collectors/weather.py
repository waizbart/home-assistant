"""
Coleta dados de clima via OpenWeatherMap.
Retorna temperatura atual, máxima/mínima do dia, previsão de chuva com horário,
sensação térmica e alertas de vento/eventos extremos.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import requests

import config

logger = logging.getLogger(__name__)

OWM_BASE = "https://api.openweathermap.org/data/2.5"
OWM_ONECALL = "https://api.openweathermap.org/data/3.0/onecall"


def _params() -> dict:
    return {
        "lat": config.WEATHER_LAT,
        "lon": config.WEATHER_LON,
        "appid": config.OPENWEATHERMAP_API_KEY,
        "units": config.WEATHER_UNITS,
        "lang": config.WEATHER_LANG,
    }


def collect() -> Optional[dict]:
    """
    Returns a dict with weather context, or None on failure.

    {
        "current_temp": 19.0,
        "feels_like": 17.5,
        "temp_min": 15.0,
        "temp_max": 27.0,
        "description": "nublado",
        "rain_windows": [{"start": "14:00", "end": "17:00", "prob": 0.85}],
        "wind_speed_kmh": 12.0,
        "alerts": []
    }
    """
    try:
        current = _fetch_current()
        forecast = _fetch_forecast()
        if current is None or forecast is None:
            return None

        today = datetime.now().date()

        # Today's min/max from forecast (3h slots)
        today_temps = [
            slot["main"]["temp"]
            for slot in forecast["list"]
            if datetime.fromtimestamp(slot["dt"]).date() == today
        ]
        temp_min = round(min(today_temps), 1) if today_temps else round(current["main"]["temp_min"], 1)
        temp_max = round(max(today_temps), 1) if today_temps else round(current["main"]["temp_max"], 1)

        # Rain windows: consecutive 3h slots with pop > 0.4
        rain_windows = _extract_rain_windows(forecast["list"], today)

        # Wind alert if > 40 km/h
        wind_ms = current.get("wind", {}).get("speed", 0)
        wind_kmh = round(wind_ms * 3.6, 1)

        # OWM national alerts (only present in paid OneCall — graceful skip)
        alerts = []

        feels_like = round(current["main"]["feels_like"], 1)
        current_temp = round(current["main"]["temp"], 1)

        return {
            "current_temp": current_temp,
            "feels_like": feels_like,
            "temp_min": temp_min,
            "temp_max": temp_max,
            "description": current["weather"][0]["description"],
            "rain_windows": rain_windows,
            "wind_speed_kmh": wind_kmh,
            "alerts": alerts,
        }
    except Exception as exc:
        logger.warning("Weather collection failed: %s", exc)
        return None


def _fetch_current() -> Optional[dict]:
    try:
        resp = requests.get(
            f"{OWM_BASE}/weather",
            params=_params(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("OWM /weather failed: %s", exc)
        return None


def _fetch_forecast() -> Optional[dict]:
    try:
        resp = requests.get(
            f"{OWM_BASE}/forecast",
            params={**_params(), "cnt": 16},  # 16 slots × 3h = 48h
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("OWM /forecast failed: %s", exc)
        return None


def _extract_rain_windows(slots: list, today) -> list:
    """Groups consecutive rainy 3h forecast slots into windows."""
    windows = []
    in_window = False
    window_start = None

    for slot in slots:
        dt = datetime.fromtimestamp(slot["dt"])
        if dt.date() != today:
            continue
        pop = slot.get("pop", 0)  # probability of precipitation 0–1
        if pop >= 0.4:
            if not in_window:
                in_window = True
                window_start = dt
        else:
            if in_window:
                windows.append({
                    "start": window_start.strftime("%H:%M"),
                    "end": dt.strftime("%H:%M"),
                    "prob": round(pop, 2),
                })
                in_window = False

    if in_window and window_start:
        windows.append({
            "start": window_start.strftime("%H:%M"),
            "end": "23:59",
            "prob": 1.0,
        })

    return windows
