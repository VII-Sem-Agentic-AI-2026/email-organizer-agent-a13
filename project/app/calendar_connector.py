import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("Asia/Kolkata")

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = [
    "https://www.googleapis.com/auth/calendar.freebusy",
    "https://www.googleapis.com/auth/calendar.events"
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CREDENTIALS_FILE = os.path.join(
    BASE_DIR,
    "credentials.json"
)

TOKEN_FILE = os.path.join(
    BASE_DIR,
    "calendar_token.json"
)


def get_calendar_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES
            )

            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build(
        "calendar",
        "v3",
        credentials=creds
    )


class GoogleCalendarConnector:

    def __init__(self):
        self.service = get_calendar_service()

    def get_busy_periods(
        self,
        time_min: datetime,
        time_max: datetime,
        calendar_id: str = "primary"
    ):
        """
        Retrieves busy time periods from Google Calendar.
        Combines both events.list() (real-time primary calendar events, invites, meetings)
        and freebusy.query() (domain-level / external busy blocks) to ensure no scheduled
        event is ever missed or falsely marked available.
        """
        if not self.service:
            return []

        # Ensure timezone-aware
        if time_min.tzinfo is None:
            time_min = time_min.replace(tzinfo=LOCAL_TZ)
        if time_max.tzinfo is None:
            time_max = time_max.replace(tzinfo=LOCAL_TZ)

        t_min_utc = time_min.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        t_max_utc = time_max.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        busy_periods = []
        seen_spans = set()

        # 1. Primary: Query actual events directly from Google Calendar events API
        try:
            events_result = (
                self.service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=t_min_utc,
                    timeMax=t_max_utc,
                    singleEvents=True,
                    orderBy="startTime"
                )
                .execute()
            )
            for item in events_result.get("items", []):
                # Skip cancelled events
                if item.get("status") == "cancelled":
                    continue
                start_obj = item.get("start", {})
                end_obj = item.get("end", {})

                start_val = start_obj.get("dateTime")
                end_val = end_obj.get("dateTime")

                # Handle all-day events (date only, e.g. "2026-11-16")
                if not start_val and start_obj.get("date"):
                    start_val = f"{start_obj.get('date')}T00:00:00+05:30"
                if not end_val and end_obj.get("date"):
                    end_val = f"{end_obj.get('date')}T23:59:59+05:30"

                if start_val and end_val:
                    span_key = (start_val, end_val)
                    if span_key not in seen_spans:
                        seen_spans.add(span_key)
                        busy_periods.append({
                            "start": start_val,
                            "end": end_val,
                            "summary": item.get("summary", "Busy")
                        })
        except Exception as e:
            # If events.list fails (e.g. scope limitation), fallback to freebusy
            print(f"[Calendar] events.list query note: {e}")

        # 2. Also query freebusy.query() to catch domain-wide or external calendar busy blocks
        try:
            response = (
                self.service
                .freebusy()
                .query(
                    body={
                        "timeMin": t_min_utc,
                        "timeMax": t_max_utc,
                        "timeZone": "UTC",
                        "items": [
                            {
                                "id": calendar_id
                            }
                        ]
                    }
                )
                .execute()
            )
            calendar_data = response.get("calendars", {}).get(calendar_id, {})
            for b in calendar_data.get("busy", []):
                b_start = b.get("start")
                b_end = b.get("end")
                if b_start and b_end:
                    span_key = (b_start, b_end)
                    if span_key not in seen_spans:
                        seen_spans.add(span_key)
                        busy_periods.append({
                            "start": b_start,
                            "end": b_end
                        })
        except Exception as e:
            print(f"[Calendar] freebusy query note: {e}")

        return busy_periods

    def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: str = "",
        attendees: list[str] = None,
        timezone_str: str = "Asia/Kolkata",
        calendar_id: str = "primary"
    ) -> dict:
        """
        Creates an event in Google Calendar.
        Only called after explicit user approval.
        """
        if not self.service:
            raise RuntimeError("Google Calendar service is not initialized.")

        if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
            raise ValueError("start_time and end_time must be datetime instances.")

        body = {
            "summary": title,
            "description": description or "",
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": timezone_str or "Asia/Kolkata",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": timezone_str or "Asia/Kolkata",
            },
        }

        if attendees:
            body["attendees"] = [
                {"email": att.strip()}
                for att in attendees
                if att and isinstance(att, str) and "@" in att
            ]

        try:
            event = (
                self.service.events()
                .insert(calendarId=calendar_id, body=body)
                .execute()
            )
            return event
        except Exception as e:
            err_msg = str(e)
            if "insufficient" in err_msg.lower() or "insufficientpermissions" in err_msg.lower() or "403" in err_msg:
                raise PermissionError(
                    "Google Calendar token has insufficient permissions to create events. "
                    "Your token was created with freebusy-only access. "
                    "Please run 'python scripts/reauth_calendar.py' in your terminal to grant Calendar Event creation permissions, then restart the dashboard."
                ) from e
            print(f"Error creating calendar event '{title}': {e}")
            raise
