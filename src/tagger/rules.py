"""Rule tagger EN+ES. One coach_move per coach line (first matching rule, else "other"),
one participant_talk per participant line (default "neutral"), plus text_intent on text-channel lines.

Optional classifier layer: if trained weights exist (directory in $COACH_CLASSIFIER_DIR, files
classifier_coach.json / classifier_talk.json) it labels coach moves and client talk, with method "classifier".
Rules still win for the specific moves a coarse classifier cannot see (RULE_KEEPS), and with no weights the
tagger is exactly the rule tagger. The needs-a-human flagger never uses the classifier.
"""
import os
import re
from pathlib import Path

from ..config import COACH_RULES, PARTICIPANT_RULES, TEXT_INTENT_RULES
from ..classifier import NaiveBayes
from ..schema import Conversation, Tag

CLASSIFIER_DIR_ENV = "COACH_CLASSIFIER_DIR"
RULE_KEEPS = ("affirm", "seek_collaboration", "emphasize_autonomy", "ask_permission", "persuade", "confront")
FROM_COARSE = {"question_open": "open_question", "question_closed": "closed_question",
               "reflection_simple": "simple_reflection", "reflection_complex": "complex_reflection",
               "information_advice": "give_information", "other": "other"}
_UNSET = object()
_CACHE = {}


def load_models(directory=None):
    """Load trained weights from `directory` (default: $COACH_CLASSIFIER_DIR); None if unset or absent."""
    directory = directory or os.environ.get(CLASSIFIER_DIR_ENV)
    if not directory:
        return None
    models = {}
    for key in ("coach", "talk"):
        path = Path(directory).expanduser() / f"classifier_{key}.json"
        if path.is_file():
            stamp = (str(path), path.stat().st_mtime)
            if stamp not in _CACHE:
                _CACHE[stamp] = NaiveBayes.load(path)
            models[key] = _CACHE[stamp]
    return models or None


def _compile(rules):
    return [(label, {l: re.compile(p, re.IGNORECASE) for l, p in pats.items()}) for label, pats in rules]


_COACH, _PART, _INTENT = _compile(COACH_RULES), _compile(PARTICIPANT_RULES), _compile(TEXT_INTENT_RULES)


_REFLECTIONS = ("simple_reflection", "complex_reflection")
_SENTENCE_END = re.compile(r"[.!?]")


def _in_question(text: str, end: int) -> bool:
    """True if the sentence containing text[:end] ends with a question mark."""
    m = _SENTENCE_END.search(text, end)
    return m is not None and m.group(0) == "?"


def _first(rules, text, lang):
    for label, pats in rules:
        m = pats[lang].search(text)
        if m and not (label in _REFLECTIONS and _in_question(text, m.end())):
            return label
    return None


def tag_conversation(conv: Conversation, models=_UNSET) -> list:
    if models is _UNSET:
        models = load_models()
    models = models or {}
    tags = []
    lang = conv.language
    for line in conv.lines:
        if line.speaker == "coach":
            label = _first(_COACH, line.text, lang)
            if "coach" in models and label not in RULE_KEEPS:
                tags.append(Tag(conv.id, line.idx, "coach_move", FROM_COARSE[models["coach"].predict(line.text)],
                                "classifier"))
            else:
                tags.append(Tag(conv.id, line.idx, "coach_move", label or "other", "rule",
                                f"T-{label}-{lang}" if label else f"T-other-{lang}"))
        else:
            if "talk" in models:
                tags.append(Tag(conv.id, line.idx, "participant_talk", models["talk"].predict(line.text), "classifier"))
            else:
                label = _first(_PART, line.text, lang)
                tags.append(Tag(conv.id, line.idx, "participant_talk", label or "neutral", "rule",
                                f"T-{label}-{lang}" if label else f"T-neutral-{lang}"))
        if conv.channel == "text":
            intent = _first(_INTENT, line.text, lang)
            if intent:
                tags.append(Tag(conv.id, line.idx, "text_intent", intent, "rule", f"I-{intent}-{lang}"))
    return tags
