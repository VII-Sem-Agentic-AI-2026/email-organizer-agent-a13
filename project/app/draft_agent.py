import os
import re
from dotenv import load_dotenv, find_dotenv
from response_library import find_standard_response

# Find .env from this file's directory upward
_dotenv_path = find_dotenv(usecwd=False)
load_dotenv(dotenv_path=_dotenv_path)

_groq_client = None

def get_groq_client():
    global _groq_client
    if _groq_client is not None:
        return _groq_client
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        from groq import Groq
        _groq_client = Groq(api_key=api_key)
        return _groq_client
    except Exception as e:
        print(f"Failed to initialize Groq client for draft generation: {e}")
        return None


MODEL_NAME = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


def generate_groq_reply(
    email,
    action_items=None,
    category=None,
    priority=None,
    evidence=None
) -> str | None:
    """
    Uses the Groq API to analyze the full email context and draft a tailored,
    context-aware professional reply on behalf of a university faculty member.
    """
    client = get_groq_client()
    if not client:
        return None

    # Format action items if available
    actions_desc = "None"
    if action_items:
        formatted_items = []
        for item in action_items:
            desc = item.get("description") if isinstance(item, dict) else getattr(item, "description", str(item))
            deadline = item.get("deadline") if isinstance(item, dict) else getattr(item, "deadline", None)
            if deadline:
                formatted_items.append(f"- {desc} (Deadline: {deadline})")
            else:
                formatted_items.append(f"- {desc}")
        if formatted_items:
            actions_desc = "\n".join(formatted_items)

    # Format evidence if available
    evidence_desc = ""
    if evidence:
        ev_lines = []
        for ev in evidence:
            content = ev.get("content") if isinstance(ev, dict) else getattr(ev, "content", str(ev))
            ev_lines.append(f"- {content}")
        if ev_lines:
            evidence_desc = f"\nRelevant Thread History / Grounding Evidence:\n" + "\n".join(ev_lines)

    sender = getattr(email, "sender", "Unknown")
    subject = getattr(email, "subject", "No Subject")
    body = getattr(email, "body", "")

    prompt = f"""You are an email assistant for a university faculty member.
Analyze the email context below and draft a professional, courteous, and specific reply.

Incoming Email:
From: {sender}
Category: {category or 'General'}
Priority: {priority or 'Normal'}
Subject: {subject}

Email Body:
\"\"\"{body}\"\"\"

Detected Action Items & Deadlines:
{actions_desc}
{evidence_desc}

Drafting Guidelines:
1. Address the sender respectfully (e.g. "Dear [Sender Name]," or "Hello [Sender Name],").
2. Directly answer questions, acknowledge action items, and address concerns raised in the email.
3. Keep the tone warm, academic, and professional.
4. If faculty-specific details are required that you cannot know (e.g. specific dates or attachments), use clean placeholders like [insert date] or [attached file].
5. Sign off respectfully as the Faculty Member (e.g. "Best regards,\nFaculty").
6. Output ONLY the email body text. Do NOT include a subject line, do NOT wrap the entire text in quotes or code blocks, and do NOT include preamble like "Here is your draft:".
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional email drafting assistant for university faculty. You output only the reply text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=800
        )
        content = response.choices[0].message.content
        if content:
            cleaned = content.strip()
            # Remove markdown code block wrappers if model outputs them
            if cleaned.startswith("```") and cleaned.endswith("```"):
                lines = cleaned.splitlines()
                if len(lines) >= 2:
                    cleaned = "\n".join(lines[1:-1]).strip()
            return cleaned
        return None
    except Exception as e:
        print(f"Groq draft generation failed or unavailable: {e}")
        return None


def draft_reply(
    email,
    action_items=None,
    category=None,
    priority=None,
    evidence=None,
    prefer_groq=True
):
    """
    Drafts an email reply.
    When prefer_groq is True (default), analyzes the full email context with Groq API.
    Gracefully falls back to standard templates or heuristic summaries if Groq is unavailable.
    """
    subject = getattr(email, "subject", "")
    body_text = getattr(email, "body", "")

    # 1. Try Groq AI context-aware drafting if enabled
    if prefer_groq:
        ai_draft = generate_groq_reply(
            email=email,
            action_items=action_items,
            category=category,
            priority=priority,
            evidence=evidence
        )
        if ai_draft:
            return {
                "status": "draft",
                "template": "Groq AI (Context-Aware)",
                "source": "Groq AI",
                "subject": f"Re: {subject}",
                "body": ai_draft
            }

    # 2. Check standard response template library
    match = find_standard_response(subject, body_text)
    if match:
        return {
            "status": "draft",
            "template": match["title"],
            "source": "Template",
            "subject": f"Re: {subject}",
            "body": match["response"]
        }

    # 3. Fallback deterministic drafting using action items and subject context
    if action_items:
        items = []
        for a in action_items:
            desc = a.get("description") if isinstance(a, dict) else getattr(a, "description", str(a))
            items.append(desc)
        items_str = ", ".join(items)
        fallback_body = (
            f"Dear Sender,\n\n"
            f"Thank you for your email regarding '{subject}'.\n"
            f"I have noted the following action items: {items_str}.\n"
            f"I will review this and follow up with you shortly.\n\n"
            f"Best regards,\nFaculty"
        )
    else:
        fallback_body = (
            f"Dear Sender,\n\n"
            f"Thank you for reaching out regarding '{subject}'.\n"
            f"I have received your email and will get back to you shortly.\n\n"
            f"Best regards,\nFaculty"
        )

    return {
        "status": "draft",
        "template": "Standard Fallback",
        "source": "Fallback",
        "subject": f"Re: {subject}",
        "body": fallback_body
    }


def draft_meeting_reply(
    sender: str,
    subject: str,
    confirmed_slot: str = None,
    duration_minutes: int = 30,
    is_rejection: bool = False,
    description: str = "",
    prefer_groq: bool = True
) -> dict:
    """
    Drafts an email reply for meeting approvals or rejections.
    Uses Groq AI if available to formulate a polite, context-aware reply,
    with deterministic template fallback.
    """
    sender_clean = sender.split("<")[0].strip().replace('"', '') if sender else "Colleague"
    if not sender_clean or "@" in sender_clean:
        sender_clean = sender.split("@")[0].capitalize() if "@" in sender else "Colleague"

    if prefer_groq:
        client = get_groq_client()
        if client:
            status_text = (
                f"Approved and confirmed for: {confirmed_slot} (Duration: {duration_minutes} minutes)"
                if not is_rejection
                else "Declined due to scheduling constraints"
            )
            prompt = f"""You are an email assistant for a university faculty member.
