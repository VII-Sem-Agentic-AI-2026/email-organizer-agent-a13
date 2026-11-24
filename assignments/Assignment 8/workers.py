from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from time import perf_counter
from models import Candidate, EmailThread, LockedPlan

class EmailWorker:
    def __init__(self, name):
        self.name = name

    def process(self, email, plan):
        print(f"[START] {self.name}: {email.thread_id}", flush=True)

        text = f"{email.subject} {email.body}".lower()
        urgent = any(w in text for w in ("urgent", "today", "tomorrow", "deadline", "asap"))
        priority = "High" if urgent else "Normal"

        summary = email.body.strip().split(".")[0][:180]
        draft = (
            f"Hello {email.sender.split('@')[0]},\n\n"
            f"Thank you for your email regarding '{email.subject}'. "
            "I have noted the details and will review the requested action.\n\nRegards"
        )

        covered = ("sender", "subject", "priority", "summary", "draft_reply")
        score = sum(field in covered for field in plan.required_fields)
        if urgent and "urgent deadlines first" in plan.priority_rules:
            score += 2

        print(f"[DONE] {self.name}: {email.thread_id} | score={score}", flush=True)
        return Candidate(email.thread_id, self.name, priority, summary, draft, score, covered)


class ParallelSwarm:
    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self.worker_names = ["Triage Worker", "Reply Worker"]
        self.processed_thread_ids = []

    def run_sequential(self, emails, plan):
        workers = [EmailWorker(name) for name in self.worker_names]
        start = perf_counter()
        groups = [
            [worker.process(email, plan) for worker in workers]
            for email in emails
        ]
        return groups, perf_counter() - start

    def run(self, emails, plan):
        if not emails:
            return [], 0.0

        workers = [EmailWorker(name) for name in self.worker_names]
        results = {email.thread_id: [] for email in emails}
        start = perf_counter()

        print("\nStarting parallel worker fan-out...")
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {
                pool.submit(worker.process, email, plan): email.thread_id
                for email in emails
                for worker in workers
            }

            for future in as_completed(futures):
                thread_id = futures[future]
                results[thread_id].append(future.result())

        elapsed = perf_counter() - start
        self.processed_thread_ids = [email.thread_id for email in emails]

        groups = [results[email.thread_id] for email in emails]
        print("Parallel worker fan-in completed.")
        return groups, elapsed
