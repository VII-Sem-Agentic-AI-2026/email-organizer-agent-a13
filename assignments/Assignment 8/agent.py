from models import EmailThread, LockedPlan, SwarmResult
from workers import ParallelSwarm
from merge import merge_results

class EmailSwarmCoordinator:
    def __init__(self, max_workers=4):
        self.swarm = ParallelSwarm(max_workers)

    def execute(self, emails, plan=None):
        plan = plan or LockedPlan()

        print("Running sequential baseline...")
        sequential_groups, sequential_time = self.swarm.run_sequential(emails, plan)

        parallel_groups, parallel_time = self.swarm.run(emails, plan)
        merged = merge_results(emails, parallel_groups, plan)

        print("\nSelecting best candidate for each email...")
        for item in merged:
            print(f"{item.thread_id}: selected {item.selected_worker}, score={item.alignment_score}")

        return SwarmResult(
            self.swarm.processed_thread_ids,
            merged,
            min(len(emails), self.swarm.max_workers),
            len(merged) == len(emails),
        ), sequential_time, parallel_time
