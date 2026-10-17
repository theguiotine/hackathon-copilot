import unittest
from pathlib import Path

from src.flagger.rules import flag_conversation, is_negated
from src.loader import load_conversations
from src.schema import Conversation
from src.tagger.rules import tag_conversation

FX = Path(__file__).parent / "fixtures"
BASE = {c.id: c for c in load_conversations(FX / "conversations.json")}
FLAGS = {c.id: c for c in load_conversations(FX / "flag_cases.json")}


def one(text, speaker="coach", lang="en", channel="call"):
    c = Conversation.from_dict({"id": "t", "channel": channel, "language": lang,
                                "lines": [{"idx": 0, "speaker": speaker, "text": text}]})
    return [(t.kind, t.label) for t in tag_conversation(c)]


class Tagger(unittest.TestCase):
    def test_english_moves(self):
        self.assertIn(("coach_move", "open_question"), one("How have you been feeling about your walks?"))
        self.assertIn(("coach_move", "closed_question"), one("Did you walk on Monday?"))
        self.assertIn(("coach_move", "affirm"), one("Three walks is a real win."))
        self.assertIn(("coach_move", "simple_reflection"), one("It sounds like company matters."))
        self.assertIn(("coach_move", "complex_reflection"), one("It sounds like you want to walk but evenings feel heavy because of work."))
        self.assertIn(("coach_move", "ask_permission"), one("Would you like to plan one more walk?"))
        self.assertIn(("coach_move", "persuade"), one("You should walk every day."))
        self.assertIn(("coach_move", "emphasize_autonomy"), one("It's up to you how often."))
        self.assertIn(("coach_move", "other"), one("Okay."))

    def test_spanish_moves(self):
        self.assertIn(("coach_move", "open_question"), one("¿Cómo te has sentido con tus caminatas?", lang="es"))
        self.assertIn(("coach_move", "closed_question"), one("¿Caminaste el lunes? ¿Has salido?", lang="es"))
        self.assertIn(("coach_move", "affirm"), one("Tres caminatas es un gran logro.", lang="es"))
        self.assertIn(("coach_move", "simple_reflection"), one("Parece que la compañía te importa.", lang="es"))
        self.assertIn(("coach_move", "persuade"), one("Deberías caminar todos los días.", lang="es"))
        self.assertIn(("coach_move", "ask_permission"), one("¿Te gustaría planear otra caminata?", lang="es"))

    def test_participant_talk(self):
        self.assertIn(("participant_talk", "change"), one("I want to walk on Sunday.", "participant"))
        self.assertIn(("participant_talk", "sustain"), one("I'm too tired, I can't.", "participant"))
        self.assertIn(("participant_talk", "neutral"), one("Okay.", "participant"))
        self.assertIn(("participant_talk", "sustain"), one("Estaba muy cansada.", "participant", "es"))

    def test_one_move_per_line_and_rule_ids(self):
        for c in BASE.values():
            tags = tag_conversation(c)
            keyed = [(t.line_idx, t.kind) for t in tags if t.kind != "text_intent"]
            self.assertEqual(len(keyed), len(set(keyed)))
            self.assertEqual(len(keyed), len(c.lines))
            self.assertTrue(all(t.method == "rule" and t.rule_id for t in tags))

    def test_text_intent_only_on_text_channel(self):
        self.assertIn(("text_intent", "thanks"), one("Thanks!", "participant", channel="text"))
        self.assertNotIn(("text_intent", "thanks"), one("Thanks!", "participant", channel="call"))
        self.assertIn(("text_intent", "reminder"), one("Recordatorio: no olvides tu caminata.", lang="es", channel="text"))


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

    def test_negation_window(self):
        self.assertTrue(is_negated("no tengo dolor de pecho", 10, "es"))
        self.assertFalse(is_negated("No me siento bien. Tengo fiebre", 24, "es"))

    def test_unhandled_sorts_first_within_tier(self):
        c = Conversation.from_dict({"id": "x", "channel": "text", "language": "en", "lines": [
            {"idx": 0, "speaker": "participant", "text": "I have chest pain."},
            {"idx": 1, "speaker": "coach", "text": "Thanks for telling me."},
            {"idx": 2, "speaker": "participant", "text": "Now I cannot breathe, shortness of breath."}]})
        self.assertEqual([x.line_idx for x in flag_conversation(c)], [2, 0])


if __name__ == "__main__":
    unittest.main()
