import unittest
from agent import EmailSwarmCoordinator
from merge import merge_results, select_best
from models import Candidate, EmailThread, LockedPlan
from workers import ParallelSwarm

class SwarmTests(unittest.TestCase):
    def setUp(self):
        self.emails = [EmailThread("1", "a@x.com", "Urgent deadline", "Report due today."),
                       EmailThread("2", "b@x.com", "Question", "Please clarify this topic.")]
        self.plan = LockedPlan()

    def test_every_thread_processed_and_merged(self):
        result = EmailSwarmCoordinator(2).execute(self.emails, self.plan)
        self.assertTrue(result.all_threads_processed)
        self.assertEqual({x.thread_id for x in result.selected}, {"1", "2"})
        self.assertEqual(len(result.selected), 2)

    def test_merge_selects_highest_plan_alignment(self):
        low = Candidate("1", "Pretty Worker", "Normal", "short", "reply", 2, ("subject",))
        high = Candidate("1", "Plan Worker", "High", "complete", "reply", 7, self.plan.required_fields)
        self.assertEqual(select_best([low, high], self.plan).worker, "Plan Worker")

    def test_input_order_preserved_after_fan_in(self):
        swarm = ParallelSwarm(2)
        groups = swarm.run(self.emails, self.plan)
        merged = merge_results(self.emails, groups, self.plan)
        self.assertEqual([x.thread_id for x in merged], ["1", "2"])

    def test_empty_input(self):
        result = EmailSwarmCoordinator().execute([], self.plan)
        self.assertEqual(result.selected, [])
        self.assertTrue(result.all_threads_processed)

    def test_merge_rejects_missing_group(self):
        with self.assertRaises(ValueError):
            merge_results(self.emails, [], self.plan)

if __name__ == "__main__":
    unittest.main()
