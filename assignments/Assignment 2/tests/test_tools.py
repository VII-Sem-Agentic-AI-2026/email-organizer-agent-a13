import unittest
from tool_layer import EmailTools
from agent import ToolUsingEmailAgent

class ToolTests(unittest.TestCase):
    def setUp(self):
        self.tools = EmailTools()

    def test_inbox_returns_typed_emails(self):
        emails = self.tools.read_inbox()
        self.assertGreater(len(emails), 0)
        self.assertTrue(all(hasattr(e, "message_id") for e in emails))

    def test_thread_lookup(self):
        thread = self.tools.read_thread("T001")
        self.assertEqual(len(thread), 1)
        self.assertEqual(thread[0].message_id, "M001")

    def test_contact_lookup_includes_previous_replies(self):
        contact = self.tools.lookup_contact("student@example.com")
        self.assertEqual(contact.category, "Student")
        self.assertGreater(len(contact.previous_replies), 0)

    def test_calculator_flags_admin_as_high(self):
        email = self.tools.read_inbox()[1]
        result = self.tools.compute_and_check(email)
        self.assertEqual(result.priority, "High")
        self.assertTrue(result.sender_known)
        self.assertTrue(result.valid)

    def test_agent_calls_tools_and_returns_all_emails(self):
        result = ToolUsingEmailAgent(self.tools).run()
        self.assertEqual(len(result), len(self.tools.read_inbox()))
        self.assertIn("verification", result[0])

    def test_invalid_deadline_is_not_calculated(self):
        email = self.tools.read_inbox()[0]
        result = self.tools.compute_and_check(email, "26-11-2026")
        self.assertIsNone(result.deadline_days)
        self.assertTrue(any("invalid" in reason.lower() for reason in result.reasons))

if __name__ == "__main__":
    unittest.main()
