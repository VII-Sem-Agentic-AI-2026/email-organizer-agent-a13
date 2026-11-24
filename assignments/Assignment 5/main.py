from agent import EmailDataAgent
from connector import EmailDataConnector
from data_source import MockDataSource, AlternateMockDataSource

TOKEN = "local-demo-token"

def show(label, context):
    print(f"\n{label}")
    print("=" * 45)

    for source, records in context.items():
        print(f"\n{source}: {len(records)} record(s)")
        for row in records:
            print(" ", row)

def main():
    print("\n========== LAB 5: CONNECTOR DEMO ==========")

    print("\n[STEP 1] Connecting original data source")
    connector = EmailDataConnector(MockDataSource(), TOKEN)
    agent = EmailDataAgent(connector, TOKEN)

    print("\n[STEP 2] Agent requesting data through connector")
    context = agent.collect_email_context()
    show("ORIGINAL DATA SOURCE", context)

    print("\n[STEP 3] Replacing backend")
    replacement_connector = EmailDataConnector(
        AlternateMockDataSource(), TOKEN
    )

    print("[STEP 4] Reusing the same agent interface")
    replacement_agent = EmailDataAgent(replacement_connector, TOKEN)
    replacement_context = replacement_agent.collect_email_context()
    show("REPLACEMENT DATA SOURCE", replacement_context)

    print("\n========== DEMONSTRATION COMPLETE ==========")
    print("All data requests passed through the connector.")
    print("Agent implementation did not need modification.")
    print("This is MCP-style, not the official MCP protocol.")
    print("No live Gmail or Calendar account was accessed.")

if __name__ == "__main__":
    main()
