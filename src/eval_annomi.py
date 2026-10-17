"""AnnoMI eval adapter: run our tagger and flagger on the organizers' AnnoMI CSV and print ONLY aggregates.

Run it locally (never inside an AI tool):
    python3 -m src.eval_annomi            # reads the file named by COACH_ANNOMI_CSV (or --csv)
    python3 -m src.eval_annomi --selftest # fictional fixtures only, no real data

Privacy rules this file enforces: it prints label names and numbers only, never a line of text or a row;
errors name the problem without echoing cell contents; predictions and derived labels are written to an
output folder OUTSIDE the repo (set COACH_OUT_DIR) and the writer
refuses any folder inside the repo.
"""
import argparse
import csv
import os
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "eval"))
import run_eval  # noqa: E402  (row 8 harness, offline)

from .flagger.rules import flag_conversation  # noqa: E402
from .schema import Conversation, SchemaError  # noqa: E402
from .tagger.rules import tag_conversation  # noqa: E402

ENV_CSV, ENV_OUT = "COACH_ANNOMI_CSV", "COACH_OUT_DIR"


def resolve_csv(arg=None):
    """The AnnoMI file to read: --csv, else $COACH_ANNOMI_CSV. No default path is baked into the repo."""
    value = arg or os.environ.get(ENV_CSV)
    if not value:
        raise AdapterError(f"set {ENV_CSV} (or pass --csv) to the local AnnoMI CSV")
    return Path(value).expanduser()


def resolve_out():
    value = os.environ.get(ENV_OUT)
    if not value:
        raise AdapterError(f"set {ENV_OUT} to a folder OUTSIDE the repo for predictions and weights")
    return value
REQUIRED = ("session_id", "line_number", "speaker", "text", "counsellor_move", "question_type",
            "reflection_type", "client_talk", "expert_raters", "expert_agreement_pct")
EXPERT_FULL = "10"

# Our 12 coach moves -> AnnoMI's coarser set.
COARSE = {
    "open_question": "question_open", "closed_question": "question_closed",
    "simple_reflection": "reflection_simple", "complex_reflection": "reflection_complex",
    "give_information": "information_advice", "persuade": "information_advice",
    "affirm": "other", "seek_collaboration": "other", "emphasize_autonomy": "other",
    "ask_permission": "other", "confront": "other", "other": "other",
}


from .safe_paths import AdapterError, safe_dest, safe_dir  # noqa: E402


def _norm(value):
    return (value or "").strip().lower().replace("_", "-").replace("/", "-").replace(" ", "-")


def gold_coach_label(row):
    """Coarse AnnoMI label for a counsellor row, tolerant of spelling (information, information/advice, ...)."""
    move = _norm(row.get("counsellor_move"))
    if not move:
        return None
    if "question" in move:
        return "question_" + (_norm(row.get("question_type")) or "open")
    if "reflection" in move:
        return "reflection_" + (_norm(row.get("reflection_type")) or "simple")
    if "info" in move or "advice" in move:
        return "information_advice"
    return "other"


def gold_talk_label(row):
    talk = _norm(row.get("client_talk"))
    return talk if talk in ("change", "sustain", "neutral") else None


def _to_int(value, what):
    try:
        return int(float(str(value).strip()))
    except ValueError:
        raise AdapterError(f"non-numeric {what} in the CSV") from None


def read_sessions(path):
    """Return {session_id: [rows sorted by line_number]} from the AnnoMI CSV (cell contents are never reported)."""
    path = Path(path)
    if not path.is_file():
        raise AdapterError(f"CSV not found: {path}")
    sessions = defaultdict(list)
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            raise AdapterError("CSV is missing columns: " + ", ".join(missing))
        for row in reader:
            row["_n"] = _to_int(row["line_number"], "line_number")
            sessions[row["session_id"].strip()].append(row)
    for rows in sessions.values():
        rows.sort(key=lambda r: r["_n"])
    return dict(sessions)


def to_conversation(session_id, rows, language="en"):
    lines = []
    for i, r in enumerate(rows):
        speaker = "coach" if (r["speaker"] or "").strip().lower().startswith("counsel") else "participant"
        lines.append({"idx": i, "speaker": speaker, "text": (r["text"] or "").strip() or "(blank)"})
    return Conversation.from_dict({"id": session_id, "channel": "call", "language": language, "lines": lines})


def category_counts(sessions):
    """Counts of the documented category strings per column (label names only, never text)."""
    out = {c: Counter() for c in ("counsellor_move", "question_type", "reflection_type", "client_talk")}
    for rows in sessions.values():
        for r in rows:
            for c in out:
                v = (r.get(c) or "").strip()
                if v and len(v) <= 40:
                    out[c][v] += 1
    return {c: dict(v) for c, v in out.items()}


