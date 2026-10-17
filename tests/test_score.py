import unittest
from pathlib import Path

from src.loader import load_conversations
from src.score.card import score_conversation

FX = Path(__file__).parent / "fixtures"
BASE = {c.id: c for c in load_conversations(FX / "conversations.json")}
FLAGS = {c.id: c for c in load_conversations(FX / "flag_cases.json")}


class Score(unittest.TestCase):
    def test_english_counts_and_checklist(self):
        s = score_conversation(BASE["fx-en-1"])
        c = s["counts"]
        self.assertEqual(c["mi_consistent_share"]["den"], 3)
        self.assertEqual(c["open_question_share"], {"num": 1, "den": 1, "lines": [0]})
        self.assertEqual(c["mi_inconsistent"]["num"], 0)
        self.assertEqual(s["checklist"]["checked_feelings"]["value"], "yes")
        self.assertEqual(s["checklist"]["checked_feelings"]["evidence_lines"], [0])
        self.assertEqual(s["checklist"]["summarized"]["value"], "no")
        self.assertEqual(s["checklist"]["safety_issue_handled"]["value"], "n/a")

    def test_spanish_checklist(self):
        s = score_conversation(BASE["fx-es-1"])
        self.assertEqual(s["checklist"]["checked_feelings"]["value"], "yes")
        self.assertEqual(s["checklist"]["set_new_goal"]["value"], "yes")

    def test_safety_item(self):
        self.assertEqual(score_conversation(FLAGS["fx-en-flag"])["checklist"]["safety_issue_handled"]["value"], "no")
        self.assertEqual(score_conversation(FLAGS["fx-es-flag"])["checklist"]["safety_issue_handled"]["value"], "yes")
        self.assertEqual(score_conversation(FLAGS["fx-es-neg"])["checklist"]["safety_issue_handled"]["value"], "n/a")

    def test_shape_matches_contract(self):
        s = score_conversation(BASE["fx-en-1"])
        self.assertEqual(set(s), {"conv_id", "counts", "checklist"})
        for v in s["counts"].values():
            self.assertEqual(set(v), {"num", "den", "lines"})
            self.assertLessEqual(v["num"], max(v["den"], 0))
        self.assertEqual(len(s["checklist"]), 8)

    def test_no_division_needed(self):
        s = score_conversation(FLAGS["fx-en-flag"])
        self.assertEqual(s["counts"]["reflection_to_question"]["den"], 1)


if __name__ == "__main__":
    unittest.main()


class SafetyEvidence(unittest.TestCase):
    def conv(self, coach):
        from src.schema import Conversation
        return Conversation.from_dict({"id": "s", "channel": "text", "language": "en", "lines": [
            {"idx": 0, "speaker": "participant", "text": "I have chest pain."},
            {"idx": 1, "speaker": "coach", "text": coach}]})

    def test_unrelated_reply_is_not_handled(self):
        r = score_conversation(self.conv("Anyway, how was your weekend?"))["checklist"]["safety_issue_handled"]
        self.assertEqual(r["value"], "no")

    def test_handled_includes_response_line_as_evidence(self):
        r = score_conversation(self.conv("I'm sorry, I will call the nurse now."))["checklist"]["safety_issue_handled"]
        self.assertEqual(r, {"value": "yes", "evidence_lines": [0, 1]})
