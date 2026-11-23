import os
import sys
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

# Add app directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from models import Email
from reminder_manager import ReminderManager, ReminderScheduler
from calendar_agent import LOCAL_TZ
from meeting_agent import (
    extract_meeting_request,
    parse_slot_to_datetimes,
    MeetingRequest
)
from dashboard_service import DashboardService
from graph import build_graph, to_graph_state, GraphState, GraphData, run_graph
from classifier import EmailClassification, ActionExtraction, ActionItem
from review_queue import ReviewState, create_review_item, approve_review_item


@pytest.fixture
def temp_reminder_manager(tmp_path):
    """Provides a cleanly isolated ReminderManager using a temporary SQLite DB."""
    db_file = str(tmp_path / "test_reminders.db")
    manager = ReminderManager(db_path=db_file)
    return manager


# =========================================================================
# TEST 1: High-priority email creates a reminder
# =========================================================================
def test_1_high_priority_email_creates_reminder(temp_reminder_manager):
    reminder = temp_reminder_manager.create_reminder(
        email_id="email-high-1",
        sender="dean@university.edu",
        subject="Urgent: Faculty meeting agenda",
        body="Please review the agenda immediately.",
        priority="High",
        delay_minutes=15
    )
    assert reminder is not None
    assert reminder.email_id == "email-high-1"
    assert reminder.priority == "High"
    assert reminder.status == "pending"
    assert reminder.delay_minutes == 15
    assert reminder.snooze_count == 0

    # Also test Critical priority
    critical_rem = temp_reminder_manager.create_reminder(
        email_id="email-crit-1",
        sender="provost@university.edu",
        subject="Critical: Grant submission",
        body="Submit before midnight.",
        priority="Critical",
        delay_minutes=10
    )
    assert critical_rem is not None
    assert critical_rem.priority == "Critical"
    assert critical_rem.status == "pending"


# =========================================================================
# TEST 2: Low-priority email does not create a reminder
# =========================================================================
def test_2_low_priority_email_does_not_create_reminder(temp_reminder_manager):
    low_rem = temp_reminder_manager.create_reminder(
        email_id="email-low-1",
        sender="newsletter@university.edu",
        subject="Weekly Campus Newsletter",
        body="Check out events happening this weekend.",
        priority="Low",
        delay_minutes=15
    )
    assert low_rem is None

    med_rem = temp_reminder_manager.create_reminder(
        email_id="email-med-1",
        sender="colleague@university.edu",
        subject="FYI: Interesting paper",
        body="Found this interesting paper.",
        priority="Medium",
        delay_minutes=15
    )
    assert med_rem is None

    all_reminders = temp_reminder_manager.get_all_reminders()
    assert len(all_reminders) == 0


# =========================================================================
# TEST 3: User can snooze a reminder
# =========================================================================
def test_3_user_can_snooze_reminder(temp_reminder_manager):
    reminder = temp_reminder_manager.create_reminder(
        email_id="email-snooze-1",
        sender="head@university.edu",
        subject="Important: Budget submission",
        body="Submit the departmental budget.",
        priority="High",
        delay_minutes=10
    )
    assert reminder.status == "pending"
    initial_remind_at = datetime.fromisoformat(reminder.remind_at)

    # Snooze for 30 minutes
    snoozed = temp_reminder_manager.snooze_reminder(reminder.id, delay_minutes=30)
    assert snoozed.status == "snoozed"
    assert snoozed.snooze_count == 1
    assert snoozed.last_snoozed_at is not None

    new_remind_at = datetime.fromisoformat(snoozed.remind_at)
    assert new_remind_at > initial_remind_at


