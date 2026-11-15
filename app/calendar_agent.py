from dataclasses import dataclass
from datetime import (
    datetime,
    timedelta,
    time
)
import re
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("Asia/Kolkata")


@dataclass
class ProposedSlot:
    start: datetime
    end: datetime


DAYS_OF_WEEK = {
    "monday": 0, "tuesday": 1, "wednesday": 2,
    "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
}

def parse_busy_datetime(dt_val) -> datetime:
    """
    Safely converts a datetime or string representation into an aware datetime in LOCAL_TZ or UTC.
    Handles ISO 8601 strings (with Z or +/- offset), YYYY-MM-DD date strings, and naive datetimes.
    """
    if isinstance(dt_val, datetime):
        if dt_val.tzinfo is None:
            return dt_val.replace(tzinfo=LOCAL_TZ)
        return dt_val
    if not isinstance(dt_val, str):
        dt_val = str(dt_val)
    clean = dt_val.strip()
    if len(clean) == 10 and clean.count("-") == 2:
        try:
            d = datetime.strptime(clean, "%Y-%m-%d").date()
            return datetime.combine(d, time(0, 0)).replace(tzinfo=LOCAL_TZ)
        except ValueError:
            pass
    clean = clean.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=LOCAL_TZ)
        return dt
    except Exception:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %I:%M %p"):
            try:
                return datetime.strptime(clean, fmt).replace(tzinfo=LOCAL_TZ)
            except ValueError:
                pass
        return datetime.now(LOCAL_TZ)


def resolve_datetime(day_str, time_str, reference_date=None):
    if reference_date is None:
        reference_date = datetime.now().date()
        
    clean_day = day_str.lower().strip() if day_str else ""
    
    if clean_day == "today":
        resolved_date = reference_date
    elif clean_day == "tomorrow":
        resolved_date = reference_date + timedelta(days=1)
    elif clean_day.count("-") == 2:
        try:
            resolved_date = datetime.strptime(clean_day, "%Y-%m-%d").date()
        except ValueError:
            resolved_date = reference_date
    elif clean_day in DAYS_OF_WEEK:
        target_weekday = DAYS_OF_WEEK[clean_day]
        days_ahead = target_weekday - reference_date.weekday()
        if days_ahead < 0 or (days_ahead == 0 and clean_day in DAYS_OF_WEEK):
            if days_ahead < 0:
                days_ahead += 7
        resolved_date = reference_date + timedelta(days=days_ahead)
    else:
        # Try date parsing like "Nov 16" or "16 Nov"
        parsed = False
        for fmt in ("%b %d", "%B %d", "%d %b", "%d %B"):
            try:
                p_dt = datetime.strptime(clean_day, fmt)
                resolved_date = p_dt.replace(year=reference_date.year).date()
                if resolved_date < reference_date:
                    resolved_date = resolved_date.replace(year=reference_date.year + 1)
                parsed = True
                break
            except ValueError:
                pass
        if not parsed:
            target_weekday = DAYS_OF_WEEK.get(clean_day, reference_date.weekday())
            days_ahead = target_weekday - reference_date.weekday()
            if days_ahead < 0:
                days_ahead += 7
            resolved_date = reference_date + timedelta(days=days_ahead)
    
    match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", time_str.lower() if time_str else "")
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        ampm = match.group(3)
        if ampm == "pm" and hour < 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0
        resolved_time = time(hour, minute)
    else:
        resolved_time = time(9, 0)
        
    return datetime.combine(resolved_date, resolved_time).replace(tzinfo=LOCAL_TZ)


def overlaps(
    slot_start,
    slot_end,
    busy_start,
    busy_end
):
    s_start = parse_busy_datetime(slot_start)
    s_end = parse_busy_datetime(slot_end)
    b_start = parse_busy_datetime(busy_start)
    b_end = parse_busy_datetime(busy_end)
    return (
        s_start < b_end
        and s_end > b_start
    )

