"""Train and evaluate the local classifier on the AnnoMI CSV; prints ONLY aggregates.

Run locally by the owner (never in an AI tool):
    python3 -m src.train_annomi             # needs COACH_ANNOMI_CSV (or --csv) and COACH_OUT_DIR
    python3 -m src.train_annomi --selftest  # fictional data only
    python3 -m src.train_annomi --cv        # 5-fold cross-validation: mean and range, no weights saved

Session-level split (see classifier.split_sessions): no line of a test session is used for training.
Reports the rules baseline and the classifier on the SAME held-out sessions. Weights go to the output folder
OUTSIDE the repo (COACH_OUT_DIR, required); the repo is refused.
"""
import argparse
import csv
import hashlib
import os
import random
import sys
import tempfile
from pathlib import Path

from . import eval_annomi as ea
from .classifier import NaiveBayes, split_sessions
import metrics  # noqa: E402  (eval/metrics.py; eval_annomi put eval/ on sys.path)

FOLDS = 5


def neighbours(sessions):
    """{(session, line_number): (previous_text, next_text)} from the transcript order (texts only)."""
    out = {}
    for sid, rows in sessions.items():
        for i, r in enumerate(rows):
            prev = rows[i - 1]["text"] if i > 0 else ""
            nxt = rows[i + 1]["text"] if i + 1 < len(rows) else ""
            out[(sid, r["_n"])] = (prev or "", nxt or "")
    return out


def datasets(sessions):
    """{task: [(session, line_number, text, gold, rules_pred, row, context)]} for coach moves and client talk."""
    coach, talk, _ = ea.analyze(sessions)  # (sid, n, rules_pred, gold, row)
    near = neighbours(sessions)
    out = {}
    for name, pairs in (("coach", coach), ("talk", talk)):
        out[name] = [(sid, n, (row["text"] or "").strip() or "(blank)", gold, pred, row, near[(sid, n)])
                     for sid, n, pred, gold, row in pairs]
    return out


def evaluate(sessions, out_dir, use_context=False):
    out = ea._safe_out(out_dir)
    train_ids, test_ids = split_sessions(sessions)
    assert not (train_ids & test_ids)
    lines = [f"Classifier features: words and bigrams{' + neighbouring-line words (--context)' if use_context else ''}",
             f"Sessions: {len(sessions)} (train {len(train_ids)}, held-out test {len(test_ids)}; split by session id hash, no overlap)", ""]
    for name, title in (("coach", "COACH MOVES (coarse AnnoMI set)"), ("talk", "CLIENT TALK")):
        rows = datasets(sessions)[name]
        train = [r for r in rows if r[0] in train_ids]
        test = [r for r in rows if r[0] in test_ids]
        if not train or not test:
            lines += [f"== {title}: not enough labeled lines on both sides of the split ==", ""]
            continue
        model = NaiveBayes().fit([r[2] for r in train], [r[3] for r in train],
                                 [r[6] for r in train] if use_context else None)
        model.save(out / f"classifier_{name}.json")
        clf_pairs = [(r[0], r[1], model.predict(r[2], r[6]), r[3], r[5]) for r in test]
        rules_pairs = [(r[0], r[1], r[4], r[3], r[5]) for r in test]
        full = [(a, b) for a, b in zip(rules_pairs, clf_pairs)
                if str(a[4].get("expert_raters", "")).strip().split(".")[0] == ea.EXPERT_FULL]
        views = [("all held-out", rules_pairs, clf_pairs)]
        if full:
            views.append((f"expert_raters == {ea.EXPERT_FULL}", [a for a, _ in full], [b for _, b in full]))
        for scope, rp, cp in views:
            for label, pairs in (("RULES baseline", rp), ("CLASSIFIER", cp)):
                acc = sum(1 for q in pairs if q[2] == q[3]) / len(pairs)
                lines += [f"######## {title}: {label}, {scope} ({len(pairs)} lines): accuracy {acc:.3f} ########",
                          ea.run_eval.format_report(*ea._write_pair(
                              out, f"{name}_test_{label.split()[0].lower()}_{scope.split()[0]}", pairs)), ""]
            if scope != "all held-out":
                ceil = ea._mean_agreement(cp)
                lines += [f"Expert agreement ceiling on these lines (mean expert_agreement_pct): "
                          f"{'n/a' if ceil is None else format(ceil, '.1f')}", ""]
    lines.append(f"Weights saved to {out} (outside the repo; never commit them). Not wired into the pipeline.")
    return "\n".join(lines)


def fold_of(session_id, folds=FOLDS):
    """Fold number 0..folds-1 from sha1(session_id) mod folds: whole sessions stay together, deterministic."""
    return int(hashlib.sha1(str(session_id).encode("utf-8")).hexdigest(), 16) % folds


def _spread(values):
    return f"mean {sum(values) / len(values):.3f} (min {min(values):.3f}, max {max(values):.3f})"


