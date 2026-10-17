"""Tests for src/eval_needs_human.py and the cross-validation mode of src/train_annomi.py (fictional fixtures only)."""
import contextlib
import csv
import io
import tempfile
import unittest
from pathlib import Path

from src import eval_needs_human as nh
from src import train_annomi as ta
from src import eval_annomi as ea
from src.safe_paths import AdapterError


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


HEADER = ["call_id", "line_number", "speaker", "text", "needs_human", "language"]


class NeedsHuman(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def results(self, rows):
        p = self.dir / "x.csv"
        write_csv(p, HEADER, rows)
        sessions, stats = nh.read_labelled(p)
        return nh.score(sessions), stats

    def test_counts_and_metrics_on_a_known_fixture(self):
        res, _ = self.results([
            ("c1", 1, "counsellor", "How are you?", "no", "en"),
            ("c1", 2, "client", "I have had chest pain since last night.", "yes", "en"),   # caught
            ("c1", 3, "client", "My stomach has felt strange for days.", "yes", "en"),     # missed
            ("c1", 4, "client", "I want to walk on Sunday.", "no", "en"),                  # quiet, correct
            ("c1", 5, "client", "I have chest pain.", "no", "en"),                         # false alarm (gold says no)
            ("c2", 1, "client", "No puedo respirar bien.", "yes", "es"),                   # caught (S1)
        ])
        s = nh.summarize(res)
        self.assertEqual((s["lines"], s["positives"], s["tp"], s["fp"], s["fn"]), (5, 3, 2, 1, 1))
        self.assertAlmostEqual(s["precision"], 2 / 3)
        self.assertAlmostEqual(s["recall"], 2 / 3)
        self.assertAlmostEqual(s["false_alarms_per_100"], 20.0)
        self.assertAlmostEqual(s["recall_s1_only"], 2 / 3)

    def test_coach_lines_are_never_scored(self):
        res, _ = self.results([("c1", 1, "counsellor", "I have chest pain.", "yes", "en"),
                               ("c1", 2, "client", "Fine.", "no", "en")])
        self.assertEqual([r[1] for r in res], [2])

    def test_unknown_or_blank_labels_are_left_out_and_counted(self):
        res, stats = self.results([("c1", 1, "client", "I have chest pain.", "", "en"),
                                   ("c1", 2, "client", "Fine.", "maybe", "en"),
                                   ("c1", 3, "client", "Okay.", "No", "en")])
        self.assertEqual(len(res), 1)
        self.assertEqual(stats["unlabelled_participant_lines"], 2)

    def test_language_comes_from_the_column_and_falls_back_to_the_flag(self):
        res, _ = self.results([("c1", 1, "client", "I have chest pain.", "yes", "en"),
                               ("c1", 2, "client", "Me duele el pecho desde anoche.", "yes", "es")])
        self.assertEqual({r[2] for r in res}, {"en", "es"})
        p = self.dir / "nolang.csv"
        write_csv(p, ["session_id", "line_number", "speaker", "text", "needs_human"],
                  [("s", 1, "client", "I have chest pain.", "yes")])
        sessions, _ = nh.read_labelled(p, "en")
        self.assertEqual(nh.score(sessions)[0][2], "en")

    def test_file_without_needs_human_is_skipped_not_an_error(self):
        p = self.dir / "annomi.csv"
        write_csv(p, ["session_id", "line_number", "speaker", "text"], [("s", 1, "client", "hello")])
        sessions, stats = nh.read_labelled(p)
        self.assertIsNone(sessions)
        out = nh.report([p])
        self.assertIn("skipped (no needs_human column)", out)
        self.assertIn("Nothing scored", out)

    def test_report_never_prints_text_or_file_names(self):
        p = self.dir / "secret-name.csv"
        write_csv(p, HEADER, [("c1", 1, "client", "I have had chest pain since last night.", "yes", "en"),
                              ("c1", 2, "client", "Zebra umbrella sentence.", "no", "es")])
        out = nh.report([p])
        for forbidden in ("chest pain", "Zebra", "secret-name", str(self.dir)):
            self.assertNotIn(forbidden, out)
        self.assertIn("recall counting only S1 flags", out)
        self.assertIn("language es", out)

    def test_missing_columns_error_names_columns_only(self):
        p = self.dir / "bad.csv"
        write_csv(p, ["needs_human", "text"], [("yes", "Private words")])
        with self.assertRaises(AdapterError) as cm:
            nh.read_labelled(p)
        self.assertNotIn("Private words", str(cm.exception))

    def test_output_inside_the_repo_is_refused_and_outside_is_written(self):
        p = self.dir / "x.csv"
        write_csv(p, HEADER, [("c1", 1, "client", "I have chest pain.", "yes", "en")])
        repo = Path(__file__).resolve().parent.parent
        with self.assertRaises(AdapterError):
            nh.report([p], repo / "tmp_out_should_not_exist")
        self.assertFalse((repo / "tmp_out_should_not_exist").exists())
        nh.report([p], self.dir / "out")
        self.assertTrue((self.dir / "out" / "needs_human_file1_predictions.csv").is_file())

    def test_no_out_folder_means_no_files(self):
        p = self.dir / "x.csv"
        write_csv(p, HEADER, [("c1", 1, "client", "I have chest pain.", "yes", "en")])
        before = {x.name for x in self.dir.iterdir()}
        nh.report([p])
        self.assertEqual({x.name for x in self.dir.iterdir()}, before)

    def test_selftest_runs_and_missing_env_is_a_clear_error(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(nh.main(["--selftest"]), 0)
        self.assertIn("precision", buf.getvalue())
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            import os
            saved = {k: os.environ.pop(k, None) for k in (ea.ENV_CSV, nh.ENV_TEXT_CSV)}
            try:
                self.assertEqual(nh.main([]), 1)
            finally:
                for k, v in saved.items():
                    if v is not None:
                        os.environ[k] = v
        self.assertIn(ea.ENV_CSV, err.getvalue())


class CrossValidation(unittest.TestCase):
    def test_fold_assignment_is_deterministic_and_sessions_never_split(self):
        ids = [f"sess{i}" for i in range(200)]
        folds = [ta.fold_of(i) for i in ids]
        self.assertEqual(folds, [ta.fold_of(i) for i in ids])
        self.assertEqual(set(folds), {0, 1, 2, 3, 4})

    def test_cv_report_has_five_folds_and_mean_and_range(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "s.csv"
            ta.build_selftest_csv(p)
            out = ta.cross_validate(ea.read_sessions(p))
        self.assertIn("5 of 5 folds had data", out)
        for word in ("accuracy", "macro F1", "kappa", "mean", "min", "max", "RULES baseline"):
            self.assertIn(word, out)
        self.assertNotIn("walk", out)  # no line text in the report

    def test_cli_cv_selftest(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(ta.main(["--selftest", "--cv"]), 0)
        self.assertIn("5-fold cross-validation", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
