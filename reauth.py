"""
Re-authentication script for Gmail + Google Calendar.
Run this once to get fresh tokens, then start dashboard.py.
"""
import os
import sys

# Ensure app dir is on path
APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app")
sys.path.insert(0, APP_DIR)

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CREDENTIALS_FILE = os.path.join(APP_DIR, "credentials.json")

# ─── Gmail ────────────────────────────────────────────────────────────────────
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]
GMAIL_TOKEN = os.path.join(APP_DIR, "token.json")

print("=" * 60)
print("STEP 1: Gmail Authentication")
print("=" * 60)
print("A browser window will open. Sign in and grant Gmail access.")
print()

flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, GMAIL_SCOPES)
creds = flow.run_local_server(port=0, open_browser=True)

with open(GMAIL_TOKEN, "w") as f:
    f.write(creds.to_json())

print(f"\n✓ Gmail token saved to: {GMAIL_TOKEN}")

# Verify
svc = build("gmail", "v1", credentials=creds)
profile = svc.users().getProfile(userId="me").execute()
print(f"✓ Authenticated as: {profile.get('emailAddress')}")


# ─── Google Calendar ──────────────────────────────────────────────────────────
CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar.freebusy",
    "https://www.googleapis.com/auth/calendar.events"
]
CALENDAR_TOKEN = os.path.join(APP_DIR, "calendar_token.json")

print()
print("=" * 60)
print("STEP 2: Google Calendar Authentication")
print("=" * 60)
print("A second browser window will open. Grant Calendar access.")
print()

flow2 = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, CALENDAR_SCOPES)
creds2 = flow2.run_local_server(port=0, open_browser=True)

with open(CALENDAR_TOKEN, "w") as f:
    f.write(creds2.to_json())

print(f"\n✓ Calendar token saved to: {CALENDAR_TOKEN}")

# Verify calendar
from datetime import datetime, timedelta, timezone
cal_svc = build("calendar", "v3", credentials=creds2)
now = datetime.now(timezone.utc)
result = cal_svc.freebusy().query(body={
    "timeMin": now.isoformat(),
    "timeMax": (now + timedelta(hours=1)).isoformat(),
    "timeZone": "UTC",
    "items": [{"id": "primary"}]
}).execute()
print("✓ Calendar API responding OK")

print()
print("=" * 60)
print("All authentication complete!")
print("Now start the app with:")
print(f'  cd "{APP_DIR}"')
print(f'  python dashboard.py')
print("=" * 60)
