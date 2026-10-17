"""Synthetic, invented predictions/labels for tests. No real data; nothing is written unless asked."""
import csv
import random

LABELS = ["open question", "simple reflection", "affirm", "other"]
FIELDS = ["call_id", "line_number", "language", "label", "needs_human"]


def make_pair(n_rows=200, accuracy=0.75, seed=7):
    """Return (predictions, labels) as lists of dict rows sharing call_id/line_number/language."""
    rng = random.Random(seed)
    labels, preds = [], []
    for i in range(n_rows):
        key = {
            "call_id": "mock-%02d" % (i // 20),
            "line_number": str(i % 20 + 1),
            "language": "en" if (i // 20) % 2 == 0 else "es",
        }
        true_label = rng.choice(LABELS)
        pred_label = true_label if rng.random() < accuracy else rng.choice(LABELS)
        true_nh = rng.random() < 0.1
        pred_nh = true_nh if rng.random() < 0.8 else not true_nh
        labels.append(dict(key, label=true_label, needs_human="yes" if true_nh else "no"))
        preds.append(dict(key, label=pred_label, needs_human="yes" if pred_nh else "no"))
    return preds, labels


def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