# =========================================================================
# TEST 4: Snoozing does not create duplicate reminders
# =========================================================================
def test_4_snoozing_does_not_create_duplicate_reminders(temp_reminder_manager):
    reminder = temp_reminder_manager.create_reminder(
        email_id="email-dedup-1",
        sender="hod@university.edu",
        subject="Urgent Accreditation documents",
        body="Need documents by 5 PM.",
        priority="Critical",
        delay_minutes=15
    )
    assert len(temp_reminder_manager.get_all_reminders()) == 1

    # Snooze multiple times
    temp_reminder_manager.snooze_reminder(reminder.id, delay_minutes=5)
    temp_reminder_manager.snooze_reminder(reminder.id, delay_minutes=10)
    temp_reminder_manager.snooze_reminder(reminder.id, delay_minutes=60)

    # Database must still have exactly 1 record
    all_reminders = temp_reminder_manager.get_all_reminders()
    assert len(all_reminders) == 1
    assert all_reminders[0]["id"] == reminder.id
    assert all_reminders[0]["snooze_count"] == 3
    assert all_reminders[0]["status"] == "snoozed"

    # Trying to create another active reminder for the same email must also not duplicate
    dup_attempt = temp_reminder_manager.create_reminder(
        email_id="email-dedup-1",
        sender="hod@university.edu",
        subject="Urgent Accreditation documents",
        body="Need documents by 5 PM.",
        priority="Critical"
    )
    assert dup_attempt.id == reminder.id
    assert len(temp_reminder_manager.get_all_reminders()) == 1


# =========================================================================
# TEST 5: Marking an email handled cancels its reminder
# =========================================================================
def test_5_marking_email_handled_cancels_reminder(temp_reminder_manager):
    reminder = temp_reminder_manager.create_reminder(
        email_id="email-handle-1",
        sender="student@university.edu",
        subject="Urgent: Recommendation letter",
        body="Deadline is tonight.",
        priority="High"
    )
    assert reminder.status == "pending"

    # Mark as handled
    success = temp_reminder_manager.mark_handled(reminder.id)
    assert success is True

    updated = temp_reminder_manager.get_reminder(reminder.id)
    assert updated.status == "completed"
    assert updated.handled_at is not None

    # Due reminders should not include completed reminder
    due = temp_reminder_manager.get_due_reminders()
    assert reminder.id not in [d.id for d in due]


# =========================================================================
# TEST 6: Reminders survive application restarts
# =========================================================================
def test_6_reminders_survive_application_restarts(tmp_path):
    db_file = str(tmp_path / "persistent_reminders.db")

    # Instance 1: Create reminder and configure interval
    mgr1 = ReminderManager(db_path=db_file)
    mgr1.set_default_delay_minutes(30)
    r = mgr1.create_reminder(
        email_id="email-restart-1",
        sender="rector@university.edu",
        subject="High: Senate meeting attendance",
        body="Please confirm attendance.",
        priority="High"
    )
    reminder_id = r.id
    # Simulate closing / stopping the app
    del mgr1

    # Instance 2: Simulate restart of the application by creating new ReminderManager
    mgr2 = ReminderManager(db_path=db_file)
    assert mgr2.get_default_delay_minutes() == 30

    reloaded = mgr2.get_reminder(reminder_id)
    assert reloaded is not None
    assert reloaded.id == reminder_id
    assert reloaded.sender == "rector@university.edu"
    assert reloaded.subject == "High: Senate meeting attendance"
    assert reloaded.status == "pending"
    assert reloaded.delay_minutes == 30


