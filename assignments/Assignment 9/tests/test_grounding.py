import unittest
from models import Candidate
from grounding import ground_candidate
from agent import run_research_agent

class GroundingTests(unittest.TestCase):
    def test_supported_thread_and_owner_claims_are_kept(self):
        result = run_research_agent()
        by_id = {x.candidate.unit_id: x for x in result.items}
        self.assertIn("T-101", by_id)
        self.assertEqual(len(by_id["T-101"].evidence.unsupported_claims), 0)
        self.assertTrue(any(x.startswith("R-101") for x in by_id["T-101"].evidence.source_ids))

    def test_unsupported_candidate_is_rejected(self):
        result = run_research_agent()
        self.assertIn("T-999", result.rejected_unit_ids)
        row = next(x for x in result.evidence_table if x.unit_id == "T-999")
        self.assertFalse(row.in_scope)
        self.assertTrue(row.unsupported_claims)

    def test_every_candidate_has_evidence_record(self):
        result = run_research_agent()
        self.assertEqual(len(result.evidence_table), 3)
        self.assertEqual({x.unit_id for x in result.evidence_table}, {"T-101", "T-102", "T-999"})

    def test_unknown_thread_cannot_be_grounded(self):
        c = Candidate("T-404", "Unknown", "Anything", ["A real source supports this statement"])
        g = ground_candidate(c)
        self.assertFalse(g.evidence.in_scope)
        self.assertEqual(g.evidence.source_ids, [])

if __name__ == "__main__":
    unittest.main()
