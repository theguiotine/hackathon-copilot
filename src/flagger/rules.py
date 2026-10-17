"""Needs-a-human flagger with a negation guard and the 'unhandled' rule.

Only participant lines flag. Every match of a rule is checked; a match is dropped when a negation cue
sits in the same clause within NEGATION_WINDOW tokens before it (clause = since the last punctuation
or contrast word). A rule's own words are never treated as the cue, so "no puedo respirar" stands.
coach_responded is True only when one of the next RESPONSE_LOOKAHEAD coach lines shows acknowledgement or a
concrete action (RESPONSE_CUES); unhandled flags (coach_responded False) sort first within a tier.
"""
import re

from ..config import (CLAUSE_BOUNDARY, CLAUSE_STARTERS, FLAG_RULES, NEGATION_WINDOW, NEGATIONS, RESPONSE_CUES,
                      RESPONSE_LOOKAHEAD)
from ..schema import Conversation, Flag

_FLAGS = [(rid, tier, {l: re.compile(p, re.IGNORECASE) for l, p in pats.items()}) for rid, tier, pats in FLAG_RULES]
_NEG = {l: re.compile(p, re.IGNORECASE) for l, p in NEGATIONS.items()}
_BOUND = {l: re.compile(p, re.IGNORECASE) for l, p in CLAUSE_BOUNDARY.items()}
_START = {l: re.compile(p, re.IGNORECASE) for l, p in CLAUSE_STARTERS.items()}
_RESP = {l: re.compile(p, re.IGNORECASE) for l, p in RESPONSE_CUES.items()}
_TOKEN = re.compile(r"[\w']+", re.UNICODE)


def is_negated(text: str, start: int, lang: str) -> bool:
    """True if a negation cue sits in the current clause, within NEGATION_WINDOW tokens before text[start:].

    A hard boundary (; : . ! ? or a contrast word) always opens a new clause. A comma opens one only if
    a new clause starts after it ("No fiebre, tengo dolor") or the text before it is a bare negation
    ("No, no puedo"); otherwise it is a list comma and the denial still covers what follows.
    """
    before = text[:start]
    last = None
    for last in _BOUND[lang].finditer(before):
        pass
    clause = before[last.end():] if last else before
    parts = clause.split(",")
    keep = len(parts) - 1
    while keep > 0:
        head = " ".join(parts[:keep])
        tail = ",".join(parts[keep:])
        head_tokens = _TOKEN.findall(head)
        interjection = len(head_tokens) == 1 and _NEG[lang].fullmatch(head_tokens[0]) is not None
        if _START[lang].match(tail) or interjection:
            break
        keep -= 1
    clause = ",".join(parts[keep:]) if keep < len(parts) else clause
    window = _TOKEN.findall(clause)[-NEGATION_WINDOW:]
    return any(_NEG[lang].fullmatch(tok) for tok in window)


def self_negating(phrase: str, lang: str) -> bool:
    """True when the rule's own phrase starts with a negation ("no puedo respirar"): the phrase reports
    the symptom, so a negation earlier in the sentence does not cancel it."""
    first = _TOKEN.findall(phrase)[:1]
    return bool(first) and _NEG[lang].fullmatch(first[0]) is not None


def find_response(conv: Conversation, line_idx: int):
    """Index of the first of the next RESPONSE_LOOKAHEAD coach lines that responds to the flag, or None."""
    seen = 0
    for line in conv.lines:
        if line.idx > line_idx and line.speaker == "coach":
            if _RESP[conv.language].search(line.text):
                return line.idx
            seen += 1
            if seen >= RESPONSE_LOOKAHEAD:
                break
    return None


def flag_conversation(conv: Conversation) -> list:
    flags = []
    for line in conv.lines:
        if line.speaker != "participant":
            continue
        for rid, tier, pats in _FLAGS:
            for m in pats[conv.language].finditer(line.text):
                if self_negating(m.group(0), conv.language) or not is_negated(line.text, m.start(), conv.language):
                    responded = find_response(conv, line.idx) is not None
                    flags.append(Flag(conv.id, line.idx, tier, rid, line.text, True, responded))
                    break
    return sorted(flags, key=lambda f: (f.tier, f.coach_responded, f.conv_id, f.line_idx))
