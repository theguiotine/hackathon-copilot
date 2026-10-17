import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("gen", ROOT / "scripts" / "gen_ui_fixtures.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


class UiFixtures(unittest.TestCase):
    def test_demo_calls_cover_tiers_and_denials(self):
        from src.flagger.rules import flag_conversation
        from src.schema import Conversation
        tiers, quiet = set(), []
        for cid, lines in gen.DEMO.items():
            lang = "es" if cid in ("cc-001", "cc-002", "cc-005", "cc-009") else "en"
            conv = Conversation.from_dict({"id": cid, "channel": "call", "language": lang, "lines": [
                {"idx": i, "speaker": "coach" if w == "C" else "participant", "text": t} for i, (w, t) in enumerate(lines)]})
            flags = flag_conversation(conv)
            tiers |= {f.tier for f in flags}
            if not flags:
                quiet.append(cid)
        self.assertEqual(tiers, {"S1", "S2", "S3"})
        self.assertEqual(set(quiet), {"cc-003", "cc-009", "cc-013"})  # denials and a clean call stay quiet

    def test_committed_fixtures_match_the_engine(self):
        _, flags = gen.parse_array(gen.FX / "humanReviewFlag.fixture.ts")
        _, calls = gen.parse_array(gen.FX / "coachingCall.fixture.ts")
        self.assertEqual(sum(c["flagCount"] for c in calls), len(flags))
        text = (gen.FX / "callLine.fixture.ts").read_text(encoding="utf-8")
        self.assertIn("dolor de pecho", text)
        self.assertEqual(len(set(re.findall(r'id: "(cl-\d+)"', text))), len(re.findall(r'id: "(cl-\d+)"', text)))


if __name__ == "__main__":
    unittest.main()
