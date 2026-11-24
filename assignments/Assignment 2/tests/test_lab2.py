from tool_layer import EmailTools, Email
from agent import EmailOrganizerAgent


def test_read_inbox():
    result = EmailTools().read_inbox()
    assert result.success
    assert len(result.data) >= 1


def test_read_thread():
    result = EmailTools().read_thread("T001")
    assert result.success
    assert len(result.data) >= 1


def test_invalid_thread():
    result = EmailTools().read_thread("UNKNOWN")
    assert not result.success


def test_read_contacts():
    result = EmailTools().read_contacts()
    assert result.success
    assert any(c.email == "student@college.edu" for c in result.data)


def test_read_prior_replies():
    result = EmailTools().read_prior_replies("student@college.edu")
    assert result.success
    assert len(result.data) >= 1


def test_email_validation():
    email = Email(
        "E100", "test@college.edu", "Test",
        "Test message", "T100", "2026-11-24"
    )
    assert EmailTools().validate_email(email).success


def test_invalid_email_validation():
    email = Email("", "invalid", "", "", "", "")
    assert not EmailTools().validate_email(email).success


def test_date_calculator():
    result = EmailTools().calculate_days_until("2026-11-28")
    assert result.success
    assert isinstance(result.data, int)


def test_agent_uses_tools():
    agent = EmailOrganizerAgent()
    results = agent.run()
    assert len(results) == 3
    assert "mock_inbox" in agent.evidence
    assert "mock_threads" in agent.evidence
    assert "mock_contacts" in agent.evidence


def test_agent_uses_prior_replies():
    results = EmailOrganizerAgent().run()
    student = next(x for x in results if x["email_id"] == "E001")
    assert len(student["prior_replies"]) >= 1
