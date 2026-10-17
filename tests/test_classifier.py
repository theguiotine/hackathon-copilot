import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from src import classifier_train as ct
from src import eval_annomi as ea
from src.classifier import NaiveBayes, split_sessions


class Split(unittest.TestCase):
    def test_deterministic_disjoint_and_nonempty(self):
        ids = [f"s{i}" for i in range(200)]
        a = split_sessions(ids)
        self.assertEqual(a, split_sessions(list(reversed(ids))))
        train, test = a
        self.assertFalse(train & test)
        self.assertEqual(train | test, set(ids))
        self.assertTrue(20 < len(test) < 70)


class Model(unittest.TestCase):
    def test_learns_separable_data_and_roundtrips(self):
        texts = ["how are you feeling", "what helped you", "did you walk", "are you free",
                 "you should walk daily", "you must rest"] * 3
        labels = ["open", "open", "closed", "closed", "advice", "advice"] * 3
        m = NaiveBayes().fit(texts, labels)
        self.assertEqual(m.predict("how are you doing"), "open")
        self.assertEqual(m.predict("you should rest"), "advice")
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "m.json"
            m.save(p)
            m2 = NaiveBayes.load(p)
            self.assertEqual(m2.predict("did you rest"), m.predict("did you rest"))

    def test_fit_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            NaiveBayes().fit([], [])
        with self.assertRaises(ValueError):
            NaiveBayes().fit(["a"], ["x", "y"])


class Train(unittest.TestCase):
    def test_no_test_session_line_is_trained_on(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.csv"
            ct.build_selftest_csv(p)
            sessions = ea.read_sessions(p)
            train, test = split_sessions(sessions)
            self.assertTrue(train and test)
            rows = ct.datasets(sessions)["coach"]
            self.assertTrue(all(r[0] in train for r in rows if r[0] not in test))

    def test_selftest_prints_aggregates_only_and_refuses_repo(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(ct.main(["--selftest"]), 0)
        out = buf.getvalue()
        self.assertIn("RULES baseline", out)
        self.assertIn("CLASSIFIER", out)
        self.assertNotIn("walks", out)
        self.assertNotIn("Monday", out)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.csv"
            ct.build_selftest_csv(p)
            with self.assertRaises(ea.AdapterError):
                ct.evaluate(ea.read_sessions(p), ea.REPO / "tmp_out")


if __name__ == "__main__":
    unittest.main()
