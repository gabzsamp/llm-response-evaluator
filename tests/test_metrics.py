import unittest

from evaluator import metrics

GOOD = {"accuracy": 5, "instruction_following": 5, "clarity": 4}
OK = {"accuracy": 3, "instruction_following": 3, "clarity": 3}
LONG_TEXT = "Response A follows the instruction exactly and is clearer overall."


class TestScores(unittest.TestCase):
    def test_total_score(self):
        self.assertEqual(metrics.total_score(GOOD), 14)

    def test_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            metrics.total_score({"accuracy": 6, "instruction_following": 3, "clarity": 3})

    def test_rejects_missing_dimension(self):
        with self.assertRaises(ValueError):
            metrics.total_score({"accuracy": 3, "clarity": 3})

    def test_implied_preference(self):
        self.assertEqual(metrics.implied_preference(GOOD, OK), "A")
        self.assertEqual(metrics.implied_preference(OK, GOOD), "B")
        self.assertEqual(metrics.implied_preference(OK, OK), "tie")


class TestQA(unittest.TestCase):
    def record(self, preferred, justification=LONG_TEXT):
        return {"scores_a": GOOD, "scores_b": OK, "preferred": preferred,
                "justification": justification}

    def test_consistent_record_has_no_findings(self):
        self.assertEqual(metrics.qa_findings(self.record("A")), [])

    def test_contradiction_is_flagged(self):
        findings = metrics.qa_findings(self.record("B"))
        self.assertEqual(len(findings), 1)
        self.assertIn("contradiction", findings[0])

    def test_tie_is_not_a_contradiction(self):
        self.assertEqual(metrics.qa_findings(self.record("tie")), [])

    def test_short_justification_is_flagged(self):
        findings = metrics.qa_findings(self.record("A", "better"))
        self.assertTrue(any("too short" in f for f in findings))


class TestKappa(unittest.TestCase):
    def test_perfect_agreement(self):
        self.assertAlmostEqual(metrics.cohens_kappa(["A", "B", "A"], ["A", "B", "A"]), 1.0)

    def test_known_value(self):
        # observed 0.75, chance 0.5 -> kappa 0.5
        self.assertAlmostEqual(
            metrics.cohens_kappa(["A", "A", "B", "B"], ["A", "B", "B", "B"]), 0.5)

    def test_systematic_disagreement(self):
        self.assertAlmostEqual(metrics.cohens_kappa(["A", "B"], ["B", "A"]), -1.0)

    def test_single_label_everywhere(self):
        self.assertEqual(metrics.cohens_kappa(["A", "A"], ["A", "A"]), 1.0)

    def test_length_mismatch(self):
        with self.assertRaises(ValueError):
            metrics.cohens_kappa(["A"], ["A", "B"])

    def test_empty(self):
        with self.assertRaises(ValueError):
            metrics.cohens_kappa([], [])

    def test_interpretation(self):
        self.assertEqual(metrics.interpret_kappa(0.5), "moderate")
        self.assertEqual(metrics.interpret_kappa(0.9), "almost perfect")
        self.assertEqual(metrics.interpret_kappa(-0.3), "worse than chance")


if __name__ == "__main__":
    unittest.main()
