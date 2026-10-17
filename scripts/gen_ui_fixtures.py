"""Regenerate the UI's demo fixtures from OUR engine (fictional transcripts only, no real data).

Reads the existing CallLine / CoachingCall / Scorecard fixtures in ui/src/infrastructure/memory/fixtures/ (Archie's
invented calls), runs our tagger, flagger and score card on each call, and rewrites:
  callLine (coachMove from our tags), humanReviewFlag (our flags, undecided), checklistItem (our checklist),
  scorecard (score and reflectionRatio from our counts), coachingCall (flagCount).
Run:  python3 scripts/gen_ui_fixtures.py        (idempotent; uses the rule tagger so output is deterministic)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
FX = ROOT / "ui" / "src" / "infrastructure" / "memory" / "fixtures"

from src.config import CHECKLIST_ITEMS  # noqa: E402
from src.flagger.rules import flag_conversation  # noqa: E402
from src.schema import Conversation  # noqa: E402
from src.score.card import score_conversation  # noqa: E402
from src.tagger.rules import tag_conversation  # noqa: E402

MOVE_ENUM = {"open_question": "OPEN_QUESTION", "simple_reflection": "REFLECTION", "complex_reflection": "REFLECTION",
             "affirm": "AFFIRMATION", "persuade": "ADVICE", "give_information": "ADVICE"}
LABELS = {"set_agenda": "Sets the agenda for the call", "checked_feelings": "Checks in on feelings",
          "reviewed_last_goal": "Reviews the last goal", "set_new_goal": "Sets a new goal",
          "planned_for_barriers": "Plans for barriers", "summarized": "Summarizes the call",
          "set_next_contact": "Sets the next contact"}
REASONS = {"F-CRISIS": "The participant may be describing thoughts of harming themselves.",
           "F-CHEST": "The participant mentions chest pain or trouble breathing.",
           "F-SYMPTOM": "The participant mentions a symptom (fever, bleeding, vomiting, new lump or severe pain).",
           "F-DISTRESS": "The participant sounds overwhelmed, hopeless or alone."}
FORMULA = "Score = (open questions + reflections + affirmations) / total coach moves × 100, minus 5 points per unresolved S2 flag."

# Invented demo transcripts (fictional people and lines) that exercise the engine: unhandled and handled flags in
# three tiers, plus denials that must stay quiet. C = coach, P = participant.
DEMO = {
    "cc-001": [("C", "Hola Marcos, ¿cómo te sentiste esta semana con tus caminatas?"), ("P", "Caminé dos veces, pero tuve vómitos el martes."),
               ("C", "Gracias por decírmelo. Voy a avisar a la enfermera de tu equipo hoy."), ("P", "Gracias, quiero volver a caminar el domingo."),
               ("C", "Parece que tienes ganas de intentarlo. ¿Qué podría impedirlo?"), ("P", "Quizás el cansancio, pero voy a probar.")],
    "cc-002": [("C", "¿Qué notaste en las noches entre semana?"), ("P", "Llego cansada y termino picando algo en el sofá."),
               ("C", "Llegar agotada hace que las decisiones sean más difíciles. Es comprensible."), ("P", "Esta noche tengo dolor de pecho."),
               ("C", "Entiendo. ¿Te gustaría planear una merienda para mañana?"), ("P", "Sí, algo con fruta.")],
    "cc-003": [("C", "How has your bedtime routine been this week?"), ("P", "Better. No fever and no chest pain, just tired."),
               ("C", "It sounds like the screen cutoff is helping. What made it easier?"), ("P", "I put my phone in the kitchen.")],
    "cc-004": [("C", "How have your blood pressure readings looked?"), ("P", "I have had shortness of breath and a fever since last night."),
               ("C", "How is the diet change going?"), ("P", "I can't cope with the new meal plan, I feel hopeless."),
               ("C", "You should follow the plan exactly."), ("P", "Okay.")],
    "cc-005": [("C", "¿Cómo te has sentido con la natación?"), ("P", "Me siento abrumada y muy sola esta semana."),
               ("C", "Siento mucho que te sientas así. Voy a llamarte mañana y avisar al equipo de cuidado."), ("P", "Gracias, lo necesito.")],
    "cc-006": [("C", "How did the weekend gatherings go?"), ("P", "I felt overwhelmed and I had a few drinks anyway."),
               ("C", "That took courage to share. What would help next time?"), ("P", "Maybe I can bring a friend.")],
    "cc-013": [("C", "Today we will talk about your sleep schedule. How are you feeling about it?"), ("P", "My weekends are slipping, I stay up late."),
               ("C", "It sounds like weekends feel free, but then Mondays are hard because you are tired. What could get in the way of a steadier bedtime?"),
               ("P", "Friends texting late, but I want to try a cutoff."), ("C", "That took effort to say. Let's set a new goal together: phone away at eleven this week."),
               ("P", "I will do that."), ("C", "To sum up, you will set a phone cutoff at eleven. I will call you next week to hear how it went.")],
    "cc-009": [("C", "¿Cómo va la práctica de respiración antes del examen?"), ("P", "Bien. No tengo fiebre, vómitos ni sangrado, solo nervios."),
               ("C", "Parece que la respiración ayuda porque te calma antes de estudiar. ¿Qué más ayuda?"), ("P", "Caminar un poco.")],
    "cc-010": [("C", "Did you notice glucose spikes after dinner this week?"), ("P", "Yes, and I had bleeding from a cut that will not stop."),
               ("C", "Let's look at the dinner plan together. What do you think about smaller portions?"), ("P", "I can try that.")],
}


def parse_array(path):
    text = path.read_text(encoding="utf-8")
    rows = []
    for block in re.findall(r"\n  \{\n(.*?)\n  \}", text, flags=re.S):
        row = {}
        for m in re.finditer(r"^\s+(\w+): (.*?),?$", block, flags=re.M):
            v = m.group(2).strip()
            row[m.group(1)] = json.loads(v) if v[:1] in '"[' or re.fullmatch(r"-?\d+(\.\d+)?", v) or v in ("true", "false") else v
        rows.append(row)
    return text, rows


def write_array(path, text, rows):
    head = text[: text.index("= [") + 3]
    body = ",\n".join("  {\n" + "\n".join(f"    {k}: {json.dumps(v, ensure_ascii=False)}," for k, v in r.items()) + "\n  }" for r in rows)
    path.write_text(head + "\n" + body + "\n];\n", encoding="utf-8")


def main():
    _, calls = parse_array(FX / "coachingCall.fixture.ts")
    _, lines = parse_array(FX / "callLine.fixture.ts")
    _, cards = parse_array(FX / "scorecard.fixture.ts")
    call_text, _ = parse_array(FX / "coachingCall.fixture.ts")
    by_call = {}
    n = 0
    for call in calls:
        if call["id"] in DEMO:
            for i, (who, text) in enumerate(DEMO[call["id"]], 1):
                n += 1
                by_call.setdefault(call["id"], []).append({"id": f"cl-{n:03d}", "callId": call["id"], "lineNumber": i,
                                                           "speaker": "COACH" if who == "C" else "PARTICIPANT", "text": text})
    for l in lines:
        if l["callId"] not in DEMO:
            n += 1
            by_call.setdefault(l["callId"], []).append(dict(l, id=f"cl-{n:03d}"))

    new_lines, new_flags, new_items, flag_n = [], [], [], 0
    results = {}
    for call in calls:
        rows = sorted(by_call.get(call["id"], []), key=lambda r: r["lineNumber"])
        if not rows:
            results[call["id"]] = None
            continue
        conv = Conversation.from_dict({"id": call["id"], "channel": "call", "language": call["language"].lower(), "lines": [
            {"idx": i, "speaker": "coach" if r["speaker"] == "COACH" else "participant", "text": r["text"]} for i, r in enumerate(rows)]})
        tags = {t.line_idx: t for t in tag_conversation(conv, models=None) if t.kind == "coach_move"}
        flags = flag_conversation(conv)
        score = score_conversation(conv)
        for i, r in enumerate(rows):
            out = {k: v for k, v in r.items() if k != "coachMove"}
            if r["speaker"] == "COACH":
                out["coachMove"] = MOVE_ENUM.get(tags[i].label, "NONE")
            new_lines.append(out)
        for f in flags:
            flag_n += 1
            new_flags.append({"id": f"hf-{flag_n:03d}", "lineId": rows[f.line_idx]["id"], "severity": f.tier,
                              "reason": f"{REASONS[f.rule_id]} Rule {f.rule_id}, negation checked. "
                                        f"{'A coach reply acknowledged it.' if f.coach_responded else 'No coach reply handled it yet.'}",
                              "createdAt": call["completedAt"]})
        results[call["id"]] = (conv, flags, score)

    _, old_items = parse_array(FX / "checklistItem.fixture.ts")
    regenerated = {c["id"] for c in cards if results.get(c["callId"])}
    kept = [i for i in old_items if i["scorecardId"] not in regenerated]
    item_n = 0
    for card in cards:
        res = results.get(card["callId"])
        if not res:
            continue
        conv, flags, score = res
        moves = [t.label for t in tag_conversation(conv, models=None) if t.kind == "coach_move"]
        good = sum(1 for m in moves if m in ("open_question", "simple_reflection", "complex_reflection", "affirm"))
        refl = sum(1 for m in moves if m.endswith("reflection"))
        unresolved_s2 = sum(1 for f in flags if f.tier == "S2" and not f.coach_responded)
        card["score"] = max(0, round(100 * good / len(moves) - 5 * unresolved_s2)) if moves else 0
        card["reflectionRatio"] = round(refl / len(moves), 2) if moves else 0
        for item in CHECKLIST_ITEMS:
            item_n += 1
            new_items.append({"id": f"ci-g{item_n:03d}", "scorecardId": card["id"], "behavior": LABELS[item],
                              "observed": score["checklist"][item]["value"] == "yes", "weight": 1})

    new_items = kept + new_items
    for call in calls:
        res = results.get(call["id"])
        call["flagCount"] = len(res[1]) if res else 0

    for name, rows in (("callLine", new_lines), ("humanReviewFlag", new_flags), ("checklistItem", new_items),
                       ("scorecard", cards), ("coachingCall", calls)):
        path = FX / f"{name}.fixture.ts"
        text, _ = parse_array(path)
        write_array(path, text, rows)
    print(f"calls with lines: {sum(1 for r in results.values() if r)}; lines {len(new_lines)}; flags {len(new_flags)}; "
          f"checklist items {len(new_items)}; scorecards {len(cards)}")


if __name__ == "__main__":
    main()
