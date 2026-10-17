"""Pure-Python text classifier (multinomial naive Bayes on TF-IDF-weighted unigrams and bigrams).

No dependencies (scikit-learn is not installed here). It is NOT wired into the tagging pipeline; the owner
approves that step. Trained weights belong OUTSIDE the repo (see train_annomi.py).
"""
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from .config import COACH_RULES, PARTICIPANT_RULES

_TOKEN = re.compile(r"[\w']+", re.UNICODE)
_CUES = [(label, re.compile(p, re.IGNORECASE)) for rules in (COACH_RULES, PARTICIPANT_RULES)
         for label, pats in rules for p in pats.values()]


def features(text: str, context=None) -> Counter:
    """Unigrams, bigrams and shape markers from lowercase text.

    `context` is an optional (previous_line_text, next_line_text) pair; its words become extra "p:" / "n:"
    features (a reflection is often followed by "yeah", a question by an answer). Texts only, never labels.
    """
    toks = _TOKEN.findall(text.lower())
    feats = Counter(toks)
    if context:
        for prefix, other in zip(("p:", "n:"), context):
            feats.update(prefix + t for t in _TOKEN.findall((other or "").lower()))
    feats.update(a + " " + b for a, b in zip(toks, toks[1:]))
    if "?" in text or "¿" in text:
        feats["__question__"] += 1
    if toks:
        feats["__first_" + toks[0] + "__"] += 1
    for mark, name in ((",", "comma"), ("!", "bang"), ("...", "ellipsis")):
        if mark in text:
            feats["__punct_" + name + "__"] += 1
    stripped = text.strip()
    if stripped and stripped[-1] in ".!?":
        feats["__end_" + ("q" if stripped[-1] == "?" else "stop") + "__"] += 1
    for label, rx in _CUES:  # lexical cues from the rule tagger as extra features
        if rx.search(text):
            feats["__cue_" + label + "__"] += 1
    feats["__len_%d__" % min(len(toks) // 5, 6)] += 1
    return feats


def split_sessions(session_ids, test_fraction_denominator=5):
    """Deterministic session-level split: a session is test iff sha1(id) % denominator == 0.

    Returns (train_ids, test_ids); the two sets never overlap, so no line of a test session is trained on.
    """
    train, test = set(), set()
    for sid in session_ids:
        bucket = int(hashlib.sha1(str(sid).encode("utf-8")).hexdigest(), 16) % test_fraction_denominator
        (test if bucket == 0 else train).add(sid)
    return train, test


class NaiveBayes:
    def __init__(self, alpha: float = 0.5, use_context: bool = False):
        self.alpha = alpha
        self.use_context = use_context
        self.labels = []
        self.log_prior = {}
        self.weights = {}     # label -> {feature: log P(feature | label)}
        self.default = {}     # label -> log P(unseen feature | label)
        self.idf = {}

    def fit(self, texts, labels, contexts=None):
        if len(texts) != len(labels) or not texts:
            raise ValueError("need the same non-zero number of texts and labels")
        if contexts is not None and len(contexts) != len(texts):
            raise ValueError("contexts must match texts")
        self.use_context = contexts is not None
        docs = [features(t, contexts[i] if contexts is not None else None) for i, t in enumerate(texts)]
        df = Counter(f for d in docs for f in d)
        n = len(docs)
        self.idf = {f: math.log((1 + n) / (1 + c)) + 1.0 for f, c in df.items()}
        by_label = defaultdict(Counter)
        for d, y in zip(docs, labels):
            for f, c in d.items():
                by_label[y][f] += (1.0 + math.log(c)) * self.idf[f]
        self.labels = sorted(by_label)
        counts = Counter(labels)
        vocab = len(self.idf)
        for y in self.labels:
            total = sum(by_label[y].values()) + self.alpha * vocab
            self.log_prior[y] = math.log(counts[y] / n)
            self.weights[y] = {f: math.log((v + self.alpha) / total) for f, v in by_label[y].items()}
            self.default[y] = math.log(self.alpha / total)
        return self

    def predict(self, text: str, context=None) -> str:
        feats = features(text, context if self.use_context else None)
        best, best_score = None, -math.inf
        for y in self.labels:
            w, d = self.weights[y], self.default[y]
            score = self.log_prior[y] + sum(
                (1.0 + math.log(c)) * self.idf.get(f, 1.0) * w.get(f, d) for f, c in feats.items())
            if score > best_score:
                best, best_score = y, score
        return best

    def to_dict(self):
        return {"alpha": self.alpha, "use_context": self.use_context, "labels": self.labels, "log_prior": self.log_prior,
                "weights": self.weights, "default": self.default, "idf": self.idf}

    @classmethod
    def from_dict(cls, d):
        m = cls(d["alpha"], d.get("use_context", False))
        m.labels, m.log_prior, m.weights, m.default, m.idf = d["labels"], d["log_prior"], d["weights"], d["default"], d["idf"]
        return m

    def save(self, path):
        Path(path).write_text(json.dumps(self.to_dict()), encoding="utf-8")

    @classmethod
    def load(cls, path):
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
