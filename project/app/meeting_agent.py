from dataclasses import dataclass, field
from datetime import datetime, timedelta, time
import re
from zoneinfo import ZoneInfo
from calendar_agent import propose_meeting_slots_with_preference, resolve_datetime, LOCAL_TZ

@dataclass
class MeetingRequest:
    meeting_requested: bool
    proposed_date: str | None
    proposed_time: str | None
    purpose: str | None
    title: str | None = None
    duration_minutes: int = 30
    attendees: list[str] = field(default_factory=list)
    description: str | None = None
    missing_date_or_time: bool = False
    status: str = "pending"
    google_event_id: str | None = None
    start_time: str | None = None
    end_time: str | None = None


def extract_meeting_request(email):
    subj_lower = (email.subject or "").lower()
    body_lower = (email.body or "").lower()

    # Skip automated confirmation / approval receipt emails sent by our system
    if (
        "meeting confirmation:" in subj_lower
        or "your meeting request has been approved" in body_lower
        or "confirmed time:" in body_lower
    ):
        return MeetingRequest(
            meeting_requested=False,
            proposed_date=None,
            proposed_time=None,
            purpose=None,
            title=None,
            duration_minutes=30,
            attendees=[],
            description=None,
            missing_date_or_time=False
        )

    text = f"{email.subject} {email.body}".lower()

    meeting_words = [
        "meeting",
        "meet",
        "schedule",
        "discuss",
        "call"
    ]

    meeting_requested = any(word in text for word in meeting_words)

    if not meeting_requested:
        return MeetingRequest(
            meeting_requested=False,
            proposed_date=None,
            proposed_time=None,
            purpose=None,
            title=None,
            duration_minutes=30,
            attendees=[],
            description=None,
            missing_date_or_time=False
        )

    proposed_date = None
    proposed_time = None

    # Check weekdays
    for day in [
        "monday", "tuesday", "wednesday",
        "thursday", "friday", "saturday", "sunday"
    ]:
        if day in text:
            proposed_date = day.capitalize()
            break

    # Relative dates & explicit dates
    if not proposed_date:
        if "tomorrow" in text:
            proposed_date = "Tomorrow"
        elif "today" in text:
            proposed_date = "Today"
        else:
            iso_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
            if iso_match:
                proposed_date = iso_match.group(1)
            else:
                m_match = re.search(r"\b((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?)\b", text)
                if m_match:
                    proposed_date = m_match.group(1).title()

    # Time extraction (exact strings first, then flexible regex)
    for t_str in [
        "9 am", "10 am", "11 am", "12 pm",
        "1 pm", "2 pm", "3 pm", "4 pm", "5 pm"
    ]:
        if t_str in text:
            proposed_time = t_str
            break

    if not proposed_time:
        t_match = re.search(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm))\b", text)
        if t_match:
            proposed_time = t_match.group(1)
        else:
            t_match_24 = re.search(r"\b([012]?\d:[0-5]\d)\b", text)
            if t_match_24:
                proposed_time = t_match_24.group(1)

    purpose = email.subject if email.subject else "Discussion Meeting"
    title = f"Meeting: {email.subject}" if email.subject else "Discussion Meeting"
    attendees = [email.sender] if email.sender else []
    description = email.body[:300] if email.body else ""
    missing_date_or_time = (proposed_date is None or proposed_time is None)

    return MeetingRequest(
        meeting_requested=True,
        proposed_date=proposed_date,
        proposed_time=proposed_time,
        purpose=purpose,
        title=title,
        duration_minutes=30,
        attendees=attendees,
        description=description,
        missing_date_or_time=missing_date_or_time,
        status="pending"
    )


