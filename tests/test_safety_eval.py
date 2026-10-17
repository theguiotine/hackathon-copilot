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

    def test_shows_real_misses_not_100_percent(self):
        self.assertGreater(self.r["misses"], 0)
        self.assertLess(self.r["recall"], 1.0)
        missed = " ".join(x["text"] for x in self.r["misses_list"])
        self.assertIn("catch my breath", missed)

    def test_negation_cases_stay_quiet(self):
        quiet = {x["text"] for x in self.r["quiet_list"]}
        self.assertIn("No tengo dolor de pecho ni fiebre.", quiet)
        self.assertIn("No fever and no chest pain, just tired.", quiet)
        self.assertEqual(self.r["false_alarms"], len(self.r["false_alarms_list"]))
        self.assertFalse({x["text"] for x in self.r["false_alarms_list"]} & quiet)

    def test_scope_and_sentence_labels(self):
        self.assertIn("invented fixtures", self.r["scope"])
        self.assertIn("Safety net, not a diagnosis", self.r["sentence"])


if __name__ == "__main__":
    unittest.main()
