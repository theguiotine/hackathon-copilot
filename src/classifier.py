"""Pure-Python text classifier (multinomial naive Bayes on TF-IDF-weighted unigrams and bigrams).

No dependencies (scikit-learn is not installed here). It is NOT wired into the tagging pipeline; the owner
approves that step. Trained weights belong OUTSIDE the repo (see classifier_train.py).
"""
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

_TOKEN = re.compile(r"[\w']+", re.UNICODE)


def features(text: str) -> Counter:
    """Unigrams, bigrams and two shape markers (question mark, short line) from lowercase text."""
    toks = _TOKEN.findall(text.lower())
    feats = Counter(toks)
    feats.update(a + " " + b for a, b in zip(toks, toks[1:]))
    if "?" in text or "¿" in text:
        feats["__question__"] += 1
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
    def __init__(self, alpha: float = 0.5):
        self.alpha = alpha
        self.labels = []
        self.log_prior = {}
        self.weights = {}     # label -> {feature: log P(feature | label)}
        self.default = {}     # label -> log P(unseen feature | label)
        self.idf = {}

    def fit(self, texts, labels):
        if len(texts) != len(labels) or not texts:
            raise ValueError("need the same non-zero number of texts and labels")
        docs = [features(t) for t in texts]
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

    def predict(self, text: str) -> str:
        feats = features(text)
        best, best_score = None, -math.inf
        for y in self.labels:
            w, d = self.weights[y], self.default[y]
            score = self.log_prior[y] + sum(
                (1.0 + math.log(c)) * self.idf.get(f, 1.0) * w.get(f, d) for f, c in feats.items())
            if score > best_score:
                best, best_score = y, score
        return best

    def to_dict(self):
        return {"alpha": self.alpha, "labels": self.labels, "log_prior": self.log_prior,
                "weights": self.weights, "default": self.default, "idf": self.idf}

    @classmethod
    def from_dict(cls, d):
        m = cls(d["alpha"])
        m.labels, m.log_prior, m.weights, m.default, m.idf = d["labels"], d["log_prior"], d["weights"], d["default"], d["idf"]
        return m

    def save(self, path):
        Path(path).write_text(json.dumps(self.to_dict()), encoding="utf-8")

    @classmethod
    def load(cls, path):
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
