"""Rule tagger EN+ES. One coach_move per coach line (first matching rule, else "other"),
one participant_talk per participant line (default "neutral"), plus text_intent on text-channel lines."""
import re

from ..config import COACH_RULES, PARTICIPANT_RULES, TEXT_INTENT_RULES
from ..schema import Conversation, Tag


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


def tag_conversation(conv: Conversation) -> list:
    tags = []
    lang = conv.language
    for line in conv.lines:
        if line.speaker == "coach":
            label = _first(_COACH, line.text, lang)
            tags.append(Tag(conv.id, line.idx, "coach_move", label or "other", "rule",
                            f"T-{label}-{lang}" if label else f"T-other-{lang}"))
        else:
            label = _first(_PART, line.text, lang)
            tags.append(Tag(conv.id, line.idx, "participant_talk", label or "neutral", "rule",
                            f"T-{label}-{lang}" if label else f"T-neutral-{lang}"))
        if conv.channel == "text":
            intent = _first(_INTENT, line.text, lang)
            if intent:
                tags.append(Tag(conv.id, line.idx, "text_intent", intent, "rule", f"I-{intent}-{lang}"))
    return tags