def cross_validate(sessions, use_context=False, folds=FOLDS):
    """5-fold cross-validation for coach moves and client talk. For each fold: train on the other folds' sessions,
    test on the held-out fold's sessions (no session in both). Prints mean and range per metric, aggregates only.
    Weights are NOT saved here (no output folder is needed)."""
    lines = [f"{folds}-fold cross-validation, folds = sha1(session_id) mod {folds}; features: words and bigrams"
             f"{' + neighbouring-line words (--context)' if use_context else ''}",
             f"Sessions: {len(sessions)}", ""]
    for name, title in (("coach", "COACH MOVES (coarse AnnoMI set)"), ("talk", "CLIENT TALK")):
        rows = datasets(sessions)[name]
        acc, f1, kap, base_acc, sizes = [], [], [], [], []
        for k in range(folds):
            train = [r for r in rows if fold_of(r[0], folds) != k]
            test = [r for r in rows if fold_of(r[0], folds) == k]
            assert not ({r[0] for r in train} & {r[0] for r in test})
            if not train or not test:
                continue
            model = NaiveBayes().fit([r[2] for r in train], [r[3] for r in train],
                                     [r[6] for r in train] if use_context else None)
            gold = [r[3] for r in test]
            pred = [model.predict(r[2], r[6]) for r in test]
            acc.append(sum(1 for g, p in zip(gold, pred) if g == p) / len(test))
            f1.append(metrics.macro_f1(gold, pred))
            kap.append(metrics.cohen_kappa(gold, pred))
            base_acc.append(sum(1 for r in test if r[3] == r[4]) / len(test))
            sizes.append(len(test))
        if not acc:
            lines += [f"== {title}: not enough labeled lines for cross-validation ==", ""]
            continue
        lines += [f"######## {title}: {len(acc)} of {folds} folds had data (test lines per fold: {min(sizes)} to {max(sizes)}) ########",
                  f"CLASSIFIER accuracy  {_spread(acc)}",
                  f"CLASSIFIER macro F1  {_spread(f1)}",
                  f"CLASSIFIER kappa     {_spread(kap)}",
                  f"RULES baseline accuracy on the same folds  {_spread(base_acc)}", ""]
    return "\n".join(lines)


def build_selftest_csv(path, n_sessions=40, seed=3):
    """Invented, tiny AnnoMI-shaped CSV with enough sessions for a split (fictional lines only)."""
    rng = random.Random(seed)
    coach_lines = [
        ("How have you been feeling about your walks?", "question", "open", ""),
        ("What helped you get out the door?", "question", "open", ""),
        ("Did you walk on Monday?", "question", "closed", ""),
        ("Are you free on Sunday?", "question", "closed", ""),
        ("It sounds like company matters to you.", "reflection", "", "simple"),
        ("You feel tired but you still want to try.", "reflection", "", "complex"),
        ("You should walk every day.", "information-or-advice", "", ""),
        ("One option is a short walk after dinner.", "information-or-advice", "", ""),
        ("Okay, thanks for sharing.", "other", "", ""),
    ]
    client_lines = [("I want to walk on Sunday.", "change"), ("I will try Tuesday.", "change"),
                    ("I am too tired, I can't.", "sustain"), ("I have no time this week.", "sustain"),
                    ("Okay.", "neutral"), ("It was fine.", "neutral")]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(ea.REQUIRED)
        for s in range(n_sessions):
            n = 0
            for _ in range(4):
                n += 1
                t, mv, qt, rt = rng.choice(coach_lines)
                w.writerow([f"sess{s}", n, "counsellor", t, mv, qt, rt, "", "10", "90"])
                n += 1
                t, talk = rng.choice(client_lines)
                w.writerow([f"sess{s}", n, "client", t, "", "", "", talk, "10", "90"])


def main(argv=None):
    ap = argparse.ArgumentParser(description="Train/evaluate the local classifier; aggregates only.")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--csv")
    ap.add_argument("--context", action="store_true", help="add previous/next line words as features")
    ap.add_argument("--cv", action="store_true", help="5-fold cross-validation (mean and range); needs no output folder")
    args = ap.parse_args(argv)
    try:
        if args.selftest:
            with tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp) / "selftest.csv"
                build_selftest_csv(p)
                if args.cv:
                    print(cross_validate(ea.read_sessions(p), args.context))
                else:
                    print(evaluate(ea.read_sessions(p), Path(tmp) / "out", args.context))
            return 0
        if args.cv:
            print(cross_validate(ea.read_sessions(ea.resolve_csv(args.csv)), args.context))
            return 0
        print(evaluate(ea.read_sessions(ea.resolve_csv(args.csv)), ea.resolve_out(), args.context))
        return 0
    except (ea.AdapterError, ea.SchemaError, ValueError, OSError) as e:
        print(f"error: {e.__class__.__name__}: {e if isinstance(e, ea.AdapterError) else 'no row content shown'}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
