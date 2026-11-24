import tempfile
import unittest
from pathlib import Path
from models import AgentStep, RunState
from audit import AuditLog
from checkpoint import CheckpointStore
from runtime import RuntimeController, BudgetExceeded, ApprovalRequired

def action(inputs):
    return {"received": inputs}

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.audit = AuditLog(root / "audit.json")
        self.checkpoints = CheckpointStore(root / "checkpoint.json")
        self.runtime = RuntimeController(2, self.audit, self.checkpoints)

    def tearDown(self):
        self.temp.cleanup()

    def test_audit_records_inputs_and_outputs(self):
        step = AgentStep("1", "Read data", "read_data",
                         {"source": "inbox"}, action)
        state = self.runtime.run([step], RunState("R1"))
        entry = self.audit.entries[0]
        self.assertEqual(entry["inputs"], {"source": "inbox"})
        self.assertEqual(entry["output"], {"received": {"source": "inbox"}})
        self.assertEqual(state.status, "COMPLETED")

    def test_budget_pauses_and_checkpoint_resumes(self):
        steps = [
            AgentStep(str(i), "Do work", f"work_{i}", {}, action)
            for i in range(3)
        ]
        state = self.runtime.run(steps, RunState("R2"))
        self.assertEqual(state.status, "PAUSED_BUDGET")
        self.assertEqual(state.next_step, 2)

        resumed = self.checkpoints.load()
        runtime2 = RuntimeController(2, self.audit, self.checkpoints)
        final = runtime2.run(steps, resumed)
        self.assertEqual(final.status, "COMPLETED")
        self.assertEqual(final.next_step, 3)

    def test_risky_step_waits_for_approval(self):
        risky = AgentStep("P1", "Publish", "publish", {}, action, risky=True)
        with self.assertRaises(ApprovalRequired):
            self.runtime.run([risky], RunState("R3"))
        self.assertEqual(self.checkpoints.load().status, "WAITING_FOR_APPROVAL")
        self.assertEqual(self.audit.entries[-1]["status"], "BLOCKED")

    def test_approved_risky_step_runs(self):
        risky = AgentStep("P1", "Publish", "publish", {}, action, risky=True)
        state = self.runtime.run(
            [risky], RunState("R4"), approved_actions={"publish"}
        )
        self.assertEqual(state.status, "COMPLETED")

    def test_checkpoint_restores_state(self):
        step = AgentStep("1", "Read", "read", {}, action)
        self.runtime.run([step], RunState("R5"))
        loaded = self.checkpoints.load()
        self.assertEqual(loaded.run_id, "R5")
        self.assertEqual(loaded.next_step, 1)
        self.assertEqual(len(loaded.outputs), 1)

    def test_invalid_budget_rejected(self):
        with self.assertRaises(ValueError):
            RuntimeController(0, self.audit, self.checkpoints)

if __name__ == "__main__":
    unittest.main()
