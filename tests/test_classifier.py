import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from src import train_annomi as ct
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


class TaggerIntegration(unittest.TestCase):
    def setUp(self):
        from src.schema import Conversation
        self.conv = Conversation.from_dict({"id": "c", "channel": "call", "language": "en", "lines": [
            {"idx": 0, "speaker": "coach", "text": "Did you walk on Monday?"},
            {"idx": 1, "speaker": "participant", "text": "Okay."},
            {"idx": 2, "speaker": "coach", "text": "You should walk every day."},
            {"idx": 3, "speaker": "participant", "text": "I have chest pain."}]})
        coach = NaiveBayes().fit(["did you walk", "are you free", "how do you feel", "what helped"] * 3,
                                 ["question_closed", "question_closed", "question_open", "question_open"] * 3)
        talk = NaiveBayes().fit(["i want to", "i will try", "i can't", "no time"] * 3,
                                ["change", "change", "sustain", "sustain"] * 3)
        self.models = {"coach": coach, "talk": talk}

    def kinds(self, tags):
        return {(t.line_idx, t.kind): (t.label, t.method) for t in tags}

    def test_no_weights_means_pure_rules(self):
        from src.tagger.rules import tag_conversation
        tags = tag_conversation(self.conv, models=None)
        self.assertTrue(all(t.method == "rule" for t in tags))

    def test_classifier_used_when_present_but_rules_keep_specific_moves(self):
        from src.tagger.rules import tag_conversation
        k = self.kinds(tag_conversation(self.conv, models=self.models))
        self.assertEqual(k[(0, "coach_move")][1], "classifier")
        self.assertEqual(k[(2, "coach_move")], ("persuade", "rule"))
        self.assertEqual(k[(1, "participant_talk")][1], "classifier")

    def test_env_opt_in_and_absent_files_fall_back(self):
        import os
        from src.tagger import rules
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(rules.load_models(d))
            self.models["coach"].save(Path(d) / "classifier_coach.json")
            os.environ[rules.CLASSIFIER_DIR_ENV] = d
            try:
                loaded = rules.load_models()
                self.assertEqual(set(loaded), {"coach"})
                tags = rules.tag_conversation(self.conv)
                self.assertEqual(self.kinds(tags)[(0, "coach_move")][1], "classifier")
                self.assertEqual(self.kinds(tags)[(1, "participant_talk")][1], "rule")
            finally:
                del os.environ[rules.CLASSIFIER_DIR_ENV]

    def test_flagger_ignores_classifier(self):
        from src.flagger.rules import flag_conversation
        flags = flag_conversation(self.conv)
        self.assertEqual([f.rule_id for f in flags], ["F-CHEST"])


class Context(unittest.TestCase):
    def test_context_features_used_only_when_trained_with_context(self):
        texts = ["mm", "mm", "mm", "mm"] * 3
        ctx = [("how do you feel", "ok"), ("did you walk", "ok"), ("it sounds like", "yeah"), ("you feel", "yeah")] * 3
        labels = ["answer_q", "answer_q", "after_refl", "after_refl"] * 3
        with_ctx = NaiveBayes().fit(texts, labels, ctx)
        self.assertEqual(with_ctx.predict("mm", ("it sounds like", "yeah")), "after_refl")
        self.assertEqual(with_ctx.predict("mm", ("how do you feel", "ok")), "answer_q")
        plain = NaiveBayes().fit(texts, labels)
        self.assertFalse(plain.use_context)
        plain.predict("mm", ("anything", "else"))  # context ignored, no error
        with tempfile.TemporaryDirectory() as d:
            with_ctx.save(Path(d) / "m.json")
            self.assertTrue(NaiveBayes.load(Path(d) / "m.json").use_context)

    def test_train_script_context_flag_selftest(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(ct.main(["--selftest", "--context"]), 0)
        self.assertIn("neighbouring-line words", buf.getvalue())
        self.assertNotIn("Monday", buf.getvalue())


class OutputSymlinks(unittest.TestCase):
    def test_save_refuses_symlink_and_repo_paths(self):
        from src.safe_paths import AdapterError, REPO
        m = NaiveBayes().fit(["a b", "c d"], ["x", "y"])
        with tempfile.TemporaryDirectory() as d:
            target = REPO / "tmp_weights_should_not_exist.json"
            link = Path(d) / "classifier_coach.json"
            link.symlink_to(target)
            with self.assertRaises(AdapterError):
                m.save(link)
            self.assertFalse(target.exists())
            with self.assertRaises(AdapterError):
                m.save(REPO / "x.json")

    def test_prediction_writers_refuse_symlinks(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            target = ea.REPO / "tmp_pred_should_not_exist.csv"
            (out / "coach_all_predictions.csv").symlink_to(target)
            with self.assertRaises(ea.AdapterError):
                ea._write_pair(out, "coach_all", [("s", 1, "a", "b", {})])
            self.assertFalse(target.exists())

    def test_symlinked_output_folder_into_repo_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            link = Path(d) / "out"
            link.symlink_to(ea.REPO)
            with self.assertRaises(ea.AdapterError):
                ea._safe_out(link)


class LanguageGate(unittest.TestCase):
    def test_classifier_not_used_on_spanish(self):
        from src.schema import Conversation
        from src.tagger.rules import tag_conversation
        conv = Conversation.from_dict({"id": "es", "channel": "call", "language": "es", "lines": [
            {"idx": 0, "speaker": "coach", "text": "¿Cómo te sientes hoy?"},
            {"idx": 1, "speaker": "participant", "text": "Bien."}]})
        m = NaiveBayes().fit(["how are you", "did you walk"] * 3, ["question_closed", "question_closed"] * 3)
        tags = tag_conversation(conv, models={"coach": m, "talk": m})
        self.assertTrue(all(t.method == "rule" for t in tags))
        self.assertEqual(tags[0].label, "open_question")
