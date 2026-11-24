from agent import EmailMemoryAgent, build_demo_store

def main():
    agent = EmailMemoryAgent(build_demo_store())
    state, results = agent.run()

    print("\\nLAB 4 — MEMORY & RETRIEVAL")
    print("=" * 48)
    print("Short-term run state:")
    print("Current email:", state.current_email_id)
    print("Current draft:", state.current_draft)

    print("\\nLong-term memory — tag matches:")
    for hit in results["tagged"]:
        print(f"- {hit.item.item_id} | tags={hit.matched_tags} | {hit.item.text}")

    print("\\nLong-term memory — similar prior items:")
    for hit in results["similar"]:
        print(f"- {hit.item.item_id} | similarity={hit.score:.3f} | {hit.item.text}")

    print("\\nCurrent draft remains separate from stored history.")
    print("Demo uses local sample records; no Gmail account is accessed.")

if __name__ == "__main__":
    main()
