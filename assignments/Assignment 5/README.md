# Assignment 5 — MCP-Style Connector

## Aim
Expose all Email Organizer data sources through one typed connector so data-facing agents use a single governed access path.

## Sources exposed
- `inbox_threads` — inbox emails and thread details
- `contacts_replies` — contact details and prior replies
- `calendar_tasks` — calendar events and task list

## What is implemented
- A replaceable `DataSource` backend contract.
- `EmailDataConnector` as the single public data-access surface.
- Typed `ConnectorRequest` and `ConnectorResponse` objects.
- Token check before every read.
- Allow-list of exposed data sources and operations.
- `EmailDataAgent` accesses all three sources only through the connector.
- A second mock backend proves that the data source can be replaced without changing agent logic.

## Run on Windows
```powershell
py -3.11 main.py
```

Run tests:
```powershell
py -3.11 -m unittest discover -s tests -v
```

No external packages, API keys or real accounts are required.

## Architecture
```text
Email Data Agent
       |
       v
EmailDataConnector  <-- token + source + operation validation
       |
       v
DataSource interface
       |
       +--> MockDataSource
       |
       +--> AlternateMockDataSource
```

## Important note
This is an MCP-style typed connector demonstration, not a server implementing the official Model Context Protocol. The access token is a local demo token; production authentication would require a proper identity and authorization system.

## Acceptance checks
- All data reads pass through the connector.
- Invalid tokens are rejected.
- Unexposed sources and unsupported operations are rejected.
- Swapping the backend does not require changes to `EmailDataAgent`.
