"""Run the seeded synthetic set through the engine and write ONLY aggregates (no sentences).

Usage (from the repo root):  python3 eval/run_synthetic.py [N] [SEED]
Writes eval/synthetic_results.md and eval/synthetic_results.json. Nothing here reads real or challenge data.
"""
import json
import os
import sys
import time
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gen_synthetic import generate  # noqa: E402
from src.flagger.rules import flag_conversation  # noqa: E402
from src.schema import Conversation  # noqa: E402
from src.score.card import score_conversation  # noqa: E402
from src.tagger.rules import tag_conversation  # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 300
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 20261017
RULE = {"CRISIS": "F-CRISIS", "CHEST": "F-CHEST", "SYMPTOM": "F-SYMPTOM", "DISTRESS": "F-DISTRESS"}


def ratio(a, b):
    return round(a / b, 4) if b else None


def main():
    t0 = time.time()
    raw, truth = generate(N, SEED)
    flag_truth = defaultdict(lambda: [0, 0])          # key -> [hit, total]
    pred_by_rule = defaultdict(lambda: [0, 0])        # rule -> [true positive, predicted]
    decoy = defaultdict(lambda: [0, 0])               # key -> [flagged, total]
    missed = Counter()
    coach = defaultdict(lambda: [0, 0])
    miss_variant_rule = Counter()
    n_lines = 0
    score_ok = score_err = 0
    models_used = None
    for d in raw:
        conv = Conversation.from_dict(d)
        lang = conv.language
        flags = flag_conversation(conv)
        tags = tag_conversation(conv)
        try:
            score_conversation(conv)
            score_ok += 1
        except Exception:
            score_err += 1
        by_line = defaultdict(set)
        for f in flags:
            by_line[f.line_idx].add(f.rule_id)
        coach_tag = {t.line_idx: t.label for t in tags if t.kind == "coach_move"}
        for ln in conv.lines:
            n_lines += 1
            tr = truth[conv.id][ln.idx]
            got = by_line.get(ln.idx, set())
            if tr["kind"] == "flag":
                want = RULE[tr["cat"]]
                hit = want in got
                for key in (("all", "all"), ("all", lang), (tr["cat"], "all"), (tr["cat"], lang),
                            ("variant:" + tr["variant"], "all"), ("base_variant:" + tr["base_variant"], "all"),
                            ("base_variant:" + tr["base_variant"] + "|" + tr["cat"], "all")):
                    flag_truth[key][1] += 1
                    flag_truth[key][0] += int(hit)
                if not hit:
                    missed[(tr["tid"], lang)] += 1
                    if tr["base_variant"] in ("plural", "order"):
                        miss_variant_rule[(want, tr["base_variant"])] += 1
            elif tr["kind"] in ("decoy", "neutral"):
                for key in (("all", "all"), ("all", lang), (tr["cat"], "all"), (tr["cat"], lang)):
                    decoy[key][1] += 1
                    decoy[key][0] += int(bool(got))
                if got:
                    missed[("FALSE-ALARM:" + tr["tid"], lang)] += 1
            if tr["kind"] == "coach":
                lab = coach_tag.get(ln.idx)
                for key in ((tr["cat"], "all"), (tr["cat"], lang), ("all", "all"), ("all", lang)):
                    coach[key][1] += 1
                    coach[key][0] += int(lab == tr["cat"])
            for rid in got:
                truth_cat = tr["cat"] if tr["kind"] == "flag" else None
                pred_by_rule[(rid, "all")][1] += 1
                pred_by_rule[(rid, lang)][1] += 1
                if truth_cat and RULE[truth_cat] == rid:
                    pred_by_rule[(rid, "all")][0] += 1
                    pred_by_rule[(rid, lang)][0] += 1
    secs = round(time.time() - t0, 2)
    models_used = bool(os.environ.get("COACH_CLASSIFIER_DIR"))
    out = {
        "seed": SEED, "n_conversations": N, "n_lines": n_lines, "seconds": secs,
        "classifier_dir_env_set": models_used, "score_ok": score_ok, "score_errors": score_err,
        "flag_recall": {f"{k[0]}|{k[1]}": {"hit": v[0], "total": v[1], "recall": ratio(*v)} for k, v in sorted(flag_truth.items())},
        "flag_precision_by_rule": {f"{k[0]}|{k[1]}": {"tp": v[0], "predicted": v[1], "precision": ratio(*v)} for k, v in sorted(pred_by_rule.items())},
        "false_alarm_rate": {f"{k[0]}|{k[1]}": {"flagged": v[0], "total": v[1], "rate": ratio(*v)} for k, v in sorted(decoy.items())},
        "coach_move_recall": {f"{k[0]}|{k[1]}": {"hit": v[0], "total": v[1], "recall": ratio(*v)} for k, v in sorted(coach.items())},
        "missed_template_ids": sorted(([f"{k[0]}|{k[1]}", c] for k, c in missed.items()), key=lambda x: -x[1]),
        "plural_and_word_order_misses_by_rule": {f"{k[0]}|{k[1]}": c for k, c in sorted(miss_variant_rule.items())},
    }
    with open(os.path.join(ROOT, "eval", "synthetic_results.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    with open(os.path.join(ROOT, "eval", "synthetic_results.md"), "w") as fh:
        fh.write("# Synthetic robustness run (aggregates only)\n\n")
        fh.write("**These results come from invented, template-generated text. They are NOT clinical validation, "
                 "and the generator's phrasings can be easier or harder than real speech. No real or challenge data "
                 "was used and no generated sentence is stored here.**\n\n")
        fh.write(f"- seed {SEED}, {N} conversations ({n_lines} lines), run time {secs}s\n")
        fh.write(f"- COACH_CLASSIFIER_DIR set for this process: {models_used} (False means the rule tagger ran alone)\n")
        fh.write(f"- score card ran OK on {score_ok}/{N} conversations, errors {score_err}\n\n")
        for title, key in (("Flag recall (truth flag lines the engine flagged with the right rule)", "flag_recall"),
                           ("Flag precision by rule", "flag_precision_by_rule"),
                           ("False-alarm rate (decoy and neutral lines wrongly flagged)", "false_alarm_rate"),
                           ("Coach-move tag recall", "coach_move_recall")):
            fh.write(f"## {title}\n\n| group | detail |\n|---|---|\n")
            for k, v in out[key].items():
                fh.write(f"| {k} | {json.dumps(v)} |\n")
            fh.write("\n")
        fh.write("## Missed template IDs (id|language, count; FALSE-ALARM: ids are decoys that wrongly flagged)\n\n")
        for k, c in out["missed_template_ids"]:
            fh.write(f"- {k}: {c}\n")
        fh.write("\n## Plural / word-order variant misses by flag rule\n\n")
        for k, c in out["plural_and_word_order_misses_by_rule"].items():
            fh.write(f"- {k}: {c}\n")
    fr = out["flag_recall"]
    fa = out["false_alarm_rate"]
    print("seed", SEED, "N", N, "lines", n_lines, "secs", secs, "score_ok", score_ok, "score_err", score_err, "classifier_env", models_used)
    print("flag recall all", fr["all|all"], " en", fr["all|en"]["recall"], " es", fr["all|es"]["recall"])
    for c in ("CRISIS", "CHEST", "SYMPTOM", "DISTRESS"):
        print(" recall", c, fr[c + "|all"]["recall"], "(n=%d)" % fr[c + "|all"]["total"], "en", fr[c + "|en"]["recall"], "es", fr[c + "|es"]["recall"])
    for k, v in out["flag_precision_by_rule"].items():
        if k.endswith("|all"):
            print(" precision", k, v)
    print("false alarm all", fa["all|all"], " by kind:", {k.split("|")[0]: v["rate"] for k, v in fa.items() if k.endswith("|all") and not k.startswith("all")})
    print("variant recall:", {k: v["recall"] for k, v in fr.items() if k.startswith("base_variant:") and "|" not in k.split(":")[1]})
    print("plural/order misses by rule:", out["plural_and_word_order_misses_by_rule"])
    print("missed ids top:", out["missed_template_ids"][:12])
    print("coach recall all", out["coach_move_recall"]["all|all"]["recall"], " en", out["coach_move_recall"]["all|en"]["recall"], " es", out["coach_move_recall"]["all|es"]["recall"])


if __name__ == "__main__":
    main()
