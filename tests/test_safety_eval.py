import unittest

from src import safety_eval


class SafetyEval(unittest.TestCase):
    def setUp(self):
        self.r = safety_eval.run()

    def test_numbers_are_consistent_and_computed(self):
        r = self.r
        positives = r["correct_catches"] + r["misses"]
        self.assertGreater(positives, 0)
        self.assertEqual(r["recall"], round(r["correct_catches"] / positives, 3))
        self.assertEqual(r["flags_raised"], r["correct_catches"] + r["false_alarms"])
        self.assertEqual(r["false_alarms_per_10_calls"], round(10 * r["false_alarms"] / r["calls"], 2))
        self.assertEqual(len(r["misses_list"]), r["misses"])
        self.assertEqual(len(r["false_alarms_list"]), r["false_alarms"])

    def test_tuned_set_is_high_by_construction(self):
        # The rules were widened while looking at THIS set, so it is expected to be near 100%; the honest
        # out-of-sample number is the separate blind set. A drop here means a regression.
        self.assertGreaterEqual(self.r["recall"], 0.9)
        self.assertLessEqual(self.r["false_alarms"], 2)

    def test_negation_cases_stay_quiet(self):
        quiet = {x["text"] for x in self.r["quiet_list"]}
        self.assertIn("No tengo dolor de pecho ni fiebre.", quiet)
        self.assertIn("No fever and no chest pain, just tired.", quiet)
        self.assertEqual(self.r["false_alarms"], len(self.r["false_alarms_list"]))
        self.assertFalse({x["text"] for x in self.r["false_alarms_list"]} & quiet)

    def test_none_means_quiet_in_gold(self):
        import json, tempfile
        from pathlib import Path
        cases = {"cases": [{"id": "a", "language": "en", "kind": "no_flag", "text": "I walked three times.", "gold_tier": "none"},
                           {"id": "b", "language": "en", "kind": "flag", "text": "I have chest pain.", "gold_tier": "S1"}]}
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "c.json")
            p.write_text(json.dumps(cases))
            r = safety_eval.run(p)
        self.assertEqual((r["correct_catches"], r["misses"], r["false_alarms"]), (1, 0, 0))
        self.assertEqual(r["by_language"]["en"]["positives"], 1)

    def test_blind_results_file_is_consistent(self):
        from src.api import blind_results
        b = blind_results()
        self.assertIsNotNone(b)
        self.assertEqual(b["correct_catches"] + b["misses"], sum(v["positives"] for v in b["by_language"].values()))
        self.assertEqual(len(b["misses_list"]), b["misses"])
        self.assertIn("invented", b["scope"])

    def test_scope_and_sentence_labels(self):
        self.assertIn("invented fixtures", self.r["scope"])
        self.assertIn("Safety net, not a diagnosis", self.r["sentence"])


if __name__ == "__main__":
    unittest.main()
