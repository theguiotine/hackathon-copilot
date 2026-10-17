import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

import metrics
import mock_data
import run_eval

# Hand-checkable example: 6 rows, labels A/B/C.
#   true: A A A B B C
#   pred: A A B B C C
# A: tp2 fp0 fn1 -> p 1, r 2/3, f1 0.8
# B: tp1 fp1 fn1 -> p .5, r .5, f1 .5
# C: tp1 fp1 fn0 -> p .5, r 1, f1 2/3
TRUE = ["A", "A", "A", "B", "B", "C"]
PRED = ["A", "A", "B", "B", "C", "C"]


class TestPerLabel(unittest.TestCase):
    def test_per_label(self):
        s = metrics.per_label(TRUE, PRED)
        self.assertAlmostEqual(s["A"]["p"], 1.0)
        self.assertAlmostEqual(s["A"]["r"], 2 / 3)
        self.assertAlmostEqual(s["A"]["f1"], 0.8)
        self.assertEqual(s["A"]["n"], 3)
        self.assertAlmostEqual(s["B"]["p"], 0.5)
        self.assertAlmostEqual(s["B"]["r"], 0.5)
        self.assertAlmostEqual(s["B"]["f1"], 0.5)
        self.assertEqual(s["B"]["n"], 2)
        self.assertAlmostEqual(s["C"]["p"], 0.5)
        self.assertAlmostEqual(s["C"]["r"], 1.0)
        self.assertAlmostEqual(s["C"]["f1"], 2 / 3)
        self.assertEqual(s["C"]["n"], 1)

    def test_unpredicted_label_scores_zero(self):
        s = metrics.per_label(["A", "B"], ["A", "A"])
        self.assertEqual(s["B"], {"p": 0.0, "r": 0.0, "f1": 0.0, "n": 1})

    def test_length_mismatch(self):
        with self.assertRaises(ValueError):
            metrics.per_label(["A"], ["A", "B"])

    def test_macro_f1(self):
        self.assertAlmostEqual(metrics.macro_f1(TRUE, PRED), (0.8 + 0.5 + 2 / 3) / 3)

    def test_macro_f1_perfect(self):
        self.assertAlmostEqual(metrics.macro_f1(["x", "y"], ["x", "y"]), 1.0)


class TestConfusion(unittest.TestCase):
    def test_matrix(self):
        labels, m = metrics.confusion_matrix(TRUE, PRED)
        self.assertEqual(labels, ["A", "B", "C"])
        self.assertEqual(m, [[2, 1, 0], [0, 1, 1], [0, 0, 1]])
        self.assertEqual(sum(map(sum, m)), len(TRUE))


class TestByLanguage(unittest.TestCase):
    def test_split(self):
        langs = ["en", "en", "en", "es", "es", "es"]
        res = metrics.by_language(TRUE, PRED, langs)
        self.assertEqual(set(res), {"en", "es"})
        # en: true A A A, pred A A B -> A: p1 r2/3 f1 .8 ; B: p0 r0
        self.assertEqual(res["en"]["n"], 3)
        self.assertAlmostEqual(res["en"]["by_label"]["A"]["f1"], 0.8)
        self.assertAlmostEqual(res["en"]["by_label"]["B"]["p"], 0.0)
        # es: true B B C, pred B C C -> B: p1 r.5 ; C: p.5 r1
        self.assertAlmostEqual(res["es"]["by_label"]["B"]["p"], 1.0)
        self.assertAlmostEqual(res["es"]["by_label"]["B"]["r"], 0.5)
        self.assertAlmostEqual(res["es"]["by_label"]["C"]["r"], 1.0)
        self.assertAlmostEqual(res["es"]["macro_f1"], (2 / 3 + 2 / 3) / 2)


class TestKappa(unittest.TestCase):
    def test_textbook(self):
        # 50 items: both yes 20, a-yes/b-no 5, a-no/b-yes 10, both no 15.
        a = ["y"] * 25 + ["n"] * 25
        b = ["y"] * 20 + ["n"] * 5 + ["y"] * 10 + ["n"] * 15
        # p_o = 35/50 = .7 ; p_e = .5*.6 + .5*.4 = .5 ; kappa = .4
        self.assertAlmostEqual(metrics.cohen_kappa(a, b), 0.4)

    def test_perfect_and_chance(self):
        self.assertAlmostEqual(metrics.cohen_kappa(["a", "b"], ["a", "b"]), 1.0)
        # p_o = .5, p_e = .5 -> 0
        self.assertAlmostEqual(metrics.cohen_kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"]), 0.0)

    def test_single_category(self):
        self.assertEqual(metrics.cohen_kappa(["a", "a"], ["a", "a"]), 1.0)


class TestRatings(unittest.TestCase):
    A = [1, 2, 3, 4, 5]
    B = [1, 3, 5, 4, 2]  # diffs 0 1 2 0 3

    def test_mae(self):
        self.assertAlmostEqual(metrics.mean_absolute_error(self.A, self.B), 6 / 5)

    def test_within_one(self):
        self.assertAlmostEqual(metrics.within_one(self.A, self.B), 3 / 5)

    def test_out_of_range(self):
        with self.assertRaises(ValueError):
            metrics.mean_absolute_error([0], [1])
        with self.assertRaises(ValueError):
            metrics.within_one([6], [5])


class TestNeedsHuman(unittest.TestCase):
    def test_binary(self):
        t = [True, True, True, False, False, False]
        p = [True, True, False, True, False, False]
        b = metrics.binary_precision_recall(t, p)
        self.assertEqual((b["tp"], b["fp"], b["fn"]), (2, 1, 1))
        self.assertAlmostEqual(b["p"], 2 / 3)
        self.assertAlmostEqual(b["r"], 2 / 3)

    def test_no_positives(self):
        b = metrics.binary_precision_recall([False, False], [False, False])
        self.assertEqual((b["p"], b["r"]), (0.0, 0.0))


class TestMockAndCli(unittest.TestCase):
    def test_mock_pair_shape(self):
        preds, labels = mock_data.make_pair()
        self.assertEqual(len(preds), 200)
        self.assertEqual(len(labels), 200)
        self.assertEqual({r["language"] for r in labels}, {"en", "es"})
        self.assertTrue({r["label"] for r in labels} <= set(mock_data.LABELS))
        self.assertEqual(preds, mock_data.make_pair()[0])  # deterministic

    def test_cli_end_to_end(self):
        preds, labels = mock_data.make_pair()
        with tempfile.TemporaryDirectory() as d:
            pp, lp = os.path.join(d, "p.csv"), os.path.join(d, "l.csv")
            mock_data.write_csv(preds, pp)
            mock_data.write_csv(labels, lp)
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = run_eval.main([pp, lp])
        out = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("Matched rows: 200", out)
        self.assertIn("language=en", out)
        self.assertIn("language=es", out)
        self.assertIn("confusion matrix", out)
        self.assertIn("needs_human: precision", out)

    def test_cli_missing_column(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "bad.csv")
            with open(p, "w") as f:
                f.write("call_id,label\nx,affirm\n")
            with redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
                run_eval.format_report(p, p)


if __name__ == "__main__":
    unittest.main()
