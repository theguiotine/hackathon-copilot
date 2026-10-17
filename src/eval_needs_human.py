"""Score our rule flagger (S1-S3) against the organizers' `needs_human` column; prints ONLY aggregates.

Run locally by the owner (never inside an AI tool):
    python3 -m src.eval_needs_human                # reads $COACH_ANNOMI_CSV and, if set, $COACH_TEXT_CSV
    python3 -m src.eval_needs_human --csv A.csv --csv B.csv
    python3 -m src.eval_needs_human --selftest     # fictional fixtures only, no real data

What it does: for every PARTICIPANT line in a file that has a `needs_human` column, run the rule flagger on the
conversation (language per row if the file has a `language` column, else --lang, default en) and compare "line
flagged" with the label (yes/no). Prints lines, positives, precision, recall, F1, false alarms per 100 lines, and
recall counting only S1 flags, overall and split by language when the file carries one.

Expected columns (names only; no data path is baked in): a session id (`session_id` or `call_id`), `line_number`,
`speaker`, `text`, `needs_human`, optional `language`. A file without `needs_human` is reported as skipped.

Privacy rules this file enforces: it never prints a line of text or a row; errors name the problem without echoing
cell contents; with --out (or $COACH_OUT_DIR) it writes predictions and labels to a folder OUTSIDE the repo
and refuses a folder inside the repo. Without --out it writes no files at all.
"""
import argparse
import csv
import os
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

from . import eval_annomi as ea
from .flagger.rules import flag_conversation
from .safe_paths import AdapterError, safe_dest, safe_dir
from .schema import Conversation, SchemaError

import metrics  # noqa: E402  (eval/metrics.py; eval_annomi put eval/ on sys.path)

ENV_TEXT_CSV = "COACH_TEXT_CSV"
YES = {"yes", "y", "true", "1"}
NO = {"no", "n", "false", "0"}
COACH_SPEAKERS = ("counsel", "coach", "therapist", "interviewer", "clinician")


def paths_from_env(args_csv):
    """--csv values if given, else $COACH_ANNOMI_CSV and (if set) $COACH_TEXT_CSV. Nothing is baked into the repo."""
    if args_csv:
        return [Path(p).expanduser() for p in args_csv]
    found = [os.environ.get(k) for k in (ea.ENV_CSV, ENV_TEXT_CSV)]
    found = [Path(v).expanduser() for v in found if v]
    if not found:
        raise AdapterError(f"set {ea.ENV_CSV} (and optionally {ENV_TEXT_CSV}) or pass --csv")
    return found


def _col(fieldnames, *names):
    return next((n for n in names if n in fieldnames), None)


def parse_yes_no(value):
    v = (value or "").strip().lower()
    if v in YES:
        return True
    if v in NO:
        return False
    return None  # blank or unknown: the line is left out and counted


def read_labelled(path, default_lang="en"):
    """Return (sessions, stats). sessions: {id: [row dicts with _n, is_coach, text, language, gold]}.
    stats counts only; a file with no needs_human column returns (None, {'skipped': reason})."""
    path = Path(path)
    if not path.is_file():
        raise AdapterError(f"CSV not found: {path}")
    sessions = defaultdict(list)
    unlabelled = 0
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        names = reader.fieldnames or []
        if "needs_human" not in names:
            return None, {"skipped": "no needs_human column"}
        sid_col = _col(names, "session_id", "call_id")
        missing = [c for c, ok in (("session_id or call_id", sid_col), ("line_number", "line_number" in names),
                                   ("speaker", "speaker" in names), ("text", "text" in names)) if not ok]
        if missing:
            raise AdapterError("CSV is missing columns: " + ", ".join(missing))
        lang_col = "language" in names
        for row in reader:
            try:
                n = int(float(str(row["line_number"]).strip()))
            except ValueError:
                raise AdapterError("non-numeric line_number in the CSV") from None
            speaker = (row["speaker"] or "").strip().lower()
            gold = parse_yes_no(row["needs_human"])
            lang = ((row["language"] if lang_col else "") or default_lang).strip().lower()[:2]
            if lang not in ("en", "es"):
                lang = default_lang
            if gold is None and not speaker.startswith(COACH_SPEAKERS):
                unlabelled += 1
            sessions[row[sid_col].strip()].append(
                {"_n": n, "is_coach": speaker.startswith(COACH_SPEAKERS), "text": (row["text"] or "").strip() or "(blank)",
                 "language": lang, "gold": gold})
    for rows in sessions.values():
        rows.sort(key=lambda r: r["_n"])
    return dict(sessions), {"unlabelled_participant_lines": unlabelled}


def score(sessions):
    """Run the flagger. Returns [(sid, line_number, language, gold(bool), top_tier or None)] for labelled participant lines."""
    out = []
    for sid, rows in sessions.items():
        by_lang = defaultdict(list)
        for i, r in enumerate(rows):
            by_lang[r["language"]].append(i)
        for lang in by_lang:
            conv = Conversation.from_dict({
                "id": sid, "channel": "call", "language": lang,
                "lines": [{"idx": i, "speaker": "coach" if r["is_coach"] else "participant", "text": r["text"]}
                          for i, r in enumerate(rows)]})
            tiers = {}
            for f in flag_conversation(conv):
                tiers[f.line_idx] = min(tiers.get(f.line_idx, f.tier), f.tier)  # "S1" < "S2" < "S3"
            for i in by_lang[lang]:
                r = rows[i]
                if not r["is_coach"] and r["gold"] is not None:
                    out.append((sid, r["_n"], lang, r["gold"], tiers.get(i)))
    return out