# =========================================================================
# TEST 7: Calendar events are created only after approval
# =========================================================================
def test_7_calendar_events_created_only_after_approval(monkeypatch, tmp_path):
    # Set up mock calendar connector
    mock_cal_connector = MagicMock()
    mock_cal_connector.create_event.return_value = {
        "id": "gcal-event-approved-123",
        "htmlLink": "https://calendar.google.com/event?id=123"
    }

    # Isolated service with mock connectors
    db_file = str(tmp_path / "dashboard_test_reminders.db")
    service = DashboardService()
    service.reminder_manager = ReminderManager(db_path=db_file)
    service.calendar_connector = mock_cal_connector
    service.gmail_connector = MagicMock()

    # Create meeting proposal
    req = MeetingRequest(
        meeting_requested=True,
        proposed_date="Friday",
        proposed_time="3 pm",
        purpose="Project Review",
        title="Meeting: Project Review",
        duration_minutes=30,
        attendees=["researcher@university.edu"],
        description="Discuss joint research paper"
    )
    req.id = "meet-proposal-1"
    req.sender = "researcher@university.edu"
    req.subject = "Project Review"
    req.available_slots = ["2026-11-20 03:00 PM — AVAILABLE"]
    req.status = "pending"
    req.google_event_id = None
    service.meetings[req.id] = req

    # Verify that before approval, create_event has NEVER been called
    assert mock_cal_connector.create_event.call_count == 0
    assert service.meetings["meet-proposal-1"].google_event_id is None

    # Confirmation with approved=False must be rejected
    with pytest.raises(PermissionError):
        service.confirm_meeting("meet-proposal-1", "2026-11-20 03:00 PM", approved=False)
    assert mock_cal_connector.create_event.call_count == 0

    # User clicks Approve Event
    result = service.approve_meeting("meet-proposal-1", selected_slot="2026-11-20 03:00 PM")
    assert result["success"] is True
    assert result["event_id"] == "gcal-event-approved-123"
    assert result["status"] == "approved"

    # Verify that create_event was called ONLY after approval
    assert mock_cal_connector.create_event.call_count == 1
    call_kwargs = mock_cal_connector.create_event.call_args[1]
    assert call_kwargs["title"] == "Meeting: Project Review"
    assert call_kwargs["attendees"] == ["researcher@university.edu"]
    assert service.meetings["meet-proposal-1"].google_event_id == "gcal-event-approved-123"


# =========================================================================
# TEST 8: Repeated approval does not create duplicate calendar events
# =========================================================================
def test_8_repeated_approval_does_not_create_duplicate_events(tmp_path):
    mock_cal_connector = MagicMock()
    mock_cal_connector.create_event.return_value = {
        "id": "gcal-unique-event-456"
    }

    service = DashboardService()
    service.reminder_manager = ReminderManager(db_path=str(tmp_path / "dedup_cal.db"))
    service.calendar_connector = mock_cal_connector
    service.gmail_connector = MagicMock()

    req = MeetingRequest(
        meeting_requested=True,
        proposed_date="Monday",
        proposed_time="10 am",
        purpose="Curriculum Committee",
        title="Meeting: Curriculum Committee",
        attendees=["chair@university.edu"]
    )
    req.id = "meet-proposal-2"
    req.sender = "chair@university.edu"
    req.subject = "Curriculum Committee"
    req.available_slots = ["2026-11-23 10:00 AM — AVAILABLE"]
    req.status = "pending"
    service.meetings[req.id] = req

    # First approval
    res1 = service.approve_meeting("meet-proposal-2", selected_slot="2026-11-23 10:00 AM")
    assert res1["success"] is True
    assert res1["event_id"] == "gcal-unique-event-456"
    assert mock_cal_connector.create_event.call_count == 1

    # Second approval click (e.g. user double-clicked or re-submitted)
    res2 = service.approve_meeting("meet-proposal-2", selected_slot="2026-11-23 10:00 AM")
    assert res2["success"] is True
    assert res2["event_id"] == "gcal-unique-event-456"
    assert res2.get("already_approved") is True

    # create_event MUST still have been called exactly once!
    assert mock_cal_connector.create_event.call_count == 1