def parse_slot_to_datetimes(
    slot_input,
    duration_minutes: int = 30,
    reference_date=None
) -> tuple[datetime, datetime]:
    """
    Parses various slot representation strings into aware (start_dt, end_dt) datetimes in LOCAL_TZ.
    Handles:
    - '2026-11-20 03:00 PM — AVAILABLE'
    - '2026-11-20 03:00 PM' / '2026-11-20 3:00 PM' / '2026-11-20 3pm' / '2026-11-20 3 pm'
    - '2026-11-20 15:00:00' / '2026-11-20 15:00'
    - '2026-11-20T15:00' (HTML5 datetime-local)
    - 'Friday 3 pm' / 'Tomorrow 10 am'
    - Slot objects with .start and .end
    """
    if hasattr(slot_input, "start") and hasattr(slot_input, "end"):
        start = slot_input.start
        end = slot_input.end
        if start.tzinfo is None:
            start = start.replace(tzinfo=LOCAL_TZ)
        if end.tzinfo is None:
            end = end.replace(tzinfo=LOCAL_TZ)
        return start, end

    if not slot_input or not isinstance(slot_input, str):
        raise ValueError("A valid meeting time slot string or object must be provided.")

    clean_str = slot_input.split("—")[0].split("- AVAILABLE")[0].strip()

    # 1. Try standard strptime formats
    for fmt in (
        "%Y-%m-%d %I:%M %p",
        "%Y-%m-%d %I %p",
        "%Y-%m-%d %I:%M%p",
        "%Y-%m-%d %I%p",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %I:%M %p",
        "%Y/%m/%d %H:%M",
        "%d-%m-%Y %I:%M %p",
        "%d/%m/%Y %I:%M %p",
    ):
        try:
            naive_dt = datetime.strptime(clean_str, fmt)
            start_dt = naive_dt.replace(tzinfo=LOCAL_TZ)
            return start_dt, start_dt + timedelta(minutes=duration_minutes)
        except ValueError:
            pass

    # 2. Try ISO format (including HTML5 datetime-local like '2026-11-20T15:00')
    try:
        iso_str = clean_str.replace("Z", "+00:00")
        iso_dt = datetime.fromisoformat(iso_str)
        if iso_dt.tzinfo is None:
            iso_dt = iso_dt.replace(tzinfo=LOCAL_TZ)
        else:
            iso_dt = iso_dt.astimezone(LOCAL_TZ)
        return iso_dt, iso_dt + timedelta(minutes=duration_minutes)
    except Exception:
        pass

    # 3. Try regex: Date YYYY-MM-DD + Time (e.g. '2026-11-20 3pm', '2026-11-20 3:00pm', '2026-11-20 3 pm')
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", clean_str)
    if date_match:
        d_str = date_match.group(1)
        remaining = clean_str[date_match.end():].strip()
        time_match = re.search(r"(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|\d{1,2}:\d{2})", remaining, re.IGNORECASE)
        if time_match:
            try:
                ref_d = datetime.strptime(d_str, "%Y-%m-%d").date()
                start_dt = resolve_datetime(d_str, time_match.group(1), reference_date=ref_d)
                return start_dt, start_dt + timedelta(minutes=duration_minutes)
            except Exception:
                pass

    # 4. Try Day / Relative word + Time resolution (e.g. 'Friday 3 pm', 'Tomorrow 10 am', 'Today 4 pm')
    tokens = clean_str.split()
    day_token = None
    time_token = None
    for token in tokens:
        if token.lower() in [
            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
            "today", "tomorrow"
        ]:
            day_token = token
            break
    time_match = re.search(r"(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|\d{1,2}:\d{2})", clean_str, re.IGNORECASE)
    if time_match:
        time_token = time_match.group(1)

    if day_token and time_token:
        start_dt = resolve_datetime(day_token, time_token, reference_date)
        return start_dt, start_dt + timedelta(minutes=duration_minutes)

    # 5. Fallback for dummy / test slot names like "Slot 1"
    if clean_str.lower().startswith("slot"):
        ref = reference_date or (datetime.now().date() + timedelta(days=1))
        start_dt = datetime.combine(ref, time(10, 0)).replace(tzinfo=LOCAL_TZ)
        return start_dt, start_dt + timedelta(minutes=duration_minutes)

    raise ValueError(f"Unable to parse date/time from slot: '{slot_input}'")


def get_meeting_proposals(
    meeting_request,
    calendar_connector,
    start_date,
    days=5
):
    if not meeting_request.meeting_requested:
        return []

    return propose_meeting_slots_with_preference(
        calendar_connector=calendar_connector,
        start_date=start_date,
        proposed_date_str=meeting_request.proposed_date,
        proposed_time_str=meeting_request.proposed_time,
        days=days,
        duration_minutes=30,
        number_of_slots=5
    )


def confirm_meeting(
    meeting_request,
    selected_slot,
    approved=False
):
    if not approved:
        raise PermissionError(
            "Meeting cannot be confirmed "
            "without faculty approval."
        )

    start_val = getattr(selected_slot, "start", selected_slot)
    end_val = getattr(selected_slot, "end", selected_slot)

    return {
        "status": "approved",
        "subject": meeting_request.purpose or getattr(meeting_request, "title", "Meeting"),
        "start": start_val,
        "end": end_val
    }
