import unittest
from pathlib import Path

from src.flagger.rules import flag_conversation, is_negated
from src.loader import load_conversations
from src.tagger.rules import tag_conversation

FX = Path(__file__).parent / "fixtures"
BASE = {c.id: c for c in load_conversations(FX / "conversations.json")}
FLAGS = {c.id: c for c in load_conversations(FX / "flag_cases.json")}


def labels(tags, idx):
    return {t.label for t in tags if t.line_idx == idx}


class Tagger(unittest.TestCase):
    def test_english(self):
        t = tag_conversation(BASE["fx-en-1"])
        self.assertIn("open_question", labels(t, 2 - 2) | labels(t, 0))
        self.assertIn("affirmation", labels(t, 2))
        self.assertIn("reflection", labels(t, 4))
        self.assertIn("ask_permission", labels(t, 4))
        self.assertIn("change_talk", labels(t, 1))
        self.assertIn("sustain_talk", labels(t, 1))

    def test_spanish(self):
        t = tag_conversation(BASE["fx-es-1"])
        self.assertIn("open_question", labels(t, 0))
        self.assertIn("affirmation", labels(t, 2))
        self.assertIn("reflection", labels(t, 4))
        self.assertIn("ask_permission", labels(t, 4))
        self.assertIn("change_talk", labels(t, 1))
        self.assertIn("sustain_talk", labels(t, 1))

    def test_tags_are_rule_method_with_rule_id(self):
        for c in BASE.values():
            for t in tag_conversation(c):
                self.assertEqual(t.method, "rule")
                self.assertTrue(t.rule_id)

    def test_speaker_scoping(self):
        t = tag_conversation(BASE["fx-en-1"])
        self.assertFalse(any(x.kind == "coach_move" and x.line_idx % 2 == 1 for x in t))


class Flagger(unittest.TestCase):
    def test_english_positive_unhandled(self):
        f = flag_conversation(FLAGS["fx-en-flag"])
        self.assertEqual([(x.tier, x.rule_id, x.line_idx, x.coach_responded) for x in f], [("S1", "F-CHEST", 1, False)])
        self.assertIn("chest pain", f[0].quote)

    def test_english_negated_not_flagged(self):
        self.assertEqual(flag_conversation(FLAGS["fx-en-neg"]), [])

    def test_spanish_positive_handled(self):
        f = flag_conversation(FLAGS["fx-es-flag"])
        self.assertEqual([(x.rule_id, x.coach_responded, x.negation_checked) for x in f], [("F-CHEST", True, True)])

    def test_spanish_negated_not_flagged(self):
        self.assertEqual(flag_conversation(FLAGS["fx-es-neg"]), [])

    def test_coach_lines_never_flag(self):
        f = flag_conversation(FLAGS["fx-es-flag"])
        self.assertTrue(all(x.line_idx == 1 for x in f))

    def test_negation_window(self):
        self.assertTrue(is_negated("no tengo dolor de pecho", 10, "es"))
        self.assertFalse(is_negated("No me siento bien. Tengo fiebre", 24, "es"))

    def test_unhandled_sorts_first_within_tier(self):
        from src.schema import Conversation
        c = Conversation.from_dict({"id": "x", "channel": "text", "language": "en", "lines": [
            {"idx": 0, "speaker": "participant", "text": "I have chest pain."},
            {"idx": 1, "speaker": "coach", "text": "Thanks for telling me."},
            {"idx": 2, "speaker": "participant", "text": "Now I cannot breathe, shortness of breath."}]})
        f = flag_conversation(c)
        self.assertEqual([x.line_idx for x in f], [2, 0])


if __name__ == "__main__":
    unittest.main()
