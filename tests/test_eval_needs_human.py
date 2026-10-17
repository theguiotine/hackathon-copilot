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
        self.assertEqual([r[1] for r in res], ["2"])

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
        self.assertTrue((self.dir / "out" / "needs_human_file_1_1_predictions.csv").is_file())

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
            saved = {k: os.environ.pop(k, None) for k in (ea.ENV_CSV, nh.ENV_CALL_LINES, nh.ENV_CALLS, nh.ENV_TEXTS)}
            try:
                self.assertEqual(nh.main([]), 1)
            finally:
                for k, v in saved.items():
                    if v is not None:
                        os.environ[k] = v
        self.assertIn(nh.ENV_CALL_LINES, err.getvalue())


class SyntheticFiles(unittest.TestCase):
    """The organizers' synthetic layout (invented here): call lines + calls file for language, and text messages."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        nh.build_selftest_synthetic(self.dir)

    def tearDown(self):
        self.tmp.cleanup()

    def test_language_is_joined_from_the_calls_file_by_call_id(self):
        langs = nh.read_call_languages(self.dir / "calls.csv")
        self.assertEqual(langs, {"k1": "en", "k2": "es"})
        sessions, stats = nh.read_labelled(self.dir / "lines.csv", "en", langs)
        res = nh.score(sessions)
        self.assertEqual({(r[0], r[2]) for r in res}, {("k1", "en"), ("k2", "es")})
        # the Spanish call is only flagged because it was run under Spanish rules
        spanish = [r for r in res if r[0] == "k2" and r[3]]
        self.assertEqual([r[4] for r in spanish], ["S1"])
        self.assertEqual(stats["rows_without_calls_language"], 0)

    def test_call_missing_from_the_calls_file_falls_back_to_lang_and_is_counted(self):
        sessions, stats = nh.read_labelled(self.dir / "lines.csv", "en", {"k1": "en"})
        self.assertEqual(stats["rows_without_calls_language"], 3)
        spanish = [r for r in nh.score(sessions) if r[0] == "k2" and r[3]]
        self.assertEqual([r[4] for r in spanish], [None])  # run under English rules, so the Spanish line is missed

    def test_calls_file_without_language_column_is_a_clear_error(self):
        bad = self.dir / "bad_calls.csv"
        write_csv(bad, ["call_id"], [("k1",)])
        with self.assertRaises(AdapterError) as cm:
            nh.read_call_languages(bad)
        self.assertIn("language", str(cm.exception))

    def test_texts_use_sender_as_speaker_and_message_id_as_key(self):
        sessions, stats = nh.read_labelled(self.dir / "texts.csv", "en")
        self.assertEqual(list(sessions), ["p1"])  # grouped per participant_id
        res = nh.score(sessions)
        self.assertEqual([r[1] for r in res], ["m002", "m004"])  # only sender == participant, keyed by message_id
        self.assertEqual({r[2] for r in res}, {"en"})  # --lang default, the file has none
        self.assertEqual([r[3] for r in res], [True, False])
        self.assertEqual(stats["unlabelled_participant_lines"], 0)

    def test_automatic_and_coach_senders_are_never_scored_even_if_labelled(self):
        p = self.dir / "t2.csv"
        write_csv(p, ["participant_id", "message_id", "sender", "text", "needs_human"],
                  [("p", "m1", "automatic", "I have chest pain.", "yes"), ("p", "m2", "coach", "I have chest pain.", "yes"),
                   ("p", "m3", "participant", "Okay.", "no")])
        sessions, _ = nh.read_labelled(p)
        self.assertEqual([r[1] for r in nh.score(sessions)], ["m3"])

    def test_texts_lang_flag_changes_the_rules_used(self):
        p = self.dir / "t3.csv"
        write_csv(p, ["participant_id", "message_id", "sender", "text", "needs_human"],
                  [("p", "m1", "participant", "No puedo respirar bien.", "yes")])
        en = nh.score(nh.read_labelled(p, "en")[0])
        es = nh.score(nh.read_labelled(p, "es")[0])
        self.assertEqual((en[0][4], es[0][4]), (None, "S1"))

    def test_unlabelled_text_rows_are_excluded_and_counted(self):
        p = self.dir / "t4.csv"
        write_csv(p, ["participant_id", "message_id", "sender", "text", "needs_human"],
                  [("p", "m1", "participant", "I have chest pain.", ""), ("p", "m2", "participant", "Okay.", "no")])
        sessions, stats = nh.read_labelled(p)
        self.assertEqual([r[1] for r in nh.score(sessions)], ["m2"])
        self.assertEqual(stats["unlabelled_participant_lines"], 1)

    def test_report_for_synthetic_sources_prints_no_text_and_no_paths(self):
        srcs = [("calls file", "calls", self.dir / "lines.csv", self.dir / "calls.csv"),
                ("texts file", "texts", self.dir / "texts.csv", None)]
        out = nh.report(srcs)
        for forbidden in ("chest pain", "respirar", "Reminder", "lines.csv", "texts.csv", str(self.dir)):
            self.assertNotIn(forbidden, out)
        self.assertIn("calls file: language es", out)
        self.assertIn("texts file: all languages", out)
        self.assertIn("comes from --lang", out)

    def test_sources_from_flags_requires_the_calls_file_with_call_lines(self):
        import argparse
        import os
        saved = {k: os.environ.pop(k, None) for k in (ea.ENV_CSV, nh.ENV_CALL_LINES, nh.ENV_CALLS, nh.ENV_TEXTS)}
        try:
            ns = argparse.Namespace(call_lines=str(self.dir / "lines.csv"), calls=None, texts=None, csv=None)
            with self.assertRaises(AdapterError):
                nh.sources_from(ns)
            ns.calls = str(self.dir / "calls.csv")
            ns.texts = str(self.dir / "texts.csv")
            self.assertEqual([s[0] for s in nh.sources_from(ns)], ["calls file", "texts file"])
            os.environ[nh.ENV_TEXTS] = str(self.dir / "texts.csv")
            ns2 = argparse.Namespace(call_lines=None, calls=None, texts=None, csv=None)
            self.assertEqual([s[0] for s in nh.sources_from(ns2)], ["texts file"])
        finally:
            os.environ.pop(nh.ENV_TEXTS, None)
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v

    def test_selftest_covers_all_three_sources(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(nh.main(["--selftest"]), 0)
        for label in ("calls file", "texts file", "file 1"):
            self.assertIn(label, buf.getvalue())


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
