import base64
from email.mime.text import MIMEText


class GmailSender:

    def __init__(self, gmail_service):
        self.service = gmail_service

    def send(
        self,
        recipient,
        subject,
        body,
        thread_id=None,
        message_id=None
    ):

        message = MIMEText(body)

        message["to"] = recipient
        message["subject"] = subject

        # Threading headers for RFC 2822 threaded reply
        if message_id:
            clean_msg_id = message_id.strip()
            if not clean_msg_id.startswith("<"):
                clean_msg_id = f"<{clean_msg_id}>"
            message["In-Reply-To"] = clean_msg_id
            message["References"] = clean_msg_id

        encoded_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        body_payload = {
            "raw": encoded_message
        }
        if thread_id:
            body_payload["threadId"] = thread_id

        result = (
            self.service
            .users()
            .messages()
            .send(
                userId="me",
                body=body_payload
            )
            .execute()
        )

        return result
    
from review_queue import (
    ReviewState,
    mark_as_sent
)


def send_approved_email(
    review_item,
    gmail_sender
):

    if review_item.state != ReviewState.APPROVED:
        raise PermissionError(
            "Email cannot be sent without faculty approval."
        )

    # Threading support: reply inside the same email conversation
    thread_id = getattr(review_item, "thread_id", None)
    message_id = getattr(review_item, "message_id", None)

    try:
        result = gmail_sender.send(
            recipient=review_item.recipient,
            subject=review_item.subject,
            body=review_item.body,
            thread_id=thread_id,
            message_id=message_id
        )
    except TypeError:
        # Fallback for mock senders that only accept (recipient, subject, body)
        result = gmail_sender.send(
            recipient=review_item.recipient,
            subject=review_item.subject,
            body=review_item.body
        )

    mark_as_sent(review_item)

    return result