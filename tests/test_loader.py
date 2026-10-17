import copy
import json
import tempfile
import unittest
from pathlib import Path

from src.loader import load_conversations, parse_conversations
from src.schema import Conversation, Flag, Line, SchemaError, Tag

FX = Path(__file__).parent / "fixtures"


def fx(name):
    return json.loads((FX / name).read_text(encoding="utf-8"))


class FixtureLoad(unittest.TestCase):
    def test_loads_both_languages_six_lines_each(self):
        convs = load_conversations(FX / "conversations.json")
        self.assertEqual({c.language for c in convs}, {"en", "es"})
        for c in convs:
            self.assertEqual(len(c.lines), 6)
            self.assertEqual([l.speaker for l in c.lines], ["coach", "participant"] * 3)

    def test_spanish_accents_preserved(self):
        es = [c for c in load_conversations(FX / "conversations.json") if c.language == "es"][0]
        self.assertIn("¿cómo", es.lines[0].text)

    def test_single_object_accepted(self):
        one = fx("conversations.json")[0]
        self.assertEqual(len(parse_conversations(one)), 1)

    def test_tag_and_flag_fixtures(self):
        self.assertEqual(Tag.from_dict(fx("tag.json")).method, "rule")
        self.assertEqual(Flag.from_dict(fx("flag.json")).tier, "S3")


class Rejects(unittest.TestCase):
    def conv(self):
        return copy.deepcopy(fx("conversations.json")[0])

    def bad(self, mutate):
        c = self.conv()
        mutate(c)
        with self.assertRaises(SchemaError):
            Conversation.from_dict(c)

    def test_bad_channel(self): self.bad(lambda c: c.update(channel="voice"))
    def test_bad_language(self): self.bad(lambda c: c.update(language="fr"))
    def test_missing_key(self): self.bad(lambda c: c.pop("lines"))
    def test_extra_key(self): self.bad(lambda c: c.update(extra=1))
    def test_empty_id(self): self.bad(lambda c: c.update(id=""))
    def test_bad_speaker(self): self.bad(lambda c: c["lines"][0].update(speaker="bot"))
    def test_empty_text(self): self.bad(lambda c: c["lines"][0].update(text="  "))
    def test_idx_gap(self): self.bad(lambda c: c["lines"][2].update(idx=5))
    def test_idx_bool(self): self.bad(lambda c: c["lines"][0].update(idx=True))
    def test_lines_not_list(self): self.bad(lambda c: c.update(lines="x"))

    def test_line_not_object(self):
        with self.assertRaises(SchemaError):
            Line.from_dict("hello")

    def test_duplicate_ids(self):
        c = self.conv()
        with self.assertRaises(SchemaError):
            parse_conversations([c, c])

    def test_top_level_wrong_type(self):
        with self.assertRaises(SchemaError):
            parse_conversations("nope")

    def test_invalid_json_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.json"
            p.write_text("{not json")
            with self.assertRaises(SchemaError):
                load_conversations(p)

    def test_tag_rule_needs_rule_id(self):
        t = fx("tag.json"); del t["rule_id"]
        with self.assertRaises(SchemaError):
            Tag.from_dict(t)

    def test_tag_classifier_without_rule_id_ok(self):
        t = fx("tag.json"); del t["rule_id"]; t["method"] = "classifier"
        self.assertIsNone(Tag.from_dict(t).rule_id)

    def test_flag_bad_tier(self):
        f = fx("flag.json"); f["tier"] = "S4"
        with self.assertRaises(SchemaError):
            Flag.from_dict(f)

    def test_flag_non_bool(self):
        f = fx("flag.json"); f["negation_checked"] = "yes"
        with self.assertRaises(SchemaError):
            Flag.from_dict(f)

    def test_flag_empty_quote(self):
        f = fx("flag.json"); f["quote"] = ""
        with self.assertRaises(SchemaError):
            Flag.from_dict(f)


if __name__ == "__main__":
    unittest.main()
