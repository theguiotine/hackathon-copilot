"""Caught-vs-missed report for the needs-a-human flagger on INVENTED fixtures (tests/fixtures/safety_cases.json).

Every number is computed here by running the real flagger and the row 8 metrics; nothing is typed in. These
figures describe the invented fixtures only, never real data or real performance.
"""
import json
import sys
from pathlib import Path

from .flagger.rules import flag_conversation
from .schema import Conversation

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "eval"))
import metrics  # noqa: E402  (row 8 harness)

DEFAULT = REPO / "tests" / "fixtures" / "safety_cases.json"
COACH_LINE = {"en": "How are you doing today?", "es": "¿Cómo estás hoy?"}


def run(path=DEFAULT):
    cases = json.loads(Path(path).read_text(encoding="utf-8"))["cases"]
    truth, pred, rows = [], [], []
    for c in cases:
        conv = Conversation.from_dict({"id": c["id"], "channel": "text", "language": c["language"], "lines": [
            {"idx": 0, "speaker": "coach", "text": COACH_LINE[c["language"]]},
            {"idx": 1, "speaker": "participant", "text": c["text"]}]})
        flags = flag_conversation(conv)
        should, did = c["gold_tier"] is not None, bool(flags)
        truth.append(should), pred.append(did)
        rows.append({"id": c["id"], "language": c["language"], "text": c["text"], "should_flag": should, "flagged": did,
                     "tier": flags[0].tier if flags else None, "gold_tier": c["gold_tier"],
                     "outcome": "caught" if should and did else "missed" if should else "false alarm" if did else "quiet (correct)"})
    b = metrics.binary_precision_recall(truth, pred)
    s1 = [r for r in rows if r["gold_tier"] == "S1"]
    return {
        "scope": "On invented fixtures only (not real data). The set includes deliberately hard phrasings, so these figures show where the rules fail; they are not a performance claim.",
        "calls": len(cases),
        "flags_raised": sum(pred),
        "correct_catches": b["tp"],
        "misses": b["fn"],
        "false_alarms": b["fp"],
        "recall": round(b["r"], 3),
        "s1_recall": round(sum(1 for r in s1 if r["flagged"]) / len(s1), 3) if s1 else None,
        "false_alarms_per_10_calls": round(10 * b["fp"] / len(cases), 2),
        "misses_list": [r for r in rows if r["outcome"] == "missed"],
        "false_alarms_list": [r for r in rows if r["outcome"] == "false alarm"],
        "quiet_list": [r for r in rows if r["outcome"] == "quiet (correct)"],
        "sentence": "Safety net, not a diagnosis: a human decides. Rule-based negation misses some phrasings; misses are shown, not hidden.",
    }
