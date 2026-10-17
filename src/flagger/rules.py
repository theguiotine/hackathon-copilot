"""Needs-a-human flagger with a negation guard and the 'unhandled' rule.

Only participant lines flag. A match is dropped when a negation cue sits within NEGATION_WINDOW
tokens before it (e.g. Spanish "no tengo dolor de pecho"). coach_responded is True when a later
coach line exists; unhandled flags (coach_responded False) sort first within a tier.
"""
import re

from ..config import FLAG_RULES, NEGATION_WINDOW, NEGATIONS
from ..schema import Conversation, Flag

_FLAGS = [(rid, tier, {l: re.compile(p, re.IGNORECASE) for l, p in pats.items()}) for rid, tier, pats in FLAG_RULES]
_NEG = {l: re.compile(p, re.IGNORECASE) for l, p in NEGATIONS.items()}
_TOKEN = re.compile(r"[\w']+", re.UNICODE)


def is_negated(text: str, start: int, lang: str) -> bool:
    """True if a negation cue appears in the NEGATION_WINDOW tokens before text[start:]."""
    window = _TOKEN.findall(text[:start])[-NEGATION_WINDOW:]
    return any(_NEG[lang].fullmatch(tok) for tok in window)


def flag_conversation(conv: Conversation) -> list:
    last_coach = max((l.idx for l in conv.lines if l.speaker == "coach"), default=-1)
    flags = []
    for line in conv.lines:
        if line.speaker != "participant":
            continue
        for rid, tier, pats in _FLAGS:
            m = pats[conv.language].search(line.text)
            if m and not is_negated(line.text, m.start(), conv.language):
                flags.append(Flag(conv.id, line.idx, tier, rid, line.text, True, last_coach > line.idx))
    return sorted(flags, key=lambda f: (f.tier, f.coach_responded, f.conv_id, f.line_idx))
