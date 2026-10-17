"""Run the flagger ONCE on a blind set of invented sentences written separately from the rules.

    python3 -m src.blind_eval <blind_set.json> <results.json>

The blind file itself is never copied into the repo. Only the counts and the missed or falsely flagged sentences
(plain invented text) are written to the results file. The rules must be frozen before this runs; tuning after seeing
the numbers burns the blind set.
"""
import json
import sys
from datetime import datetime

from . import safety_eval


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 2:
        print(__doc__)
        return 2
    blind, out = argv
    r = safety_eval.run(blind)
    keep = ("scope", "calls", "flags_raised", "correct_catches", "misses", "false_alarms", "recall", "s1_recall",
            "false_alarms_per_10_calls", "by_language")
    res = {k: r[k] for k in keep}
    res["scope"] = "Blind set of invented sentences, written separately from the rules and run once. Invented text only; not real data."
    res["run_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    res["misses_list"] = [{"language": x["language"], "text": x["text"], "gold_tier": x["gold_tier"]} for x in r["misses_list"]]
    res["false_alarms_list"] = [{"language": x["language"], "text": x["text"]} for x in r["false_alarms_list"]]
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if not k.endswith("_list")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