def find_available_slots(
    busy_periods,
    start_date,
    days=5,
    duration_minutes=30,
    work_start_hour=9,
    work_end_hour=17
):
    slots = []

    for day_offset in range(days):

        current_date = (
            start_date
            + timedelta(days=day_offset)
        )

        # Skip Saturday and Sunday
        if current_date.weekday() >= 5:
            continue

        current_time = datetime.combine(
            current_date,
            time(work_start_hour, 0)
        ).replace(tzinfo=LOCAL_TZ)

        work_end = datetime.combine(
            current_date,
            time(work_end_hour, 0)
        ).replace(tzinfo=LOCAL_TZ)

        while (
            current_time
            + timedelta(minutes=duration_minutes)
            <= work_end
        ):

            slot_end = (
                current_time
                + timedelta(minutes=duration_minutes)
            )

            is_busy = False

            for busy in busy_periods:
                if overlaps(
                    current_time,
                    slot_end,
                    busy.get("start"),
                    busy.get("end")
                ):
                    is_busy = True
                    break

            if not is_busy:
                slots.append(
                    ProposedSlot(
                        start=current_time,
                        end=slot_end
                    )
                )

            current_time += timedelta(minutes=30)

    return slots


def propose_meeting_slots(
    calendar_connector,
    start_date,
    days=5,
    duration_minutes=30,
    number_of_slots=5
):
    # Backward compatibility
    return propose_meeting_slots_with_preference(
        calendar_connector, start_date, None, None, days, duration_minutes, number_of_slots
    )[0]


def propose_meeting_slots_with_preference(
    calendar_connector,
    start_date,
    proposed_date_str=None,
    proposed_time_str=None,
    days=5,
    duration_minutes=30,
    number_of_slots=5
):
    time_min = datetime.combine(start_date, time(0, 0)).replace(tzinfo=LOCAL_TZ)
    time_max = time_min + timedelta(days=days)

    busy_periods = calendar_connector.get_busy_periods(time_min, time_max)

    requested_slot = None
    requested_status = None
    now_dt = datetime.now(LOCAL_TZ)

    if proposed_date_str and proposed_time_str:
        requested_dt = resolve_datetime(proposed_date_str, proposed_time_str, start_date)
        req_end = requested_dt + timedelta(minutes=duration_minutes)

        is_busy = False
        # If requested slot is already in the past, treat as unavailable
        if requested_dt < now_dt:
            is_busy = True
        else:
            for busy in busy_periods:
                if overlaps(requested_dt, req_end, busy.get("start"), busy.get("end")):
                    is_busy = True
                    break

        requested_slot = ProposedSlot(start=requested_dt, end=req_end)
        requested_status = "BUSY" if is_busy else "AVAILABLE"

    slots = []
    if requested_slot and requested_status == "AVAILABLE":
        slots.append(requested_slot)

    if requested_slot:
        target_dates = [requested_slot.start.date()]
        for d in range(days):
            candidate = start_date + timedelta(days=d)
            if candidate != requested_slot.start.date():
                target_dates.append(candidate)
    else:
        target_dates = [start_date + timedelta(days=d) for d in range(days)]

    for d in target_dates:
        if d.weekday() >= 5:
            continue

        current_time = datetime.combine(d, time(9, 0)).replace(tzinfo=LOCAL_TZ)
        work_end = datetime.combine(d, time(17, 0)).replace(tzinfo=LOCAL_TZ)

        day_slots = []
        while current_time + timedelta(minutes=duration_minutes) <= work_end:
            slot_end = current_time + timedelta(minutes=duration_minutes)

            # Skip past slots if looking at today
            if current_time < now_dt:
                current_time += timedelta(minutes=30)
                continue

            if requested_slot and current_time == requested_slot.start:
                current_time += timedelta(minutes=30)
                continue

            is_busy = False
            for busy in busy_periods:
                if overlaps(current_time, slot_end, busy.get("start"), busy.get("end")):
                    is_busy = True
                    break

            if not is_busy:
                day_slots.append(ProposedSlot(start=current_time, end=slot_end))

            current_time += timedelta(minutes=30)

        if requested_slot and d == requested_slot.start.date():
            day_slots.sort(key=lambda s: abs((s.start - requested_slot.start).total_seconds()))

        for s in day_slots:
            if len(slots) >= number_of_slots:
                break
            slots.append(s)

        if len(slots) >= number_of_slots:
            break

    return slots, requested_status