import unittest
from agent import EmailDataAgent
from connector import EmailDataConnector, AuthenticationError
from data_source import MockDataSource, AlternateMockDataSource
from models import ConnectorRequest

TOKEN = "test-token"

class ConnectorTests(unittest.TestCase):
    def setUp(self):
        self.backend = MockDataSource()
        self.connector = EmailDataConnector(self.backend, TOKEN)

    def test_reads_all_three_exposed_sources(self):
        agent = EmailDataAgent(self.connector, TOKEN)
        result = agent.collect_email_context()
        self.assertIn("inbox_threads", result)
        self.assertIn("contacts_replies", result)
        self.assertIn("calendar_tasks", result)
        self.assertTrue(result["inbox_threads"])

    def test_invalid_token_is_rejected(self):
        request = ConnectorRequest("inbox_threads", "read", "wrong")
        with self.assertRaises(AuthenticationError):
            self.connector.read(request)

    def test_unknown_source_is_rejected(self):
        request = ConnectorRequest("private_database", "read", TOKEN)
        with self.assertRaises(KeyError):
            self.connector.read(request)

    def test_unsupported_operation_is_rejected(self):
        request = ConnectorRequest("inbox_threads", "delete", TOKEN)
        with self.assertRaises(ValueError):
            self.connector.read(request)

    def test_agent_works_after_backend_swap(self):
        first = EmailDataAgent(self.connector, TOKEN)
        first_result = first.collect_email_context()

        swapped = EmailDataConnector(AlternateMockDataSource(), TOKEN)
        second = EmailDataAgent(swapped, TOKEN)
        second_result = second.collect_email_context()

        self.assertEqual(first_result["inbox_threads"][0]["id"], "E101")
        self.assertEqual(second_result["inbox_threads"][0]["id"], "E201")
        self.assertEqual(second_result["contacts_replies"][0]["email"],
                         first_result["contacts_replies"][0]["email"])

    def test_returned_records_do_not_mutate_backend(self):
        response = self.connector.read_source("inbox_threads", TOKEN)
        response.records[0]["subject"] = "Changed"
        again = self.connector.read_source("inbox_threads", TOKEN)
        self.assertEqual(again.records[0]["subject"], "Project submission extension")

if __name__ == "__main__":
    unittest.main()
