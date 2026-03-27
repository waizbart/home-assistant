#!/usr/bin/env python3
"""
Google Calendar OAuth2 — Setup único.

Execute este script UMA VEZ no Raspberry Pi para autenticar com o Google Calendar.
Ele abre o browser para você autorizar o acesso e salva o token localmente.

Pré-requisitos:
  1. Crie um projeto no Google Cloud Console (console.cloud.google.com)
  2. Ative a Google Calendar API
  3. Crie credenciais OAuth2 "Desktop app" e baixe o arquivo credentials.json
  4. Coloque credentials.json na raiz do projeto (ao lado deste script)
  5. Execute: python setup_calendar.py

Após o setup, o token.json será criado e renovado automaticamente.
"""

import os
import sys

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def main():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        print("ERROR: Google client libraries not installed.")
        print("Run: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")
        sys.exit(1)

    credentials_path = os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    token_path = os.environ.get("GOOGLE_TOKEN_PATH", "token.json")

    if not os.path.isfile(credentials_path):
        print(f"ERROR: credentials.json not found at '{credentials_path}'")
        print("Download it from Google Cloud Console > APIs & Services > Credentials.")
        sys.exit(1)

    creds = None

    if os.path.isfile(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing existing token...")
            creds.refresh(Request())
        else:
            print("Opening browser for Google OAuth2 authorization...")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as f:
            f.write(creds.to_json())
        print(f"Token saved to {token_path}")

    # Verify by listing today's calendars
    try:
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get("items", [])
        print(f"\nSetup successful! Found {len(calendars)} calendar(s):")
        for cal in calendars:
            primary = " (primary)" if cal.get("primary") else ""
            print(f"  - {cal.get('summary', 'Unnamed')}{primary}")
        print("\nYou can now run main.py normally.")
    except Exception as exc:
        print(f"WARNING: Could not verify calendar access: {exc}")


if __name__ == "__main__":
    main()
