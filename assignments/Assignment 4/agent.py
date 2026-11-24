from models import MemoryItem, RunState
from memory_store import MemoryStore

def build_demo_store() -> MemoryStore:
    return MemoryStore([
        MemoryItem("H001", "A student requested an extension for the project submission because of a medical appointment.", ["student", "extension", "project"], metadata={"outcome": "Faculty asked for a revised submission date."}),
        MemoryItem("H002", "The department administration asked for the accreditation report before the deadline.", ["admin", "deadline", "report"], metadata={"outcome": "Report deadline was confirmed."}),
        MemoryItem("H003", "A student asked about the format and evaluation criteria for the final project report.", ["student", "project", "format"], metadata={"outcome": "The standard project guidelines were shared."}),
        MemoryItem("H004", "A research collaborator requested a meeting to discuss the paper draft.", ["collaborator", "meeting", "research"], metadata={"outcome": "A meeting time was proposed."})
    ])

class EmailMemoryAgent:
    def __init__(self, store: MemoryStore):
        self.store = store

    def run(self):
        print("\n[1] INITIALIZING MEMORY STORE")
        items = self.store.all_items()
        print(f"[STORE] Loaded {len(items)} historical records.")
        for item in items:
            print(f"  Stored: {item.item_id}")

        print("\n[2] CREATING SHORT-TERM RUN STATE")
        state = RunState(
            current_email_id="CURRENT-001",
            current_draft="Student asks for an extension to the project submission deadline."
        )
        print(f"[STATE] Current email: {state.current_email_id}")
        print(f"[STATE] Current draft: {state.current_draft}")
        print("[STATE] Draft has NOT been added to long-term memory.")

        print("\n[3] RUNNING TAG-BASED RETRIEVAL")
        tags = ["student", "project"]
        print(f"[CALL] retrieve_by_tags({tags})")
        tagged = self.store.retrieve_by_tags(tags)
        print(f"[RESULT] Found {len(tagged)} matching records.")
        for hit in tagged:
            print(f"  {hit.item.item_id}: matched tags {hit.matched_tags}")

        print("\n[4] RUNNING SIMILARITY RETRIEVAL")
        print("[CALL] retrieve_similar(current_draft, k=3)")
        similar = self.store.retrieve_similar(state.current_draft, k=3)
        print(f"[RESULT] Found {len(similar)} similar records.")
        for hit in similar:
            print(f"  {hit.item.item_id}: similarity score {hit.score:.3f}")

        print("\n[5] CHECKING MEMORY SEPARATION")
        stored_ids = [item.item_id for item in self.store.all_items()]
        print(f"[STORE] Historical IDs: {stored_ids}")
        print(f"[CHECK] Current email in archive: {state.current_email_id in stored_ids}")

        return state, {"tagged": tagged, "similar": similar}