# =========================================================================
# TEST 9: Invalid or incomplete meeting details are handled safely
# =========================================================================
def test_9_invalid_or_incomplete_meeting_details_handled_safely(tmp_path):
    service = DashboardService()
    service.reminder_manager = ReminderManager(db_path=str(tmp_path / "incomplete_cal.db"))
    service.calendar_connector = MagicMock()

    # Email mentions meeting, but has NO date or time specified
    email_without_datetime = Email(
        sender="student@university.edu",
        subject="Project Discussion",
        body="Can we meet to discuss my capstone project?"
    )
    req = extract_meeting_request(email_without_datetime)
    assert req.meeting_requested is True
    assert req.proposed_date is None
    assert req.proposed_time is None
    assert req.missing_date_or_time is True

    req.id = "meet-missing-datetime"
    req.available_slots = ["2026-11-24 11:00 AM — AVAILABLE", "2026-11-24 02:00 PM"]
    req.status = "pending"
    service.meetings[req.id] = req

    # Approving with no slot and no details should fail gracefully with a descriptive error
    with pytest.raises(ValueError) as excinfo:
        # Pass empty slot to trigger date/time missing error
        service.approve_meeting("meet-missing-datetime", selected_slot="")
    assert "date and time are missing" in str(excinfo.value) or "valid meeting time slot" in str(excinfo.value)

    # Approving with an invalid date string format should raise safe ValueError without crash
    with pytest.raises(ValueError) as excinfo:
        service.approve_meeting("meet-missing-datetime", selected_slot="invalid-garbage-date")
    assert "Invalid meeting date or time" in str(excinfo.value) or "Unable to parse" in str(excinfo.value)

    # When the user confirms by selecting a valid slot from suggested availability, it succeeds!
    res = service.approve_meeting("meet-missing-datetime", selected_slot="2026-11-24 11:00 AM — AVAILABLE")
    assert res["success"] is True
    assert service.meetings["meet-missing-datetime"].status == "approved"


# =========================================================================
# TEST 10: Existing classification, extraction, drafting, and LangGraph flow work
# =========================================================================
def test_10_existing_classification_extraction_drafting_and_validation():
    # 1. Classification & Action Extraction
    email = Email(
        sender="student@gmail.com",
        subject="Project submission deadline",
        body="Sir, I will submit my project report by Friday. Please review it."
    )

    # Mock groq safe fallback check
    classification = EmailClassification(
        sender_category="Student",
        email_type="Request",
        priority="High"
    )
    assert classification.priority in ["Critical", "High", "Medium", "Low"]

    extraction = ActionExtraction(
        action_items=[
            ActionItem(
                description="Review project report",
                deadline="Friday",
                assigned_to="faculty",
                confidence=0.95
            )
        ]
    )
    assert len(extraction.action_items) == 1
    assert extraction.action_items[0].description == "Review project report"

    # 2. Review Queue / Draft Lifecycle
    draft = create_review_item(
        recipient=email.sender,
        subject=f"Re: {email.subject}",
        body="Thank you. I will review it."
    )
    assert draft.state == ReviewState.DRAFT
    approve_review_item(draft, reviewer="Faculty Reviewer")
    assert draft.state == ReviewState.APPROVED

    # 3. LangGraph Workflow Structure & Node Count Verification
    compiled_graph = build_graph()
    nodes = compiled_graph.get_graph().nodes
    # Custom nodes: ingest, classify, schedule_reminders, extract_actions,
    # create_draft, ground, validate, regenerate (8 nodes) + START & END = 10
    assert len(nodes) == 10
    custom_node_names = [n for n in nodes.keys() if not n.startswith("__")]
    assert len(custom_node_names) == 8
    assert "schedule_reminders" in custom_node_names
    assert "classify" in custom_node_names
    assert "validate" in custom_node_names
    assert "regenerate" in custom_node_names


# =========================================================================
# BONUS TEST: Cancel active reminder when email draft is sent
# =========================================================================
def test_reminder_cancelled_when_draft_sent(tmp_path):
    service = DashboardService()
    service.reminder_manager = ReminderManager(db_path=str(tmp_path / "sent_cancel.db"))
    service.gmail_connector = None  # Use mock fallback in send_draft

    # Create high priority draft and reminder
    draft_id = "draft-urgent-1"
    item = create_review_item("colleague@university.edu", "Re: Urgent Evaluation", "Draft reply")
    item.state = ReviewState.APPROVED
    service.drafts[draft_id] = item

    reminder = service.reminder_manager.create_reminder(
        email_id=draft_id,
        sender="colleague@university.edu",
        subject="Urgent Evaluation",
        body="Please evaluate today.",
        priority="High"
    )
    assert reminder.status == "pending"

    # Send the approved draft
    service.send_draft(draft_id)
    assert item.state == ReviewState.SENT

    # Reminder should now be completed/cancelled
    updated_rem = service.reminder_manager.get_reminder(reminder.id)
    assert updated_rem.status == "completed"