Draft a courteous, concise email reply to {sender} regarding the meeting request.

Meeting Details:
Subject: {subject}
Status: {status_text}
Meeting Notes: {description or 'None'}

Guidelines:
1. Address the recipient respectfully (e.g. "Dear {sender_clean},").
2. Clearly state that the meeting has been confirmed on Google Calendar for {confirmed_slot} (or politely declined if declined).
3. If confirmed, invite them to share any discussion topics or agenda items beforehand.
4. Sign off respectfully as the Faculty Member.
5. Output ONLY the email body text.
"""
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional email drafting assistant for university faculty. You output only the reply text."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.2,
                    max_tokens=600
                )
                content = response.choices[0].message.content
                if content:
                    cleaned = content.strip()
                    if cleaned.startswith("```") and cleaned.endswith("```"):
                        lines = cleaned.splitlines()
                        if len(lines) >= 2:
                            cleaned = "\n".join(lines[1:-1]).strip()
                    return {
                        "status": "draft",
                        "template": "Groq AI (Meeting Confirmed)" if not is_rejection else "Groq AI (Meeting Declined)",
                        "source": "Groq AI",
                        "body": cleaned
                    }
            except Exception as e:
                print(f"Groq meeting reply generation unavailable: {e}")

    # Fallback template
    if not is_rejection:
        body = (
            f"Dear {sender_clean},\n\n"
            f"Thank you for reaching out. I have reviewed your meeting request regarding '{subject}' "
            f"and confirmed it on my Google Calendar:\n\n"
            f"📅 Confirmed Time: {confirmed_slot}\n"
            f"⏱️ Duration: {duration_minutes} minutes\n\n"
            f"I look forward to our discussion. Please let me know if you would like to share any agenda items or materials beforehand.\n\n"
            f"Best regards,\nFaculty"
        )
        source = "Meeting Confirmed"
    else:
        body = (
            f"Dear {sender_clean},\n\n"
            f"Thank you for reaching out regarding '{subject}'.\n\n"
            f"Unfortunately, I am unable to accommodate this meeting request at this time due to scheduling conflicts. "
            f"Please feel free to follow up at a later date.\n\n"
            f"Best regards,\nFaculty"
        )
        source = "Meeting Declined"

    return {
        "status": "draft",
        "template": source,
        "source": source,
        "body": body
    }

