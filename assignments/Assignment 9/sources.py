from models import SourceMessage

# Local demonstration data standing in for the actual thread history and owner's past replies.
THREAD_HISTORY = {
    "T-101": [
        SourceMessage("T-101-M1", "thread_history", "The project report is due on Friday, 28 November."),
        SourceMessage("T-101-M2", "thread_history", "The student has completed the data collection and needs help with the report format."),
    ],
    "T-102": [
        SourceMessage("T-102-M1", "thread_history", "Please send the revised event schedule by Wednesday."),
        SourceMessage("T-102-M2", "thread_history", "The event is planned for the department seminar hall."),
    ],
}

OWNER_PAST_REPLIES = {
    "T-101": [
        SourceMessage("R-101-1", "owner_past_reply", "I can review the report format after you share the completed draft."),
    ],
    "T-102": [
        SourceMessage("R-102-1", "owner_past_reply", "Please include the confirmed timings when you send the revised schedule."),
    ],
}

def get_sources(unit_id: str):
    return list(THREAD_HISTORY.get(unit_id, [])) + list(OWNER_PAST_REPLIES.get(unit_id, []))
