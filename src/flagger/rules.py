"""Needs-a-human flagger with a negation guard and the 'unhandled' rule.

Only participant lines flag. Every match of a rule is checked; a match is dropped when a negation cue
sits in the same clause within NEGATION_WINDOW tokens before it (clause = since the last punctuation
or contrast word). A rule's own words are never treated as the cue, so "no puedo respirar" stands.
coach_responded is True only when the first coach line after the flag shows acknowledgement or action
(RESPONSE_CUES); unhandled flags (coach_responded False) sort first within a tier.
"""
import re

from ..config import CLAUSE_BOUNDARY, FLAG_RULES, NEGATION_WINDOW, NEGATIONS, RESPONSE_CUES
from ..schema import Conversation, Flag

_FLAGS = [(rid, tier, {l: re.compile(p, re.IGNORECASE) for l, p in pats.items()}) for rid, tier, pats in FLAG_RULES]
_NEG = {l: re.compile(p, re.IGNORECASE) for l, p in NEGATIONS.items()}
_BOUND = {l: re.compile(p, re.IGNORECASE) for l, p in CLAUSE_BOUNDARY.items()}
_RESP = {l: re.compile(p, re.IGNORECASE) for l, p in RESPONSE_CUES.items()}
_TOKEN = re.compile(r"[\w']+", re.UNICODE)


def is_negated(text: str, start: int, lang: str) -> bool:
    """True if a negation cue sits in the current clause, within NEGATION_WINDOW tokens before text[start:]."""
    before = text[:start]
    last = None
    for last in _BOUND[lang].finditer(before):
        pass
    clause = before[last.end():] if last else before
    window = _TOKEN.findall(clause)[-NEGATION_WINDOW:]
    return any(_NEG[lang].fullmatch(tok) for tok in window)


def find_response(conv: Conversation, line_idx: int):
    """Index of the coach line that responds to the flag at line_idx, or None."""
    for line in conv.lines:
        if line.idx > line_idx and line.speaker == "coach":
            return line.idx if _RESP[conv.language].search(line.text) else None
    return None


def flag_conversation(conv: Conversation) -> list:
    flags = []
    for line in conv.lines:
        if line.speaker != "participant":
            continue
        for rid, tier, pats in _FLAGS:
            for m in pats[conv.language].finditer(line.text):
                if not is_negated(line.text, m.start(), conv.language):
                    responded = find_response(conv, line.idx) is not None
                    flags.append(Flag(conv.id, line.idx, tier, rid, line.text, True, responded))
                    break
    return sorted(flags, key=lambda f: (f.tier, f.coach_responded, f.conv_id, f.line_idx))