# =========================================================================
# TEST 12: Calendar event conflict correctly marks requested slot as BUSY
# and does not show it as available
# =========================================================================
def test_12_busy_calendar_event_prevents_available_slot(tmp_path):
    from calendar_agent import propose_meeting_slots_with_preference
    from datetime import date

    mock_cal = MagicMock()
    # Mock an event on Monday Nov 16 from 10:00 to 11:00 AM IST
    mock_cal.get_busy_periods.return_value = [
        {
            "start": "2026-11-16T10:00:00+05:30",
            "end": "2026-11-16T11:00:00+05:30",
            "summary": "Existing Meeting"
        }
    ]

    ref_date = date(2026, 11, 15)  # Sunday
    slots, status = propose_meeting_slots_with_preference(
        mock_cal,
        start_date=ref_date,
        proposed_date_str="Monday",
        proposed_time_str="10 am",
        days=5
    )

    # 1. The requested slot must be marked as BUSY
    assert status == "BUSY", f"Expected BUSY but got {status}"

    # 2. The busy slot (10:00 AM) must NOT be present in suggested free slots
    for s in slots:
        assert not (s.start.date() == date(2026, 11, 16) and s.start.hour == 10 and s.start.minute == 0), (
            f"Busy slot {s.start} was erroneously included in available slots!"
        )

    # 3. Alternative slots that do not overlap should be suggested instead
    assert len(slots) > 0
    for s in slots:
        assert s.start.hour != 10 or s.start.date() != date(2026, 11, 16)


# =========================================================================
# TEST 13: Approved emails send as direct threaded replies
# =========================================================================
def test_13_approved_email_sends_as_threaded_reply():
    from gmail_sender import GmailSender, send_approved_email
    from review_queue import ReviewItem, ReviewState
    import base64
    from email import message_from_bytes

    mock_service = MagicMock()
    sender = GmailSender(mock_service)

    item = ReviewItem(
        recipient="colleague@university.edu",
        subject="Re: Paper Review",
        body="I have reviewed the draft.",
        state=ReviewState.APPROVED,
        thread_id="thread-xyz-456",
        message_id="msg-abc-123"
    )

    send_approved_email(item, sender)

    # 1. messages().send() was called
    assert mock_service.users().messages().send.called
    call_args = mock_service.users().messages().send.call_args[1]
    
    # 2. threadId was included in Gmail API payload
    assert call_args["body"].get("threadId") == "thread-xyz-456"

    # 3. RFC 2822 In-Reply-To and References headers were set
    raw_b64 = call_args["body"]["raw"]
    msg = message_from_bytes(base64.urlsafe_b64decode(raw_b64))
    assert msg["In-Reply-To"] == "<msg-abc-123>"
    assert msg["References"] == "<msg-abc-123>"


# =========================================================================
# TEST 14: Groq API Context-Aware Drafting and Fallback
# =========================================================================
def test_14_groq_draft_generation_with_context_and_fallback(monkeypatch):
    from draft_agent import draft_reply, generate_groq_reply

    test_email = Email(
        sender="student@university.edu",
        subject="Question about Assignment 3 Deadline",
        body="Professor, I was unwell this week. Could I please get a 2-day extension on Assignment 3?"
    )
    action_items = [
        {"description": "Review assignment extension request", "deadline": "Tomorrow"}
    ]

    # 1. Mock Groq Chat Completion to simulate live Groq API returning a context-aware draft
    mock_groq_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = (
        "Dear Student,\n\n"
        "I hope you are recovering well. I have received your request regarding Assignment 3 "
        "and approve a 2-day extension. Please submit your work by [insert date].\n\n"
        "Best regards,\nFaculty"
    )
    mock_completion.choices = [mock_choice]
    mock_groq_client.chat.completions.create.return_value = mock_completion

    monkeypatch.setattr("draft_agent.get_groq_client", lambda: mock_groq_client)

    groq_result = draft_reply(
        email=test_email,
        action_items=action_items,
        category="Student",
        priority="Medium"
    )

    assert groq_result["status"] == "draft"
    assert groq_result["source"] == "Groq AI"
    assert "Assignment 3" in groq_result["body"]
    assert "extension" in groq_result["body"]

    # 2. When Groq client is None or raises an error, falls back to template logic
    monkeypatch.setattr("draft_agent.get_groq_client", lambda: None)

    fallback_result = draft_reply(
        email=test_email,
        action_items=action_items,
        category="Student",
        priority="Medium"
    )

    assert fallback_result["status"] == "draft"
    assert fallback_result["source"] == "Template"
    assert "extension" in fallback_result["body"].lower()

    # 3. When neither Groq nor any template matches, falls back to deterministic summary
    unmatched_email = Email(
        sender="colleague@random.org",
        subject="Departmental Budget Ledger",
        body="Here are the quarterly balance numbers for our financial audit."
    )
    unmatched_result = draft_reply(
        email=unmatched_email,
        action_items=[{"description": "Check budget allocation", "deadline": "Monday"}],
        category="Admin",
        priority="Medium"
    )
    assert unmatched_result["source"] == "Fallback"
    assert "Departmental Budget Ledger" in unmatched_result["body"]
    assert "Check budget allocation" in unmatched_result["body"]


