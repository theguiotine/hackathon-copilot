"""Expanded flag variants (Sat Oct 17 2026): invented phrases only. Every positive must flag S1 with the right rule;
every negated or not-about-now decoy must NOT flag. The output stays "a person should see this today", never a diagnosis."""
import unittest

from src.flagger.rules import flag_conversation
from src.schema import Conversation


def flags_for(text, lang="en"):
    conv = Conversation.from_dict({"id": "t", "channel": "text", "language": lang,
                                   "lines": [{"idx": 0, "speaker": "participant", "text": text}]})
    return flag_conversation(conv)


CHEST_EN = ["I'm having chest pains at night", "chest pains again this morning", "I have pains in my chest",
            "there is a pain in my chest", "I have a tight chest", "I feel pressure on my chest",
            "my heart is racing and hurts", "my heart hurts when I walk"]
BREATH_EN = ["it is hard to breathe", "I'm short of breath on the stairs", "I can't catch my breath",
             "I'm gasping for air", "breathing is hard tonight", "I have a hard time breathing"]
DYING_EN = ["I'm dying", "I think I am dying", "I'm going to die", "I want to die", "I feel like ending it all",
            "I want to end it all", "I don't want to be here anymore", "everyone would be better off without me",
            "I want to disappear", "I keep thinking about taking my own life", "I keep thinking about hurting myself"]
PILLS_EN = ["I took too many pills", "I swallowed a bunch of pills", "I overdosed", "I took a handful of pills",
            "I took all my pills at once", "I took all my pills tonight on purpose"]
ES = ["me estoy muriendo", "quiero morir", "quiero acabar con todo", "no quiero vivir", "me duele el pecho",
      "dolor de pecho", "presión en el pecho", "me falta el aire", "tomé muchas pastillas",
      "me tomé todas las pastillas de golpe", "tengo dolores en el pecho", "me voy a morir"]

NEG_CHEST = ["no chest pain", "I've never had chest pains", "no pains in my chest", "I don't have a tight chest",
             "my mother had chest pains last year", "without any pressure on my chest"]
NEG_BREATH = ["I'm not short of breath", "it isn't hard to breathe, no trouble", "no gasping at all",
              "never had trouble breathing", "my dad was short of breath last winter", "I don't have a hard time breathing"]
NEG_DYING = ["I'm not dying", "I am not going to hurt myself", "I don't feel like ending it all, honestly no",
             "my plant is dying", "I never want to die", "years ago I wanted to disappear but not anymore", "I would never think about hurting myself"]
NEG_PILLS = ["I didn't take too many pills", "I took all my pills this week", "I take my pills every morning",
             "I never took too many pills", "my friend overdosed years ago", "no overdose, I checked the label"]
NEG_ES = ["no me duele el pecho", "sin dolor en el pecho", "no me estoy muriendo", "nunca he tenido dolores de pecho",
          "me tomé todas las pastillas esta semana", "mi mamá tuvo dolor de pecho el año pasado"]


class ExpansionTests(unittest.TestCase):
    def _all_flag(self, phrases, lang="en"):
        for p in phrases:
            fs = flags_for(p, lang)
            self.assertTrue(fs, f"expected a flag: id-less phrase index {phrases.index(p)}")
            self.assertEqual(fs[0].tier, "S1")

    def _none_flag(self, phrases, lang="en"):
        for p in phrases:
            self.assertEqual(flags_for(p, lang), [], f"false alarm: decoy index {phrases.index(p)}")

    def test_chest_variants_flag(self): self._all_flag(CHEST_EN)
    def test_breathing_variants_flag(self): self._all_flag(BREATH_EN)
    def test_dying_variants_flag(self): self._all_flag(DYING_EN)
    def test_overdose_variants_flag(self): self._all_flag(PILLS_EN)
    def test_spanish_variants_flag(self): self._all_flag(ES, "es")

    def test_chest_decoys_do_not_flag(self): self._none_flag(NEG_CHEST)
    def test_breathing_decoys_do_not_flag(self): self._none_flag(NEG_BREATH)
    def test_dying_decoys_do_not_flag(self): self._none_flag(NEG_DYING)
    def test_overdose_decoys_do_not_flag(self): self._none_flag(NEG_PILLS)
    def test_spanish_decoys_do_not_flag(self): self._none_flag(NEG_ES, "es")


if __name__ == "__main__":
    unittest.main()
