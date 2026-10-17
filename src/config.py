"""PLACEHOLDER label, rule and tier names. Replace with the organizers' exact names (single place to edit)."""
import re

# Tag.kind -> labels (placeholders; CONTRACT.md says exact names come from the organizers' brief)
COACH_RULES = {
    "open_question": {
        "en": r"^\s*(what|how|tell me|help me understand)\b|\b(what|how) (do|did|would|could|has|have)\b",
        "es": r"¿\s*(qué|cómo|cuándo|cuál)\b|^\s*(cuéntame|cuentame)\b",
    },
    "reflection": {
        "en": r"\b(it sounds like|sounds like|you feel|you're feeling|so you)\b",
        "es": r"\b(parece que|suena como|te sientes|entonces tú|entonces tu)\b",
    },
    "affirmation": {
        "en": r"\b(real win|great job|well done|proud of you|that took)\b",
        "es": r"\b(gran logro|buen trabajo|felicidades|orgullosa de ti|orgulloso de ti)\b",
    },
    "ask_permission": {
        "en": r"\b(would you like|may i|is it ok if|can i share)\b",
        "es": r"\b(te gustar[ií]a|puedo|est[aá] bien si)\b",
    },
}
PARTICIPANT_RULES = {
    "change_talk": {
        "en": r"\b(i walked|i want to|i will|i can|i'll|i tried|maybe)\b",
        "es": r"\b(camin[eé]|quiero|voy a|puedo|intent[eé]|quiz[aá]s?)\b",
    },
    "sustain_talk": {
        "en": r"\b(can't|cannot|too tired|no time|skip(ped)?)\b",
        "es": r"\b(no puedo|muy cansad[oa]|no tengo tiempo|no salgo)\b",
    },
}

# Needs-a-human flag rules: (rule_id, tier, pattern per language). Tiers are placeholders.
FLAG_RULES = [
    ("F-CRISIS", "S1", {
        "en": r"\b(want to die|kill myself|end my life|hurt myself)\b",
        "es": r"\b(quiero morir|quitarme la vida|matarme|hacerme da[ñn]o)\b"}),
    ("F-CHEST", "S1", {
        "en": r"\bchest (pain|pressure)\b|\bcan't breathe\b|\bshort(ness)? of breath\b",
        "es": r"\bdolor (de|en el) pecho\b|\bno puedo respirar\b|\bfalta de aire\b"}),
    ("F-SYMPTOM", "S2", {
        "en": r"\b(fever|bleeding|vomiting|new lump|severe pain)\b",
        "es": r"\b(fiebre|sangrado|v[oó]mitos|bulto nuevo|dolor fuerte)\b"}),
    ("F-DISTRESS", "S3", {
        "en": r"\b(hopeless|overwhelmed|can't cope|so alone)\b",
        "es": r"\b(sin esperanza|abrumad[oa]|no puedo m[aá]s|muy sol[oa])\b"}),
]

# Negation cues that, within NEGATION_WINDOW tokens before a match, cancel it.
NEGATIONS = {
    "en": r"\b(no|not|never|without|don't|doesn't|didn't|haven't|hasn't|denies|denied)\b",
    "es": r"\b(no|nunca|ni|sin|jam[aá]s|tampoco)\b",
}
NEGATION_WINDOW = 4
COMPILED = re.compile  # alias so callers can precompile with flags
