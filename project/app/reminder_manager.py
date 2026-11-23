import os
import sqlite3
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import threading
import time
from zoneinfo import ZoneInfo

from calendar_agent import LOCAL_TZ
from audit import log_action

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "reminders.db"
)


@dataclass
class Reminder:
    id: str
    email_id: str
    sender: str
    subject: str
    body: str
    priority: str
    draft_id: str | None
    status: str  # 'pending', 'snoozed', 'completed', 'cancelled'
    delay_minutes: int
    created_at: str
    remind_at: str
    snooze_count: int = 0
    last_snoozed_at: str | None = None
    handled_at: str | None = None

    @property
    def is_due(self) -> bool:
        if self.status not in ("pending", "snoozed"):
            return False
        try:
            remind_dt = datetime.fromisoformat(self.remind_at)
            if remind_dt.tzinfo is None:
                remind_dt = remind_dt.replace(tzinfo=LOCAL_TZ)
            return datetime.now(LOCAL_TZ) >= remind_dt
        except Exception:
            return False

    def to_dict(self) -> dict:
        d = asdict(self)
        d["is_due"] = self.is_due
        return d


class ReminderManager:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id TEXT PRIMARY KEY,
                    email_id TEXT,
                    sender TEXT,
                    subject TEXT,
                    body TEXT,
                    priority TEXT,
                    draft_id TEXT,
                    status TEXT,
                    delay_minutes INTEGER,
                    created_at TEXT,
                    remind_at TEXT,
                    snooze_count INTEGER DEFAULT 0,
                    last_snoozed_at TEXT,
                    handled_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reminder_config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            # Set default delay to 15 minutes if not configured
            cursor = conn.execute(
                "SELECT value FROM reminder_config WHERE key = 'default_delay_minutes'"
            )
            if not cursor.fetchone():
                conn.execute(
                    "INSERT INTO reminder_config (key, value) VALUES ('default_delay_minutes', '15')"
                )
            conn.commit()

    def get_default_delay_minutes(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT value FROM reminder_config WHERE key = 'default_delay_minutes'"
            )
            row = cursor.fetchone()
            if row:
                try:
                    return int(row["value"])
                except ValueError:
                    return 15
        return 15

    def set_default_delay_minutes(self, minutes: int):
        if minutes <= 0:
            raise ValueError("Delay minutes must be positive.")
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO reminder_config (key, value) VALUES ('default_delay_minutes', ?)",
                (str(minutes),)
            )
            conn.commit()

    def create_reminder(
        self,
        email_id: str,
        sender: str,
        subject: str,
        body: str,
        priority: str,
        draft_id: str | None = None,
        delay_minutes: int | None = None
    ) -> Reminder | None:
        """
        Creates a persistent reminder for High or Critical priority emails.
        Avoids creating multiple active reminders for the same email.
        """
        priority_norm = (priority or "").capitalize()
        if priority_norm not in ("Critical", "High"):
            # Only high-priority and critical emails trigger reminders
            return None

        # Check if an active reminder already exists for this email
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM reminders
                WHERE (email_id = ? OR (sender = ? AND subject = ?))
                  AND status IN ('pending', 'snoozed')
                """,
                (email_id, sender, subject)
            )
            existing = cursor.fetchone()
            if existing:
                return self._row_to_reminder(existing)

            if delay_minutes is None:
                delay_minutes = self.get_default_delay_minutes()

            now = datetime.now(LOCAL_TZ)
            remind_at = now + timedelta(minutes=delay_minutes)
            reminder_id = str(uuid.uuid4())

            conn.execute(
                """
                INSERT INTO reminders (
                    id, email_id, sender, subject, body, priority,
                    draft_id, status, delay_minutes, created_at,
                    remind_at, snooze_count, last_snoozed_at, handled_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NULL, NULL)
                """,
                (
                    reminder_id,
                    email_id,
                    sender,
                    subject,
                    body,
                    priority_norm,
                    draft_id,
                    "pending",
                    delay_minutes,
                    now.isoformat(),
                    remind_at.isoformat()
                )
            )
            conn.commit()

        log_action(
            action="create_reminder",
            actor="System",
            recipient=sender,
            subject=f"Reminder scheduled: {subject} in {delay_minutes} mins"
        )

        return self.get_reminder(reminder_id)

    def snooze_reminder(self, reminder_id: str, delay_minutes: int) -> Reminder:
        """
        Snoozes an existing reminder by rescheduling it.
        Does not create duplicate reminders.
        """
        if delay_minutes <= 0:
            raise ValueError("Snooze duration must be greater than 0 minutes.")

        reminder = self.get_reminder(reminder_id)
        if not reminder:
            raise ValueError(f"Reminder {reminder_id} not found.")

        if reminder.status in ("completed", "cancelled"):
            raise ValueError(f"Cannot snooze a {reminder.status} reminder.")

        now = datetime.now(LOCAL_TZ)
        new_remind_at = now + timedelta(minutes=delay_minutes)
        new_snooze_count = reminder.snooze_count + 1

        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE reminders
                SET status = 'snoozed',
                    remind_at = ?,
                    delay_minutes = ?,
                    snooze_count = ?,
                    last_snoozed_at = ?
                WHERE id = ?
                """,
                (
                    new_remind_at.isoformat(),
                    delay_minutes,
                    new_snooze_count,
                    now.isoformat(),
                    reminder_id
                )
            )
            conn.commit()

        log_action(
            action="snooze_reminder",
            actor="User",
            recipient=reminder.sender,
            subject=f"Snoozed: {reminder.subject} for {delay_minutes} mins"
        )

        return self.get_reminder(reminder_id)

    def mark_handled(self, reminder_id_or_email_id: str) -> bool:
        """
        Dismisses/completes the reminder.
        """
        now = datetime.now(LOCAL_TZ).isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE reminders
                SET status = 'completed',
                    handled_at = ?
                WHERE (id = ? OR email_id = ?)
                  AND status IN ('pending', 'snoozed')
                """,
                (now, reminder_id_or_email_id, reminder_id_or_email_id)
            )
            updated_count = cursor.rowcount
            conn.commit()

        if updated_count > 0:
            log_action(
                action="complete_reminder",
                actor="User",
                recipient=None,
                subject=f"Reminder marked as handled ({reminder_id_or_email_id})"
            )
            return True
        return False

    def cancel_pending_for_email(
        self,
        email_id: str | None = None,
        subject: str | None = None,
        sender: str | None = None
    ) -> int:
        """
        Cancels active reminders when email is replied to or handled.
        """
        now = datetime.now(LOCAL_TZ).isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE reminders
                SET status = 'completed',
                    handled_at = ?
                WHERE (
                    (? IS NOT NULL AND email_id = ?)
                    OR (? IS NOT NULL AND ? IS NOT NULL AND subject = ? AND sender = ?)
                ) AND status IN ('pending', 'snoozed')
                """,
                (now, email_id, email_id, subject, sender, subject, sender)
            )
            count = cursor.rowcount
            conn.commit()
        return count

    def get_reminder(self, reminder_id: str) -> Reminder | None:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM reminders WHERE id = ?",
                (reminder_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_reminder(row)
        return None

    def get_due_reminders(self) -> list[Reminder]:
        """
        Returns all reminders that are due right now.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM reminders
                WHERE status IN ('pending', 'snoozed')
                ORDER BY remind_at ASC
                """
            )
            reminders = [self._row_to_reminder(row) for row in cursor.fetchall()]

        return [r for r in reminders if r.is_due]

    def get_all_reminders(self) -> list[dict]:
        """
        Returns all reminders formatted as dictionaries.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM reminders
                ORDER BY created_at DESC
                """
            )
            rows = cursor.fetchall()

        return [self._row_to_reminder(r).to_dict() for r in rows]

    def _row_to_reminder(self, row: sqlite3.Row) -> Reminder:
        return Reminder(
            id=row["id"],
            email_id=row["email_id"],
            sender=row["sender"],
            subject=row["subject"],
            body=row["body"],
            priority=row["priority"],
            draft_id=row["draft_id"],
            status=row["status"],
            delay_minutes=row["delay_minutes"],
            created_at=row["created_at"],
            remind_at=row["remind_at"],
            snooze_count=row["snooze_count"],
            last_snoozed_at=row["last_snoozed_at"],
            handled_at=row["handled_at"]
        )


class ReminderScheduler:
    """
    Background scheduler for evaluating persistent reminders.
    Periodically checks for due reminders and notifies listeners.
    """
    def __init__(self, reminder_manager: ReminderManager, check_interval_seconds: int = 5):
        self.reminder_manager = reminder_manager
        self.check_interval_seconds = check_interval_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._callbacks = []

    def register_callback(self, callback):
        self._callbacks.append(callback)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                due_reminders = self.reminder_manager.get_due_reminders()
                if due_reminders:
                    for cb in self._callbacks:
                        try:
                            cb(due_reminders)
                        except Exception as e:
                            print(f"Error in reminder scheduler callback: {e}")
            except Exception as e:
                print(f"Error checking due reminders: {e}")

            self._stop_event.wait(self.check_interval_seconds)
