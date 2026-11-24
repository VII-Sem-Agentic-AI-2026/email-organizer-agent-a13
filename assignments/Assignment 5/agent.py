from connector import EmailDataConnector
from models import ConnectorRequest

class EmailDataAgent:
    """
    Data-facing agent. It receives only the connector, not the backend.
    Changing MockDataSource to another DataSource does not change this class.
    """
    def __init__(self, connector: EmailDataConnector, token: str):
        self._connector = connector
        self._token = token

    def collect_email_context(self) -> dict:
        inbox = self._connector.read(
            ConnectorRequest("inbox_threads", "read", self._token)
        )
        contacts = self._connector.read(
            ConnectorRequest("contacts_replies", "read", self._token)
        )
        calendar = self._connector.read(
            ConnectorRequest("calendar_tasks", "read", self._token)
        )
        return {
            "inbox_threads": inbox.records,
            "contacts_replies": contacts.records,
            "calendar_tasks": calendar.records,
        }
