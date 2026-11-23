"""
Calendar-only re-auth script (ASCII-safe output for Windows cp1252).
"""
import os
import sys

# Ensure app dir is on path
APP_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
if not os.path.exists(APP_DIR):
    APP_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "app"))
sys.path.insert(0, APP_DIR)

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone

CREDENTIALS_FILE = os.path.join(APP_DIR, "credentials.json")
CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar.freebusy",
    "https://www.googleapis.com/auth/calendar.events"
]
CALENDAR_TOKEN = os.path.join(APP_DIR, "calendar_token.json")

print("=" * 60)
print("Calendar Authentication")
print("=" * 60)
print("A browser window will open. Grant Calendar access.")
print()

flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, CALENDAR_SCOPES)
creds = flow.run_local_server(port=0, open_browser=True)

with open(CALENDAR_TOKEN, "w") as f:
    f.write(creds.to_json())

print("Calendar token saved to:", CALENDAR_TOKEN)

# Verify calendar
cal_svc = build("calendar", "v3", credentials=creds)
now = datetime.now(timezone.utc)
result = cal_svc.freebusy().query(body={
    "timeMin": now.isoformat(),
    "timeMax": (now + timedelta(hours=1)).isoformat(),
    "timeZone": "UTC",
    "items": [{"id": "primary"}]
}).execute()
print("Calendar API OK")
print()
print("=" * 60)
print("ALL AUTH COMPLETE - starting Flask server...")
print("=" * 60)
