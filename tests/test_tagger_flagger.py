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

    def test_feeling_question_is_a_question_not_a_reflection(self):
        self.assertIn(("coach_move", "open_question"), one("¿Cómo te sientes hoy?", lang="es"))
        self.assertIn(("coach_move", "open_question"), one("How are you feeling today?"))
        self.assertIn(("coach_move", "simple_reflection"), one("Te sientes cansada. ¿Qué ayudaría?", lang="es"))

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
            {"idx": 1, "speaker": "coach", "text": "I am sorry, I will call the nurse now."},
            {"idx": 2, "speaker": "participant", "text": "Now I cannot breathe, shortness of breath."}]})
        self.assertEqual([x.line_idx for x in flag_conversation(c)], [2, 0])


if __name__ == "__main__":
    unittest.main()


def conv_of(lines, lang="es"):
    return Conversation.from_dict({"id": "r", "channel": "text", "language": lang, "lines": [
        {"idx": i, "speaker": s, "text": t} for i, (s, t) in enumerate(lines)]})


class ReviewFixes(unittest.TestCase):
    def rules(self, lines, lang="es"):
        return [f.rule_id for f in flag_conversation(conv_of(lines, lang))]

    def test_no_puedo_respirar_positive(self):
        self.assertEqual(self.rules([("participant", "No puedo respirar")]), ["F-CHEST"])
        self.assertEqual(self.rules([("participant", "No, no puedo respirar bien")]), ["F-CHEST"])
        self.assertEqual(self.rules([("participant", "No sé qué hacer, no puedo respirar")]), ["F-CHEST"])

    def test_no_puedo_mas_positive(self):
        self.assertEqual(self.rules([("participant", "Ya no puedo más")]), ["F-DISTRESS"])

    def test_denied_then_current_symptom(self):
        self.assertEqual(self.rules([("participant", "No chest pain yesterday; I have chest pain now")], "en"), ["F-CHEST"])
        self.assertEqual(self.rules([("participant", "No tenía dolor de pecho ayer, pero hoy tengo dolor de pecho")]), ["F-CHEST"])

    def test_later_clause_not_suppressed(self):
        self.assertEqual(self.rules([("participant", "No fever, but I have chest pain")], "en"), ["F-CHEST"])
        self.assertEqual(self.rules([("participant", "No tengo fiebre pero tengo dolor de pecho")]), ["F-CHEST"])

    def test_negation_still_works_same_clause(self):
        self.assertEqual(self.rules([("participant", "No tengo dolor de pecho ni fiebre")]), [])
        self.assertEqual(self.rules([("participant", "I have no fever and no chest pain")], "en"), [])

    def test_questions_without_punctuation(self):
        self.assertIn(("coach_move", "open_question"), one("How have you been feeling"))
        self.assertIn(("coach_move", "open_question"), one("Cómo te has sentido", lang="es"))
        self.assertIn(("coach_move", "closed_question"), one("Did you walk on Monday"))
        self.assertIn(("coach_move", "other"), one("Do not worry about it."))

    def test_unrelated_coach_line_is_not_a_response(self):
        f = flag_conversation(conv_of([("participant", "I have chest pain."), ("coach", "Anyway, how was your weekend?")], "en"))
        self.assertFalse(f[0].coach_responded)
        f = flag_conversation(conv_of([("participant", "I have chest pain."), ("coach", "I'm sorry, I will call the nurse team now.")], "en"))
        self.assertTrue(f[0].coach_responded)


class Round2(unittest.TestCase):
    def resp(self, lines, lang="en"):
        return [f.coach_responded for f in flag_conversation(conv_of(lines, lang))]

    def test_generic_intent_is_not_a_response(self):
        self.assertEqual(self.resp([("participant", "I have chest pain."), ("coach", "I will send your walking plan tomorrow.")]), [False])
        self.assertEqual(self.resp([("participant", "Tengo dolor de pecho."), ("coach", "Voy a enviarte el plan de caminata.")], "es"), [False])

    def test_spanish_stems_match_full_words(self):
        self.assertEqual(self.resp([("participant", "No puedo respirar"), ("coach", "Llama al médico ahora")], "es"), [True])
        self.assertEqual(self.resp([("participant", "No puedo respirar"), ("coach", "La enfermera te llamará")], "es"), [True])

    def test_response_after_a_clarifying_question(self):
        lines = [("participant", "I have chest pain."), ("coach", "How long has this been happening?"),
                 ("participant", "Since this morning."), ("coach", "I will call the nurse now.")]
        self.assertEqual(self.resp(lines), [True])
        from src.score.card import score_conversation
        ev = score_conversation(conv_of(lines, "en"))["checklist"]["safety_issue_handled"]
        self.assertEqual(ev, {"value": "yes", "evidence_lines": [0, 3]})

    def test_comma_separated_denials(self):
        self.assertEqual([f.rule_id for f in flag_conversation(conv_of([("participant", "No tengo fiebre, vómitos ni sangrado")]))], [])
        self.assertEqual([f.rule_id for f in flag_conversation(conv_of([("participant", "No fever, vomiting or bleeding")], "en"))], [])

    def test_comma_then_new_clause_still_flags(self):
        self.assertEqual([f.rule_id for f in flag_conversation(conv_of([("participant", "No tengo fiebre, tengo vómitos")]))], ["F-SYMPTOM"])
        self.assertEqual([f.rule_id for f in flag_conversation(conv_of([("participant", "No fever, I have vomiting")], "en"))], ["F-SYMPTOM"])