def analyze(sessions):
    """Run our engine. Returns (coach_pairs, talk_pairs, flag_stats); pairs are (session, line_number, pred, gold, row)."""
    coach, talk = [], []
    flag_lines, tiers, total = 0, Counter(), 0
    for sid, rows in sessions.items():
        conv = to_conversation(sid, rows)
        total += len(rows)
        tags = {(t.line_idx, t.kind): t.label for t in tag_conversation(conv, models=None)}  # rules-only baseline
        for i, r in enumerate(rows):
            g = gold_coach_label(r)
            if g is not None and (i, "coach_move") in tags:
                coach.append((sid, r["_n"], COARSE[tags[(i, "coach_move")]], g, r))
            g = gold_talk_label(r)
            if g is not None and (i, "participant_talk") in tags:
                talk.append((sid, r["_n"], tags[(i, "participant_talk")], g, r))
        flags = flag_conversation(conv)
        flag_lines += len({f.line_idx for f in flags})
        tiers.update(f.tier for f in flags)
    return coach, talk, {"lines": total, "flagged_lines": flag_lines, "tiers": dict(tiers)}


def _safe_out(out_dir):
    return safe_dir(out_dir)


def _write_pair(out, name, pairs):
    fields = ["call_id", "line_number", "language", "label"]
    pp, lp = out / f"{name}_predictions.csv", out / f"{name}_labels.csv"
    for path, idx in ((pp, 2), (lp, 3)):
        safe_dest(path)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for p in pairs:
                w.writerow({"call_id": p[0], "line_number": p[1], "language": "en", "label": p[idx]})
    return pp, lp


def _mean_agreement(pairs):
    vals = []
    for p in pairs:
        try:
            vals.append(float(str(p[4]["expert_agreement_pct"]).strip().rstrip("%")))
        except ValueError:
            continue
    return sum(vals) / len(vals) if vals else None


def report(sessions, out_dir):
    out = _safe_out(out_dir)
    coach, talk, fstats = analyze(sessions)
    lines = [f"Category strings seen (label names only): {category_counts(sessions)}",
             f"Lines analyzed: {fstats['lines']}; flagged lines: {fstats['flagged_lines']}; flags by tier: {fstats['tiers'] or 'none'}",
             "(AnnoMI has no needs-a-human labels, so the flagger is counted, not scored.)", ""]
    for title, name, pairs in (("COACH MOVES (coarse AnnoMI set)", "coach", coach), ("CLIENT TALK", "talk", talk)):
        if not pairs:
            lines += [f"== {title}: no labeled lines ==", ""]
            continue
        lines += [f"######## {title}: all {len(pairs)} labeled lines ########",
                  run_eval.format_report(*_write_pair(out, name + "_all", pairs)), ""]
        full = [p for p in pairs if str(p[4].get("expert_raters", "")).strip().split(".")[0] == EXPERT_FULL]
        if full:
            lines += [f"######## {title}: {len(full)} lines with expert_raters == {EXPERT_FULL} ########",
                      run_eval.format_report(*_write_pair(out, name + "_10", full))]
            ceil = _mean_agreement(full)
            lines += [f"Expert agreement ceiling on these lines (mean expert_agreement_pct): "
                      f"{'n/a' if ceil is None else format(ceil, '.1f')}", ""]
        else:
            lines += [f"(no lines with expert_raters == {EXPERT_FULL})", ""]
    lines.append(f"Predictions and derived labels written to {out} (outside the repo; never commit them).")
    return "\n".join(lines)


def build_selftest_csv(path):
    """Write a tiny AnnoMI-shaped CSV from invented lines (fictional; for --selftest and tests)."""
    rows = [
        ("s1", 1, "counsellor", "How have you been feeling about your walks this week?", "question", "open", "", "", "10", "90"),
        ("s1", 2, "client", "I want to walk on Sunday.", "", "", "", "change", "10", "80"),
        ("s1", 3, "counsellor", "It sounds like company matters to you.", "reflection", "", "simple", "", "10", "100"),
        ("s1", 4, "client", "I am too tired, I can't.", "", "", "", "sustain", "3", "60"),
        ("s1", 5, "counsellor", "Did you walk on Monday?", "question", "closed", "", "", "10", "70"),
        ("s1", 6, "client", "Okay.", "", "", "", "neutral", "10", "100"),
        ("s2", 1, "counsellor", "You should walk every day.", "information-or-advice", "", "", "", "10", "80"),
        ("s2", 2, "client", "I have chest pain since last night.", "", "", "", "neutral", "10", "90"),
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(REQUIRED)
        w.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run our engine on the AnnoMI CSV and print aggregates only.")
    ap.add_argument("--selftest", action="store_true", help="use fictional fixtures; touches no real data")
    ap.add_argument("--csv", help=f"path to the AnnoMI CSV (default: ${ENV_CSV})")
    args = ap.parse_args(argv)
    try:
        if args.selftest:
            with tempfile.TemporaryDirectory() as tmp:
                csv_path = Path(tmp) / "selftest.csv"
                build_selftest_csv(csv_path)
                print(report(read_sessions(csv_path), Path(tmp) / "out"))
            return 0
        print(report(read_sessions(resolve_csv(args.csv)), resolve_out()))
        return 0
    except (AdapterError, SchemaError, ValueError, OSError) as e:
        print(f"error: {e.__class__.__name__}: {e if isinstance(e, AdapterError) else 'see message above; no row content shown'}",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
