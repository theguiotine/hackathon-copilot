"""Evaluation metrics in plain Python (no dependencies)."""
from collections import Counter


def _safe_div(num, den):
    return num / den if den else 0.0


def _f1(p, r):
    return _safe_div(2 * p * r, p + r)


def per_label(y_true, y_pred, labels=None):
    """Return {label: {"p", "r", "f1", "n"}}; n is support (count in y_true)."""
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    if labels is None:
        labels = sorted(set(y_true) | set(y_pred))
    tp, fp, fn = Counter(), Counter(), Counter()
    for t, p in zip(y_true, y_pred):
        if t == p:
            tp[t] += 1
        else:
            fp[p] += 1
            fn[t] += 1
    out = {}
    for lab in labels:
        p = _safe_div(tp[lab], tp[lab] + fp[lab])
        r = _safe_div(tp[lab], tp[lab] + fn[lab])
        out[lab] = {"p": p, "r": r, "f1": _f1(p, r), "n": tp[lab] + fn[lab]}
    return out


def macro_f1(y_true, y_pred, labels=None):
    """Unweighted mean of per-label F1."""
    scores = per_label(y_true, y_pred, labels)
    return _safe_div(sum(s["f1"] for s in scores.values()), len(scores))


def confusion_matrix(y_true, y_pred, labels=None):
    """Return (labels, matrix) where matrix[i][j] = count(true=labels[i], pred=labels[j])."""
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    if labels is None:
        labels = sorted(set(y_true) | set(y_pred))
    index = {lab: i for i, lab in enumerate(labels)}
    matrix = [[0] * len(labels) for _ in labels]
    for t, p in zip(y_true, y_pred):
        if t in index and p in index:
            matrix[index[t]][index[p]] += 1
    return labels, matrix


def by_language(y_true, y_pred, languages, labels=None):
    """Return {language: {"by_label": per_label(...), "macro_f1": float, "n": int}}."""
    if not (len(y_true) == len(y_pred) == len(languages)):
        raise ValueError("inputs must have the same length")
    out = {}
    for lang in sorted(set(languages)):
        idx = [i for i, l in enumerate(languages) if l == lang]
        t = [y_true[i] for i in idx]
        p = [y_pred[i] for i in idx]
        out[lang] = {
            "by_label": per_label(t, p, labels),
            "macro_f1": macro_f1(t, p, labels),
            "n": len(idx),
        }
    return out


def cohen_kappa(rater_a, rater_b):
    """Cohen's kappa: (p_o - p_e) / (1 - p_e). Returns 1.0 if p_e == 1 and raters agree fully."""
    if len(rater_a) != len(rater_b):
        raise ValueError("raters must have the same length")
    n = len(rater_a)
    if n == 0:
        return 0.0
    p_o = sum(a == b for a, b in zip(rater_a, rater_b)) / n
    ca, cb = Counter(rater_a), Counter(rater_b)
    p_e = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    if p_e == 1.0:
        return 1.0 if p_o == 1.0 else 0.0
    return (p_o - p_e) / (1 - p_e)


def _check_ratings(a, b):
    if len(a) != len(b):
        raise ValueError("ratings must have the same length")
    for x in list(a) + list(b):
        if not 1 <= x <= 5:
            raise ValueError("ratings must be between 1 and 5, got %r" % (x,))


def mean_absolute_error(a, b):
    """Mean |a - b| for two numeric ratings on a 1-5 scale."""
    _check_ratings(a, b)
    return _safe_div(sum(abs(x - y) for x, y in zip(a, b)), len(a))


def within_one(a, b):
    """Share of pairs where |a - b| <= 1."""
    _check_ratings(a, b)
    return _safe_div(sum(abs(x - y) <= 1 for x, y in zip(a, b)), len(a))


def binary_precision_recall(y_true, y_pred):
    """Precision/recall for a yes/no column (True = needs_human). Returns dict with p, r, f1, tp, fp, fn."""
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    tp = sum(1 for t, p in zip(y_true, y_pred) if t and p)
    fp = sum(1 for t, p in zip(y_true, y_pred) if not t and p)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t and not p)
    p = _safe_div(tp, tp + fp)
    r = _safe_div(tp, tp + fn)
    return {"p": p, "r": r, "f1": _f1(p, r), "tp": tp, "fp": fp, "fn": fn}