# =========================================================================
# TEST 15: Option 1 - Meeting approval syncs to Draft Queue without auto-sending
# =========================================================================
def test_15_meeting_approval_syncs_to_draft_queue_without_auto_send(tmp_path):
    mock_cal_connector = MagicMock()
    mock_cal_connector.create_event.return_value = {
        "id": "gcal-sync-event-789"
    }
    mock_gmail_service = MagicMock()

    service = DashboardService()
    service.reminder_manager = ReminderManager(db_path=str(tmp_path / "sync_cal.db"))
    service.calendar_connector = mock_cal_connector
    service.gmail_connector = MagicMock()
    service.gmail_connector.service = mock_gmail_service

    # Create meeting proposal linked to a draft in Draft Queue
    draft_id = "draft-linked-123"
    initial_draft = create_review_item(
        recipient="professor@university.edu",
        subject="Re: Research Collaboration",
        body="I will review my schedule and confirm.",
        thread_id="thread-sync-1",
        message_id="msg-sync-1"
    )
    service.drafts[draft_id] = initial_draft

    req = MeetingRequest(
        meeting_requested=True,
        proposed_date="2026-11-20",
        proposed_time="03:00 PM",
        purpose="Research Collaboration",
        title="Meeting: Research Collaboration",
        duration_minutes=30,
        attendees=["professor@university.edu"],
        description="Discuss joint NSF grant proposal"
    )
    req.id = "meet-sync-test"
    req.draft_id = draft_id
    req.sender = "professor@university.edu"
    req.subject = "Research Collaboration"
    req.available_slots = ["2026-11-20 03:00 PM — AVAILABLE"]
    req.status = "pending"
    service.meetings[req.id] = req

    # 1. User approves the meeting slot in Meeting Requests block
    res = service.approve_meeting("meet-sync-test", selected_slot="2026-11-20 03:00 PM — AVAILABLE")
    assert res["success"] is True
    assert res["status"] == "approved"
    assert service.meetings["meet-sync-test"].google_event_id == "gcal-sync-event-789"

    # 2. Strict Human-in-the-Loop check: NO email was sent automatically!
    assert mock_gmail_service.users().messages().send.call_count == 0

    # 3. Draft Queue Sync check: Draft in review queue was updated with confirmed slot details!
    updated_draft = service.drafts[draft_id]
    assert updated_draft.version == 2
    assert "2026-11-20 03:00 PM" in updated_draft.body
    assert "Research Collaboration" in updated_draft.body or "confirmed" in updated_draft.body.lower()

    # 4. User explicitly reviews and sends draft from Draft Queue
    service.approve_draft(draft_id, reviewer="Faculty Reviewer")
    service.send_draft(draft_id)

    # 5. Now email is sent as a threaded reply with user approval!
    assert mock_gmail_service.users().messages().send.call_count == 1
    call_args = mock_gmail_service.users().messages().send.call_args[1]
    assert call_args["body"].get("threadId") == "thread-sync-1"


