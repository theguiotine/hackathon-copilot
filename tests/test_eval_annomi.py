import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from src import eval_annomi as ea


class Mapping(unittest.TestCase):
    def test_all_twelve_moves_map_to_coarse_set(self):
        from src.config import COACH_MOVES
        self.assertEqual(set(ea.COARSE), set(COACH_MOVES))
        self.assertEqual(set(ea.COARSE.values()), {"question_open", "question_closed", "reflection_simple",
                                                   "reflection_complex", "information_advice", "other"})

    def test_gold_labels(self):
        g = ea.gold_coach_label
        self.assertEqual(g({"counsellor_move": "question", "question_type": "open"}), "question_open")
        self.assertEqual(g({"counsellor_move": "reflection", "reflection_type": "complex"}), "reflection_complex")
        self.assertEqual(g({"counsellor_move": "information-or-advice"}), "information_advice")
        self.assertEqual(g({"counsellor_move": "other"}), "other")
        self.assertIsNone(g({"counsellor_move": ""}))
        self.assertEqual(ea.gold_talk_label({"client_talk": "Change"}), "change")
        self.assertIsNone(ea.gold_talk_label({"client_talk": ""}))


class Pipeline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.csv = Path(self.tmp.name) / "a.csv"
        ea.build_selftest_csv(self.csv)

    def tearDown(self):
        self.tmp.cleanup()

    def test_reads_and_builds_conversations(self):
        s = ea.read_sessions(self.csv)
        self.assertEqual(set(s), {"s1", "s2"})
        conv = ea.to_conversation("s1", s["s1"])
        self.assertEqual(len(conv.lines), 6)
        self.assertEqual(conv.lines[0].speaker, "coach")

    def test_analyze_counts_flags_and_pairs(self):
        coach, talk, fstats = ea.analyze(ea.read_sessions(self.csv))
        self.assertEqual(len(coach), 4)
        self.assertEqual(len(talk), 4)
        self.assertEqual(fstats["tiers"], {"S1": 1})
        self.assertEqual(coach[0][2:4], ("question_open", "question_open"))

    def test_report_has_only_aggregates(self):
        out = Path(self.tmp.name) / "out"
        text = ea.report(ea.read_sessions(self.csv), out)
        for phrase in ("walks this week", "chest pain", "Did you walk", "too tired"):
            self.assertNotIn(phrase, text)
        self.assertIn("macro-F1", text)
        self.assertIn("confusion matrix", text)
        self.assertIn("expert_raters == 10", text)
        self.assertIn("Expert agreement ceiling", text)
        self.assertTrue((out / "coach_all_predictions.csv").exists())
        for f in out.glob("*.csv"):
            self.assertNotIn("walks this week", f.read_text())

    def test_refuses_to_write_inside_repo(self):
        with self.assertRaises(ea.AdapterError):
            ea._safe_out(ea.REPO / "tmp_out")

    def test_errors_do_not_echo_cells(self):
        bad = Path(self.tmp.name) / "bad.csv"
        bad.write_text(",".join(ea.REQUIRED) + "\nS,SECRETVALUE,counsellor,hello,,,,,10,90\n")
        with self.assertRaises(ea.AdapterError) as cm:
            ea.read_sessions(bad)
        self.assertNotIn("SECRETVALUE", str(cm.exception))
        miss = Path(self.tmp.name) / "miss.csv"
        miss.write_text("session_id,text\nx,y\n")
        with self.assertRaises(ea.AdapterError):
            ea.read_sessions(miss)

    def test_selftest_flag_runs_and_prints_no_text(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(ea.main(["--selftest"]), 0)
        self.assertNotIn("chest pain", buf.getvalue())
        self.assertIn("COACH MOVES", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
