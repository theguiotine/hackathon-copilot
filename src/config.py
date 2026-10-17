"""PLACEHOLDER label, rule and tier names. Replace with the organizers' exact names (single place to edit)."""
import re

# Label names from the organizers' brief (names only). Patterns are our own heuristics.
COACH_MOVES = ("open_question", "closed_question", "simple_reflection", "complex_reflection", "affirm",
               "seek_collaboration", "emphasize_autonomy", "ask_permission", "give_information",
               "persuade", "confront", "other")
PARTICIPANT_TALK = ("change", "sustain", "neutral")
TEXT_INTENTS = ("reminder", "check_in", "nudge", "progress_report", "barrier", "encouragement", "question",
                "answer", "scheduling", "thanks", "minor_symptom", "concern", "escalation")
CHECKLIST_ITEMS = ("set_agenda", "checked_feelings", "reviewed_last_goal", "set_new_goal",
                   "planned_for_barriers", "summarized", "set_next_contact")
SAFETY_ITEM = "safety_issue_handled"  # yes / no / n/a

# Coach-move rules in PRIORITY order: first match wins, no match -> "other".
COACH_RULES = [
    ("confront", {"en": r"\b(you need to admit|that'?s not true|you always|you never|stop making excuses)\b",
                  "es": r"\b(tienes que admitir|eso no es verdad|siempre haces|nunca haces|deja las excusas)\b"}),
    ("persuade", {"en": r"\b(you should|you must|you have to|i('d| would) recommend you|why don'?t you just)\b",
                  "es": r"\b(deber[ií]as|tienes que|debes|te recomiendo que|por qu[eé] no simplemente)\b"}),
    ("emphasize_autonomy", {"en": r"\b(it'?s up to you|your (choice|decision)|you decide|you know best)\b",
                            "es": r"\b(depende de ti|es tu decisi[oó]n|t[uú] decides|t[uú] sabes mejor)\b"}),
    ("affirm", {"en": r"\b(real win|great job|well done|proud of you|that took (courage|effort)|good for you)\b",
                "es": r"\b(gran logro|buen trabajo|felicidades|orgullos[oa] de ti|qu[eé] bien|muy bien)\b"}),
    ("complex_reflection", {"en": r"\b(it sounds like|sounds like|you feel|you'?re feeling|so you)\b.*\b(because|which|while|but|and yet|means)\b",
                            "es": r"\b(parece que|suena como|te sientes|entonces t[uú])\b.*\b(porque|mientras|pero|lo que|significa)\b"}),
    ("simple_reflection", {"en": r"\b(it sounds like|sounds like|you feel|you'?re feeling|so you|you said)\b",
                           "es": r"\b(parece que|suena como|te sientes|entonces t[uú]|dijiste)\b"}),
    ("seek_collaboration", {"en": r"\b(let'?s|together|what do you think about|how about we|shall we)\b",
                            "es": r"\b(vamos a|juntos|juntas|qu[eé] opinas|qu[eé] te parece si)\b"}),
    ("ask_permission", {"en": r"\b(would you like|may i|is it ok if|can i share|do you mind if)\b",
                        "es": r"\b(te gustar[ií]a|puedo|est[aá] bien si|te molesta si)\b"}),
    ("open_question", {"en": r"(^|[.!?,]\s+)(what|how|why|when|which|tell me|help me understand)\b",
                       "es": r"(^|[.!?,¿]\s*)(qu[eé]|c[oó]mo|cu[aá]ndo|cu[aá]l|por qu[eé]|cu[eé]ntame)\b"}),
    ("closed_question", {"en": r"(^|[.!?]\s+)(did|do(?! not\b)|does|are|is|were|was|have|has|will|can|could)\b",
                         "es": r"(^|[.!?¿]\s*)(has|ha|est[aá]s?|fuiste|tienes|puedes|pudiste|hiciste|vas|quieres|caminaste)\b"}),
    ("give_information", {"en": r"\b(it is recommended|studies show|one option is|the clinic|you can call|your next appointment)\b",
                          "es": r"\b(se recomienda|los estudios|una opci[oó]n es|la cl[ií]nica|puedes llamar|tu pr[oó]xima cita)\b"}),
]
PARTICIPANT_RULES = [
    ("sustain", {"en": r"\b(can'?t|cannot|too tired|no time|skipp?ed?|almost skipped|don'?t want to|won'?t)\b",
                 "es": r"\b(no puedo|muy cansad[oa]|cansad[oa]|no tengo tiempo|no salgo|no quiero)\b"}),
    ("change", {"en": r"\b(i walked|i want to|i will|i can|i'll|i tried|maybe|i'?m going to)\b",
                "es": r"\b(camin[eé]|quiero|voy a|puedo|intent[eé]|quiz[aá]s?)\b"}),
]
# Text-channel intents (heuristic subset; unmatched lines get no intent tag).
TEXT_INTENT_RULES = [
    ("scheduling", {"en": r"\b(reschedule|schedule|appointment|tomorrow at|see you (on|at))\b",
                    "es": r"\b(reprogramar|programar|cita|ma[ñn]ana a las|nos vemos)\b"}),
    ("thanks", {"en": r"\b(thanks|thank you)\b", "es": r"\b(gracias)\b"}),
    ("reminder", {"en": r"\b(reminder|don'?t forget|remember to)\b", "es": r"\b(recordatorio|no olvides|recuerda)\b"}),
    ("encouragement", {"en": r"\b(you can do it|keep it up|great job)\b", "es": r"\b(t[uú] puedes|sigue as[ií]|buen trabajo)\b"}),
    ("check_in", {"en": r"\b(how are you|checking in|how'?s your week)\b", "es": r"\b(c[oó]mo est[aá]s|quer[ií]a saber c[oó]mo|c[oó]mo va tu semana)\b"}),
]

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

# Negation scope ends at these boundaries (punctuation or contrast words).
CLAUSE_BOUNDARY = {
    "en": r"[,;:.!?]|\b(but|however|yet|although|though)\b",
    "es": r"[,;:.!?¿¡]|\b(pero|aunque|sin embargo)\b",
}
# A coach line counts as responding to a flag only if it shows acknowledgement or action.
RESPONSE_CUES = {
    "en": r"\b(thank|sorry|i hear|i'?m glad you told|call|nurse|team|doctor|911|emergency|follow up|let me|i('ll| will)|right now)\b",
    "es": r"\b(gracias|lamento|siento|te escucho|llam|enfermer|equipo|m[eé]dic|911|emergencia|seguimiento|d[eé]jame|voy a|ahora mismo)\b",
}
