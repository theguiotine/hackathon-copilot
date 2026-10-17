"""Score our rule flagger (S1-S3) against the organizers' `needs_human` column; prints ONLY aggregates.

Run locally by the owner (never inside an AI tool):
    python3 -m src.eval_needs_human                # reads whichever of the env vars below are set
    python3 -m src.eval_needs_human --call-lines A.csv --calls B.csv --texts C.csv --csv D.csv
    python3 -m src.eval_needs_human --selftest     # fictional fixtures only, no real data

Inputs (any subset; none is baked into the repo):
  $COACH_CALL_LINES_CSV + $COACH_CALLS_CSV   synthetic call transcripts: one line per row with call_id, line_number,
        speaker (coach or participant), text, needs_human. The file has no language column, so language is joined
        from the calls file (`language`, keyed by call_id); a call missing there falls back to --lang and is counted.
  $COACH_TEXTS_CSV   synthetic text messages: one message per row with participant_id, message_id, sender (coach,
        participant or automatic), text, needs_human. `sender` is the speaker (only sender == participant is
        scored), message_id is the line key, messages are grouped per participant_id, and language comes from --lang
        (default en) because the file has none.
  $COACH_ANNOMI_CSV / --csv   optional generic file with session_id or call_id, line_number, speaker, text,
        needs_human and an optional language column; a file without needs_human is reported as skipped.

What it does: for every PARTICIPANT line with a yes/no label, run the rule flagger on the conversation and compare
"line flagged" with the label. Prints lines, positives, precision, recall, F1, false alarms per 100 lines, and recall
counting only S1 flags, overall and split by language when more than one is present. Blank or unrecognised labels
are left out and counted.

Privacy rules this file enforces: it never prints a line of text, a row or a path (sources are called "calls file",
"texts file", "file 1"); errors name columns without echoing cell contents; with --out (or $COACH_OUT_DIR) it
writes predictions and labels to a folder OUTSIDE the repo and refuses a folder inside the repo. Without --out it
writes no files at all.
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

ENV_CALL_LINES, ENV_CALLS, ENV_TEXTS = "COACH_CALL_LINES_CSV", "COACH_CALLS_CSV", "COACH_TEXTS_CSV"
YES = {"yes", "y", "true", "1"}
NO = {"no", "n", "false", "0"}
PARTICIPANT_SPEAKERS = {"participant", "client", "patient"}  # exact words; coach, counsellor, automatic are not scored
LANG_WORDS = {"en": "en", "english": "en", "es": "es", "spanish": "es", "espanol": "es", "español": "es"}


def _col(fieldnames, *names):
    return next((n for n in names if n in fieldnames), None)


def parse_yes_no(value):
    v = (value or "").strip().lower()
    if v in YES:
        return True
    if v in NO:
        return False
    return None  # blank or unknown: the line is left out and counted


def norm_lang(value, default):
    return LANG_WORDS.get((value or "").strip().lower(), default)


def read_call_languages(path):
    """{call_id: 'en'|'es'} from the calls file (columns call_id and language). Values are never printed."""
    path = Path(path)
    if not path.is_file():
        raise AdapterError("calls file not found")
    langs = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        names = reader.fieldnames or []
        if "call_id" not in names or "language" not in names:
            raise AdapterError("calls file is missing columns: " + ", ".join(c for c in ("call_id", "language") if c not in names))
        for row in reader:
            lang = norm_lang(row["language"], None)
            if lang:
                langs[(row["call_id"] or "").strip()] = lang
    return langs


def read_labelled(path, default_lang="en", call_languages=None):
    """Return (sessions, stats). sessions: {group id: [rows: key, _n, participant, text, language, gold]}.
    Group id is session_id/call_id, or participant_id for a texts file; the line key is line_number, or message_id for
    a texts file; the speaker column is `speaker`, or `sender`. When call_languages is given, language is joined by
    call_id. stats are counts only. A file with no needs_human column returns (None, {'skipped': ...})."""
    path = Path(path)
    if not path.is_file():
        raise AdapterError("CSV not found")
    sessions = defaultdict(list)
    unlabelled = fallback_lang = 0
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        names = reader.fieldnames or []
        if "needs_human" not in names:
            return None, {"skipped": "no needs_human column"}
        sid_col = _col(names, "session_id", "call_id", "participant_id")
        key_col = _col(names, "line_number", "message_id")
        spk_col = _col(names, "speaker", "sender")
        missing = [c for c, ok in (("session_id, call_id or participant_id", sid_col), ("line_number or message_id", key_col),
                                   ("speaker or sender", spk_col), ("text", "text" in names)) if not ok]
        if missing:
            raise AdapterError("CSV is missing columns: " + ", ".join(missing))
        lang_col = "language" in names
        for order, row in enumerate(reader):
            key = (row[key_col] or "").strip()
            try:
                n = float(key)
            except ValueError:
                n = order  # non-numeric id (for example m017): keep file order
            sid = (row[sid_col] or "").strip()
            if call_languages is not None:
                lang = call_languages.get(sid)
                if lang is None:
                    fallback_lang += 1
                    lang = default_lang
            else:
                lang = norm_lang(row["language"] if lang_col else "", default_lang)
            participant = (row[spk_col] or "").strip().lower() in PARTICIPANT_SPEAKERS
            gold = parse_yes_no(row["needs_human"])
            if participant and gold is None:
                unlabelled += 1
            sessions[sid].append({"key": key, "_n": n, "participant": participant,
                                  "text": (row["text"] or "").strip() or "(blank)", "language": lang, "gold": gold})
    for rows in sessions.values():
        rows.sort(key=lambda r: r["_n"])
    return dict(sessions), {"unlabelled_participant_lines": unlabelled, "rows_without_calls_language": fallback_lang}


def score(sessions):
    """Run the flagger. Returns [(group id, line key, language, gold(bool), top_tier or None)] for labelled participant lines."""
    out = []
    for sid, rows in sessions.items():
        by_lang = defaultdict(list)
        for i, r in enumerate(rows):
            by_lang[r["language"]].append(i)
        for lang in by_lang:
            conv = Conversation.from_dict({
                "id": sid, "channel": "call", "language": lang,
                "lines": [{"idx": i, "speaker": "participant" if r["participant"] else "coach", "text": r["text"]}
                          for i, r in enumerate(rows)]})
            tiers = {}
            for f in flag_conversation(conv):
                tiers[f.line_idx] = min(tiers.get(f.line_idx, f.tier), f.tier)  # "S1" < "S2" < "S3"
            for i in by_lang[lang]:
                r = rows[i]
                if r["participant"] and r["gold"] is not None:
                    out.append((sid, r["key"], lang, r["gold"], tiers.get(i)))
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


def sources_from(args):
    """Ordered [(label, kind, path, calls_path)] from flags, else env vars. Labels never reveal a path."""
    def pick(flag, env):
        v = flag or os.environ.get(env)
        return Path(v).expanduser() if v else None
    src = []
    call_lines, calls = pick(args.call_lines, ENV_CALL_LINES), pick(args.calls, ENV_CALLS)
    if call_lines:
        if not calls:
            raise AdapterError(f"the call-lines file needs the calls file for language: set {ENV_CALLS} or pass --calls")
        src.append(("calls file", "calls", call_lines, calls))
    texts = pick(args.texts, ENV_TEXTS)
    if texts:
        src.append(("texts file", "texts", texts, None))
    generic = [Path(p).expanduser() for p in (args.csv or [])]
    if not args.csv and os.environ.get(ea.ENV_CSV):
        generic = [Path(os.environ[ea.ENV_CSV]).expanduser()]
    for k, p in enumerate(generic, 1):
        src.append((f"file {k}", "generic", p, None))
    if not src:
        raise AdapterError(f"set {ENV_CALL_LINES} and {ENV_CALLS}, and/or {ENV_TEXTS}, and/or {ea.ENV_CSV} (or pass the matching flags)")
    return src


def report(sources, out_dir=None, default_lang="en"):
    """sources: [(label, kind, path, calls_path)], or plain paths (treated as generic files)."""
    sources = [s if isinstance(s, tuple) else (f"file {k}", "generic", s, None) for k, s in enumerate(sources, 1)]
    lines = ["Rule flagger (S1-S3) vs the needs_human column, participant lines only. Aggregates only; no text or paths printed.", ""]
    scored = 0
    for k, (label, kind, path, calls_path) in enumerate(sources, 1):
        langs_by_call = read_call_languages(calls_path) if kind == "calls" else None
        sessions, stats = read_labelled(path, default_lang, langs_by_call)
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
        if kind == "texts":
            lines += [f"(language for this file comes from --lang, default en; the file has no language column: used {default_lang})"]
        if stats["unlabelled_participant_lines"]:
            lines += [f"(left out: {stats['unlabelled_participant_lines']} participant lines with a blank or unknown needs_human)"]
        if stats["rows_without_calls_language"]:
            lines += [f"({stats['rows_without_calls_language']} rows had a call_id missing from the calls file; --lang {default_lang} used)"]
        if out_dir:
            write_predictions(out_dir, f"needs_human_{label.replace(' ', '_')}_{k}", results)
        lines += [""]
    if not scored:
        lines += ["Nothing scored: no source had a needs_human column with labelled participant lines."]
    elif out_dir:
        lines += [f"Predictions and labels written to {safe_dir(out_dir)} (outside the repo; never commit them)."]
    return "\n".join(lines)


def build_selftest_csv(path):
    """Invented, tiny generic CSV with a needs_human column (fictional lines only; for --selftest and tests)."""
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


def build_selftest_synthetic(folder):
    """Invented files shaped like the organizers' synthetic call lines, calls and text messages (fictional)."""
    folder = Path(folder)
    with open(folder / "calls.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["call_id", "language"])
        w.writerows([("k1", "en"), ("k2", "es")])
    with open(folder / "lines.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["call_id", "line_number", "time_in_call", "speaker", "text", "coach_move", "participant_talk", "needs_human"])
        w.writerows([
            ("k1", 1, "00:01", "coach", "How are you today?", "open_question", "", ""),
            ("k1", 2, "00:09", "participant", "I have had chest pain since last night.", "", "sustain", "yes"),
            ("k1", 3, "00:20", "participant", "I want to walk on Sunday.", "", "change", "no"),
            ("k2", 1, "00:01", "coach", "Cuéntame cómo te sientes.", "open_question", "", ""),
            ("k2", 2, "00:12", "participant", "No puedo respirar bien.", "", "sustain", "yes"),
            ("k2", 3, "00:30", "participant", "Quiero caminar el domingo.", "", "change", "no"),
        ])
    with open(folder / "texts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["participant_id", "coach_id", "message_id", "sent_at", "sender", "text", "labelled", "intent", "needs_human"])
        w.writerows([
            ("p1", "c1", "m001", "2026-01-01T09:00", "automatic", "Reminder: walk today.", "no", "", ""),
            ("p1", "c1", "m002", "2026-01-01T10:00", "participant", "I have had chest pain since last night.", "yes", "", "yes"),
            ("p1", "c1", "m003", "2026-01-01T11:00", "coach", "Thanks for telling me.", "no", "", ""),
            ("p1", "c1", "m004", "2026-01-01T12:00", "participant", "Walking went fine.", "yes", "", "no"),
        ])


def main(argv=None):
    ap = argparse.ArgumentParser(description="Score the rule flagger against needs_human; aggregates only.")
    ap.add_argument("--selftest", action="store_true", help="use fictional fixtures; touches no real data")
    ap.add_argument("--call-lines", help=f"synthetic call transcripts CSV (default: ${ENV_CALL_LINES})")
    ap.add_argument("--calls", help=f"synthetic calls CSV with call_id and language (default: ${ENV_CALLS})")
    ap.add_argument("--texts", help=f"synthetic text messages CSV (default: ${ENV_TEXTS})")
    ap.add_argument("--csv", action="append", help=f"generic labelled CSV, repeatable (default: ${ea.ENV_CSV} if set)")
    ap.add_argument("--lang", default="en", choices=("en", "es"), help="language for rows with no language information")
    ap.add_argument("--out", help=f"folder OUTSIDE the repo for predictions and labels (default: ${ea.ENV_OUT} if set; else none)")
    args = ap.parse_args(argv)
    try:
        if args.selftest:
            with tempfile.TemporaryDirectory() as tmp:
                tmp = Path(tmp)
                build_selftest_csv(tmp / "selftest.csv")
                build_selftest_synthetic(tmp)
                srcs = [("calls file", "calls", tmp / "lines.csv", tmp / "calls.csv"),
                        ("texts file", "texts", tmp / "texts.csv", None), ("file 1", "generic", tmp / "selftest.csv", None)]
                print(report(srcs, None, args.lang))
            return 0
        out = args.out or os.environ.get(ea.ENV_OUT)
        print(report(sources_from(args), out, args.lang))
        return 0
    except (AdapterError, SchemaError, ValueError, OSError) as e:
        print(f"error: {e.__class__.__name__}: {e if isinstance(e, AdapterError) else 'no row content shown'}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
