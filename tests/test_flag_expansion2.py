"""Second batch (Sat Oct 17 2026, from the live cold test): invented phrases. Tier shown is the existing idea's tier."""
import unittest

from src.flagger.rules import flag_conversation
from src.schema import Conversation


def flags_for(text, lang="en"):
    conv = Conversation.from_dict({"id": "t", "channel": "text", "language": lang,
                                   "lines": [{"idx": 0, "speaker": "participant", "text": text}]})
    return flag_conversation(conv)


MUST_FLAG = [
    ("I'm having chest pains at night", "en", "S1"), ("I have chest pains", "en", "S1"),
    ("I've had tightness in my chest for two days", "en", "S1"), ("I'm dying", "en", "S1"),
    ("I think I am going to die", "en", "S1"), ("Me estoy muriendo", "es", "S1"),
    ("Siento presión en el pecho", "es", "S1"), ("I fell yesterday and my leg is swollen", "en", "S2"),
    ("I have a lot of pain and I can't sleep", "en", "S2"), ("No puedo dormir y me siento muy triste", "es", "S3"),
    ("I feel like ending it all", "en", "S1"), ("I took too many pills", "en", "S1"),
    ("everyone would be better off without me", "en", "S1"), ("they'd be better off without me", "en", "S1"),
    ("my heart is racing and my chest feels tight", "en", "S1"),
    # already hits that must stay hits
    ("my chest hurts when I climb the stairs", "en", "S1"), ("I can't catch my breath", "en", "S1"),
    ("I'm short of breath", "en", "S1"), ("I want to die", "en", "S1"), ("Quiero morirme", "es", "S1"),
    ("I have a fever and chills", "en", "S2"), ("I've been vomiting", "en", "S2"), ("I feel hopeless", "en", "S3"),
    ("Me duele el pecho por las noches", "es", "S1"), ("Siento que me falta el aire", "es", "S1"),
]
MUST_STAY_QUIET = [
    ("no tengo dolor de pecho", "es"), ("no fever", "en"), ("no chest pain", "en"), ("I'm not dying", "en"),
    ("sin dolor", "es"), ("I have no pain and I sleep fine", "en"), ("my leg is not swollen", "en"),
    ("no me siento muy triste", "es"), ("I don't feel very sad", "en"), ("my sister's leg is swollen", "en"),
    ("my mother had chest pains last year", "en"), ("back in college I had chest pains but it was stress", "en"),
    ("I took all my pills this week", "en"), ("it isn't hard to breathe", "en"),
]


class SecondBatch(unittest.TestCase):
    def test_must_flag(self):
        for i, (text, lang, tier) in enumerate(MUST_FLAG):
            fs = flags_for(text, lang)
            self.assertTrue(fs, f"missed index {i}")
            self.assertIn(tier, {f.tier for f in fs}, f"wrong tier index {i}")

    def test_must_stay_quiet(self):
        for i, (text, lang) in enumerate(MUST_STAY_QUIET):
            self.assertEqual(flags_for(text, lang), [], f"false alarm index {i}")


if __name__ == "__main__":
    unittest.main()
