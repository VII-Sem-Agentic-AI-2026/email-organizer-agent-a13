from data_source import DataSource
from models import ConnectorRequest, ConnectorResponse

class AuthenticationError(PermissionError):
    pass

class EmailDataConnector:
    ALLOWED_SOURCES = {
        "inbox_threads",
        "contacts_replies",
        "calendar_tasks",
    }

    def __init__(self, backend: DataSource, access_token: str):
        if not access_token:
            raise ValueError("An access token is required.")
        self._backend = backend
        self._access_token = access_token

    def read(self, request: ConnectorRequest) -> ConnectorResponse:
        print(f"\n[CONNECTOR] Request received: source={request.source}, operation={request.operation}")

        if request.token != self._access_token:
            print("[AUTH] Authentication failed.")
            raise AuthenticationError("Invalid connector token.")

        print("[AUTH] Token verified.")

        if request.operation != "read":
            raise ValueError("Only read operation is allowed.")

        if request.source not in self.ALLOWED_SOURCES:
            raise KeyError(f"Source is not exposed: {request.source}")

        print(f"[CONNECTOR] Calling backend to read {request.source}...")
        records = self._backend.read(request.source)

        response = ConnectorResponse(
            source=request.source,
            records=records,
            count=len(records),
        )

        print(f"[CONNECTOR] Returned {response.count} record(s).")
        return response

    def read_source(self, source: str, token: str) -> ConnectorResponse:
        return self.read(ConnectorRequest(source, "read", token))
