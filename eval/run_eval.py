"""Usage: python3 eval/run_eval.py PREDICTIONS.csv LABELS.csv

CSV columns: call_id, line_number, language, label [, kind] [, needs_human]. Rows are joined on
(call_id, line_number), plus kind when both files have it (one label per kind per line);
language is taken from the labels file. Prints plain-text tables.
Runs fully offline.
"""
import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics  # noqa: E402

REQUIRED = ("call_id", "line_number", "language", "label")
YES = {"yes", "y", "true", "1"}
NO = {"no", "n", "false", "0"}


def read_header(path):
    with open(path, newline="", encoding="utf-8") as f:
        return next(csv.reader(f), [])


def read_rows(path, use_kind=False):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError("%s is missing columns: %s" % (path, ", ".join(missing)))
        rows = {}
        for row in reader:
            key = (row["call_id"].strip(), row["line_number"].strip())
            if use_kind:
                kind = (row["kind"] or "").strip()
                if not kind:
                    raise ValueError("%s has a blank kind for %s line %s" % (path, *key))
                key += (kind,)
            if key in rows:
                raise ValueError("%s has duplicate row for %s" % (path, " / ".join(key)))
            rows[key] = row
        return rows, "needs_human" in reader.fieldnames


def parse_yes_no(value):
    if value is None:
        raise ValueError("needs_human value is missing (short row)")
    v = value.strip().lower()
    if v in YES:
        return True
    if v in NO:
        return False
    raise ValueError("needs_human must be yes/no, got %r" % (value,))


def join(preds, labels):
    keys = sorted(k for k in labels if k in preds)
    return keys, len(set(labels) - set(preds)), len(set(preds) - set(labels))


def format_report(pred_path, label_path):
    pred_kind = "kind" in read_header(pred_path)
    label_kind = "kind" in read_header(label_path)
    if pred_kind != label_kind:
        raise ValueError("kind column must be in both files or neither")
    use_kind = pred_kind
    preds, pred_nh = read_rows(pred_path, use_kind)
    labels, label_nh = read_rows(label_path, use_kind)
    keys, only_labels, only_preds = join(preds, labels)
    if not keys:
        raise ValueError("no rows match on (call_id, line_number)")
    y_true = [labels[k]["label"].strip() for k in keys]
    y_pred = [preds[k]["label"].strip() for k in keys]
    langs = [labels[k]["language"].strip() for k in keys]
    label_set = sorted(set(y_true) | set(y_pred))

    out = ["Matched rows: %d (only in labels: %d, only in predictions: %d)"
           % (len(keys), only_labels, only_preds), ""]
    out += _label_table("ALL", metrics.per_label(y_true, y_pred, label_set),
                        metrics.macro_f1(y_true, y_pred, label_set))
    out.append("Cohen's kappa (prediction vs label): %.3f" % metrics.cohen_kappa(y_pred, y_true))
    out.append("")
    out += _confusion_table(*metrics.confusion_matrix(y_true, y_pred, label_set))
    for lang, res in metrics.by_language(y_true, y_pred, langs, label_set).items():
        out += _label_table("language=%s (n=%d)" % (lang, res["n"]), res["by_label"], res["macro_f1"])

    if pred_nh and label_nh:
        t = [parse_yes_no(labels[k].get("needs_human")) for k in keys]
        p = [parse_yes_no(preds[k].get("needs_human")) for k in keys]
        b = metrics.binary_precision_recall(t, p)
        out.append("needs_human: precision %.3f  recall %.3f  f1 %.3f  (tp %d, fp %d, fn %d)"
                   % (b["p"], b["r"], b["f1"], b["tp"], b["fp"], b["fn"]))
    else:
        out.append("needs_human: column not in both files, skipped")
    return "\n".join(out)


def _label_table(title, scores, macro):
    width = max([len("label")] + [len(l) for l in scores])
    lines = ["== %s ==" % title,
             "%-*s  %9s  %6s  %6s  %7s" % (width, "label", "precision", "recall", "f1", "support")]
    for lab, s in scores.items():
        lines.append("%-*s  %9.3f  %6.3f  %6.3f  %7d" % (width, lab, s["p"], s["r"], s["f1"], s["n"]))
    lines += ["macro-F1: %.3f" % macro, ""]
    return lines


def _confusion_table(labels, matrix):
    width = max([len("true \\ pred")] + [len(l) for l in labels])
    col = max(5, *[len(l) for l in labels])
    lines = ["== confusion matrix (rows = label, columns = prediction) ==",
             "%-*s  " % (width, "true \\ pred") + "  ".join("%*s" % (col, l) for l in labels)]
    for lab, row in zip(labels, matrix):
        lines.append("%-*s  " % (width, lab) + "  ".join("%*d" % (col, v) for v in row))
    lines.append("")
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description="Offline eval: predictions vs labels CSV.")
    ap.add_argument("predictions")
    ap.add_argument("labels")
    args = ap.parse_args(argv)
    try:
        print(format_report(args.predictions, args.labels))
    except (OSError, ValueError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
