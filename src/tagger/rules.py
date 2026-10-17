"""Rule tagger EN+ES: coach moves and participant talk, one Tag per matching rule per line."""
import re

from ..config import COACH_RULES, PARTICIPANT_RULES
from ..schema import Conversation, Tag

_C = {
    sp: {(kind, lang): re.compile(pat, re.IGNORECASE) for kind, langs in rules.items() for lang, pat in langs.items()}
    for sp, rules in (("coach", COACH_RULES), ("participant", PARTICIPANT_RULES))
}


def tag_conversation(conv: Conversation) -> list:
    tags = []
    for line in conv.lines:
        for (label, lang), rx in _C[line.speaker].items():
            if lang == conv.language and rx.search(line.text):
                kind = "coach_move" if line.speaker == "coach" else "participant_talk"
                tags.append(Tag(conv.id, line.idx, kind, label, "rule", f"T-{label}-{lang}"))
    return tags
