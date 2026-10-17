"""Score card: transparent counts and rule-based checklist for one conversation.

Counts are {num, den, lines[]} so the UI can show the evidence. Formulas:
  open_question_share      = open_question lines / (open + closed question lines)
  reflection_to_question   = reflection lines (simple+complex) / question lines
  complex_reflection_share = complex reflections / all reflections
  mi_consistent_share      = coach lines tagged MI-consistent / all coach lines
  mi_inconsistent          = persuade + confront lines / all coach lines
Safety item: yes only if every flag has a responding coach line (flag line plus response line are the evidence).
There is deliberately no single opaque overall number.
"""
import re

from ..config import CHECKLIST_ITEMS, SAFETY_ITEM
from ..flagger.rules import find_response, flag_conversation
from ..schema import Conversation
from ..tagger.rules import tag_conversation

QUESTIONS = ("open_question", "closed_question")
REFLECTIONS = ("simple_reflection", "complex_reflection")
MI_CONSISTENT = ("open_question", "simple_reflection", "complex_reflection", "affirm",
                 "seek_collaboration", "emphasize_autonomy", "ask_permission")
MI_INCONSISTENT = ("persuade", "confront")

# Checklist cues (heuristic, coach lines only), per language.
CUES = {
    "set_agenda": {"en": r"\b(today we|agenda|what would you like to talk about|let'?s talk about)\b",
                   "es": r"\b(hoy vamos|agenda|de qu[eé] te gustar[ií]a hablar|hablemos de)\b"},
    "checked_feelings": {"en": r"\b(how are you feeling|how have you been feeling|how do you feel)\b",
                         "es": r"\b(c[oó]mo te sientes|c[oó]mo te has sentido|c[oó]mo est[aá]s)\b"},
    "reviewed_last_goal": {"en": r"\b(last (week|time)|your goal|you planned|you set)\b",
                           "es": r"\b(la semana pasada|la vez pasada|tu meta|planeaste)\b"},
    "set_new_goal": {"en": r"\b(new goal|this week.{0,20}(will|plan)|plan one more|set a goal)\b",
                     "es": r"\b(nueva meta|esta semana.{0,20}(vas|plan)|planear otra|fijar una meta)\b"},
    "planned_for_barriers": {"en": r"\b(what could get in the way|if .* happens|backup plan|barrier)\b",
                             "es": r"\b(qu[eé] podr[ií]a impedir|si .* pasa|plan b|obst[aá]culo|barrera)\b"},
    "summarized": {"en": r"\b(to sum up|so today|in summary|let me recap)\b",
                   "es": r"\b(en resumen|para resumir|hoy hablamos|repasemos)\b"},
    "set_next_contact": {"en": r"\b(next (call|week|time)|talk again|see you|call you (on|next))\b",
                         "es": r"\b(pr[oó]xima (llamada|semana|vez)|hablamos|nos vemos|te llamo)\b"},
}
_CUES = {k: {l: re.compile(p, re.IGNORECASE) for l, p in v.items()} for k, v in CUES.items()}


def _count(num_lines, den_lines):
    return {"num": len(num_lines), "den": len(den_lines), "lines": sorted(num_lines)}


def score_conversation(conv: Conversation) -> dict:
    tags = tag_conversation(conv)
    moves = {}
    for t in tags:
        if t.kind == "coach_move":
            moves.setdefault(t.label, []).append(t.line_idx)
    pick = lambda labels: [i for l in labels for i in moves.get(l, [])]
    coach_lines = [l.idx for l in conv.lines if l.speaker == "coach"]
    questions, reflections = pick(QUESTIONS), pick(REFLECTIONS)
    counts = {
        "open_question_share": _count(moves.get("open_question", []), questions),
        "reflection_to_question": _count(reflections, questions),
        "complex_reflection_share": _count(moves.get("complex_reflection", []), reflections),
        "mi_consistent_share": _count(pick(MI_CONSISTENT), coach_lines),
        "mi_inconsistent": _count(pick(MI_INCONSISTENT), coach_lines),
    }
    checklist = {}
    for item in CHECKLIST_ITEMS:
        rx = _CUES[item][conv.language]
        ev = [l.idx for l in conv.lines if l.speaker == "coach" and rx.search(l.text)]
        checklist[item] = {"value": "yes" if ev else "no", "evidence_lines": ev}
    flags = flag_conversation(conv)
    if not flags:
        checklist[SAFETY_ITEM] = {"value": "n/a", "evidence_lines": []}
    else:
        resp = [find_response(conv, f.line_idx) for f in flags]
        evidence = sorted({f.line_idx for f in flags} | {r for r in resp if r is not None})
        checklist[SAFETY_ITEM] = {"value": "yes" if all(r is not None for r in resp) else "no", "evidence_lines": evidence}
    return {"conv_id": conv.id, "counts": counts, "checklist": checklist}