def summarize(results):
    """Aggregates for one set of results; plain numbers only."""
    gold = [g for _, _, _, g, _ in results]
    pred = [t is not None for *_, t in results]
    pred_s1 = [t == "S1" for *_, t in results]
    m, s1 = metrics.binary_precision_recall(gold, pred), metrics.binary_precision_recall(gold, pred_s1)
    n = len(results)
    return {"lines": n, "positives": sum(gold), "precision": m["p"], "recall": m["r"], "f1": m["f1"],
            "false_alarms_per_100": 100 * m["fp"] / n if n else 0.0, "recall_s1_only": s1["r"],
            "tp": m["tp"], "fp": m["fp"], "fn": m["fn"]}


def format_summary(title, s):
    return "\n".join([
        f"######## {title} ########",
        f"participant lines scored: {s['lines']}; labelled yes: {s['positives']}",
        f"precision {s['precision']:.3f}  recall {s['recall']:.3f}  F1 {s['f1']:.3f}",
        f"false alarms per 100 lines: {s['false_alarms_per_100']:.2f}  (tp {s['tp']}, fp {s['fp']}, fn {s['fn']})",
        f"recall counting only S1 flags: {s['recall_s1_only']:.3f}"])


def write_predictions(out_dir, name, results):
    out = safe_dir(out_dir)
    fields = ["call_id", "line_number", "language", "label"]
    for suffix, idx in (("predictions", 4), ("labels", 3)):
        path = out / f"{name}_{suffix}.csv"
        safe_dest(path)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for r in results:
                v = (r[4] is not None) if idx == 4 else r[3]
                w.writerow({"call_id": r[0], "line_number": r[1], "language": r[2], "label": "yes" if v else "no"})


def report(paths, out_dir=None, default_lang="en"):
    lines = ["Rule flagger (S1-S3) vs the needs_human column, participant lines only. Aggregates only; no text printed.", ""]
    scored = 0
    for k, path in enumerate(paths, 1):
        sessions, stats = read_labelled(path, default_lang)
        label = f"file {k}"  # never the file name: it may contain a data path
        if sessions is None:
            lines += [f"== {label}: skipped ({stats['skipped']}) ==", ""]
            continue
        results = score(sessions)
        if not results:
            lines += [f"== {label}: no labelled participant lines ==", ""]
            continue
        scored += 1
        lines += [format_summary(f"{label}: all languages", summarize(results))]
        langs = sorted({r[2] for r in results})
        if len(langs) > 1:
            for lang in langs:
                lines += [format_summary(f"{label}: language {lang}", summarize([r for r in results if r[2] == lang]))]
        if stats["unlabelled_participant_lines"]:
            lines += [f"(left out: {stats['unlabelled_participant_lines']} participant lines with a blank or unknown needs_human)"]
        if out_dir:
            write_predictions(out_dir, f"needs_human_file{k}", results)
        lines += [""]
    if not scored:
        lines += ["Nothing scored: no file had a needs_human column with labelled participant lines."]
    elif out_dir:
        lines += [f"Predictions and labels written to {safe_dir(out_dir)} (outside the repo; never commit them)."]
    return "\n".join(lines)


def build_selftest_csv(path):
    """Invented, tiny CSV with a needs_human column (fictional lines only; for --selftest and tests)."""
    rows = [
        ("c1", 1, "counsellor", "How have you been this week?", "no", "en"),
        ("c1", 2, "client", "I have had chest pain since last night.", "yes", "en"),
        ("c1", 3, "client", "I want to walk on Sunday.", "no", "en"),
        ("c1", 4, "client", "My stomach has felt strange for days.", "yes", "en"),
        ("c2", 1, "counsellor", "Cuéntame cómo te sientes.", "no", "es"),
        ("c2", 2, "client", "No puedo respirar bien.", "yes", "es"),
        ("c2", 3, "client", "Ya no me duele el pecho.", "no", "es"),
        ("c2", 4, "client", "Quiero caminar el domingo.", "no", "es"),
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["call_id", "line_number", "speaker", "text", "needs_human", "language"])
        w.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Score the rule flagger against needs_human; aggregates only.")
    ap.add_argument("--selftest", action="store_true", help="use fictional fixtures; touches no real data")
    ap.add_argument("--csv", action="append", help=f"labelled CSV (repeatable; default: ${ea.ENV_CSV} and ${ENV_TEXT_CSV})")
    ap.add_argument("--lang", default="en", choices=("en", "es"), help="language for rows with no language column")
    ap.add_argument("--out", help=f"folder OUTSIDE the repo for predictions and labels (default: ${ea.ENV_OUT} if set; else none)")
    args = ap.parse_args(argv)
    try:
        if args.selftest:
            with tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp) / "selftest.csv"
                build_selftest_csv(p)
                print(report([p], None, args.lang))
            return 0
        out = args.out or os.environ.get(ea.ENV_OUT)
        print(report(paths_from_env(args.csv), out, args.lang))
        return 0
    except (AdapterError, SchemaError, ValueError, OSError) as e:
        print(f"error: {e.__class__.__name__}: {e if isinstance(e, AdapterError) else 'no row content shown'}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
