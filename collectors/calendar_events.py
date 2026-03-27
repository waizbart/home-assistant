"""
Coleta eventos do Google Calendar para o dia atual.
Requer credenciais OAuth2 geradas pelo setup_calendar.py.
"""

import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

import config

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def collect() -> Optional[list]:
    """
    Returns a list of today's events, sorted by start time, or None on failure.

    [
        {
            "title": "Call com cliente",
            "start": "10:00",
            "end": "11:00",
            "duration_min": 60,
            "location": "Google Meet",
            "all_day": False
        },
        ...
    ]
    """
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        logger.warning("google-api-python-client not installed — skipping calendar")
        return None

    creds = _load_credentials()
    if creds is None:
        logger.warning("Google Calendar credentials not available — skipping")
        return None

    try:
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)

        now = datetime.now()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=day_start.astimezone().isoformat(),
                timeMax=day_end.astimezone().isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = []
        for item in result.get("items", []):
            event = _parse_event(item)
            if event:
                events.append(event)

        return events
    except Exception as exc:
        logger.warning("Google Calendar API call failed: %s", exc)
        return None


def _load_credentials():
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        token_path = config.GOOGLE_TOKEN_PATH
        creds_path = config.GOOGLE_CREDENTIALS_PATH

        if not os.path.exists(token_path):
            logger.warning("Token file not found at %s — run setup_calendar.py", token_path)
            return None

        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, "w") as f:
                f.write(creds.to_json())

        return creds
    except Exception as exc:
        logger.warning("Failed to load Google credentials: %s", exc)
        return None


def _parse_event(item: dict) -> Optional[dict]:
    try:
        title = item.get("summary", "(sem título)")
        start_raw = item["start"]
        end_raw = item["end"]

        all_day = "date" in start_raw and "dateTime" not in start_raw

        if all_day:
            return {
                "title": title,
                "start": None,
                "end": None,
                "duration_min": None,
                "location": item.get("location"),
                "all_day": True,
            }

        start_dt = datetime.fromisoformat(start_raw["dateTime"])
        end_dt = datetime.fromisoformat(end_raw["dateTime"])
        duration_min = int((end_dt - start_dt).total_seconds() / 60)

        return {
            "title": title,
            "start": start_dt.strftime("%H:%M"),
            "end": end_dt.strftime("%H:%M"),
            "duration_min": duration_min,
            "location": item.get("location"),
            "all_day": False,
        }
    except Exception as exc:
        logger.warning("Failed to parse calendar event: %s", exc)
        return None
