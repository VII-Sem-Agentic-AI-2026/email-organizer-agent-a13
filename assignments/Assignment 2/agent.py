import re
from tool_layer import EmailTools


class EmailOrganizerAgent:
    def __init__(self, tools=None):
        self.tools = tools or EmailTools()
        self.evidence = []

    def run(self):
        print("\n[1] TOOL: Read inbox and threads")
        inbox_result = self.tools.read_inbox()
        print("    Source:", inbox_result.source)
        if not inbox_result.success:
            raise RuntimeError(inbox_result.message)

        print("\n[2] TOOL: Read contacts")
        contacts_result = self.tools.read_contacts()
        print("    Source:", contacts_result.source)
        contacts = {c.email: c for c in contacts_result.data}

        results = []

        for email in inbox_result.data:
            print(f"\n--- Processing {email.email_id}: {email.subject} ---")

            print("[3] TOOL: Validate email")
            validation = self.tools.validate_email(email)
            print("    Result:", "VALID" if validation.success else "INVALID")

            if not validation.success:
                continue

            print("[4] TOOL: Read email thread")
            thread = self.tools.read_thread(email.thread_id)
            print("    Messages retrieved:", len(thread.data) if thread.success else 0)

            print("[5] TOOL: Look up contact and previous replies")
            contact = contacts.get(email.sender)
            previous = self.tools.read_prior_replies(email.sender)
            print("    Contact:", contact.name if contact else "Not found")
            print("    Previous replies:", len(previous.data))

            print("[6] TOOL: Check deadline, if present")
            dates = re.findall(r"\d{4}-\d{2}-\d{2}", email.body)
            deadline_result = None
            if dates:
                deadline_result = self.tools.calculate_days_until(dates[0])
                print("    Deadline:", dates[0])
                print("    Days remaining:", deadline_result.data)
            else:
                print("    No ISO-format deadline found.")

            results.append({
                "email": email,
                "contact": contact,
                "thread": thread.data if thread.success else [],
                "previous_replies": previous.data,
                "validation": validation.success,
                "deadline": deadline_result
            })

        self.evidence = [
            "mock_inbox", "mock_contacts", "mock_threads",
            "mock_prior_replies", "email_validator", "date_calculator"
        ]
        return results

    def display(self, results):
        print("\n===== VERIFIED TOOL RESULTS =====")
        for item in results:
            email = item["email"]
            print(f"\n{email.email_id} | {email.subject}")
            print("Sender:", item["contact"].name if item["contact"] else "Unknown")
            print("Thread messages:", len(item["thread"]))
            print("Previous replies:", len(item["previous_replies"]))
            print("Validation:", "PASS" if item["validation"] else "FAIL")
            if item["deadline"]:
                print("Days until deadline:", item["deadline"].data)

        print("\nAll displayed facts were obtained using tools.")
        print("No emails were sent.")


