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
        "en": r"\b(want to die|kill myself|killing myself|end my life|end it all|hurt myself|harm myself|better off dead|(don'?t|do not) want to (live|be here|be alive)|suicid\w+)\b",
        "es": r"\b(quiero morir|me quiero morir|quitarme la vida|matarme|hacerme da[ñn]o|acabar con todo|no quiero (vivir|seguir viviendo)|quiero desaparecer|ya no quiero estar aqu[ií]|suicid\w+)\b"}),
    ("F-CHEST", "S1", {
        "en": (r"\bchest (pain|pressure|tightness|is tight|feels? (really |very |so )?(tight|heavy|funny|squeezed|crushed))\b"
               r"|\b(tight|heavy|crushing|squeezing|pressure|pain) (in|on) (my )?chest\b|\bchest (hurts|aches|burns)\b"
               r"|\b(can'?t|cannot|can not|couldn'?t|unable to) (breathe|catch (my|a) breath|get (enough )?(air|a breath)|take a (full )?breath)\b"
               r"|\b(hard|trouble|difficult\w*|struggling) (to )?breath(e|ing)\b|\b(short|out) of breath\b|\bshortness of breath\b|\bgasping\b"
               r"|\bheart (feels? (really |very )?(tight|squeezed)|is pounding hard)\b"),
        "es": (r"\bdolor (de|en el|en mi) pecho\b|\bpecho (apretado|oprimido|pesado)\b|\bopresi[oó]n (en el |del )?pecho\b"
               r"|\b(me )?(aprieta|aprieto|oprime|pesa|duele|arde)n? (mucho )?(el )?pecho\b|\b(me )?aprieta(n)? el coraz[oó]n\b|\bcoraz[oó]n (muy |bien )?(apretado|oprimido)\b"
               r"|\bno (puedo|logro|consigo) (respirar|agarrar aire|coger aire|tomar aire)\b|\bno me entra el aire\b|\bme cuesta (mucho )?respirar\b"
               r"|\b(me )?falta(n)? (de )?(el )?(aire|aliento|respiraci[oó]n)\b|\bfalta de aire\b|\bme ahogo\b|\bsin aliento\b|\bse me va el aire\b")}),
    ("F-SYMPTOM", "S2", {
        "en": (r"\b(fever|bleeding|vomiting|vomit|new lump|a lump|severe pain|chills|night sweats)\b"
               r"|\b(throwing up|threw up|coughing up blood|blood in (my )?(stool|urine|cough)|can'?t (stop|keep) (bleeding|vomiting|food down|anything down))\b"
               r"|\b(pass(ing)? out|going to pass out|faint(ing|ed)?|black(ing)? out|dizzy and weak)\b|\bworst pain\b|\bcut that will not stop\b"),
        "es": (r"\b(fiebre|calentura|sangrado|v[oó]mitos?|bulto nuevo|un bulto|dolor (muy )?fuerte|escalofr[ií]os)\b"
               r"|\b(me )?(estoy )?vomit\w+|\b(devuelvo|devolviendo)\b|\bsangre (en|al) (la orina|el excremento|las heces|toser)\b|\bme sale sangre\b|\btosiendo sangre\b"
               r"|\b(me voy a desmayar|me desmay[oóé]|desmay\w+|me desvanezco|mareo fuerte|muy maread[oa])\b|\bno puedo (comer|retener|aguantar) nada\b")}),
    ("F-DISTRESS", "S3", {
        "en": r"\b(hopeless|overwhelmed|can'?t cope|so alone|can'?t go on|can'?t take it any ?more|giving up|want to disappear|nothing matters|no point)\b",
        "es": r"\b(sin esperanza|abrumad[oa]|no puedo m[aá]s|muy sol[oa]|no aguanto m[aá]s|ya no aguanto|me quiero rendir|nada tiene sentido|sin ganas de vivir|me siento perdid[oa])\b"}),
]

# A match is NOT about the participant right now when its sentence is about another person or about long ago.
OTHER_PERSON = {
    "en": r"\b(my (dad|father|mom|mother|sister|brother|friend|wife|husband|son|daughter|neighbou?r|grand(ma|mother|pa|father)|aunt|uncle|cousin|coworker|boss)|he|she|they|someone|somebody)\b",
    "es": r"\b(mi (mam[aá]|pap[aá]|madre|padre|hermano|hermana|amig[oa]|espos[oa]|marido|mujer|hij[oa]|vecin[oa]|abuel[oa]|t[ií][oa]|prim[oa]|jefe)|él|ella|ellos|ellas|alguien)\b",
}
LONG_AGO = {
    "en": r"\b(last year|years? ago|months? ago|when I was (a kid|little|young)|as a (kid|child)|a long time ago)\b",
    "es": r"\b(el a[ñn]o pasado|hace (\w+ )?(a[ñn]os|meses)|cuando era (ni[ñn][oa]|chic[oa]|joven|peque[ñn][oa])|a[ñn]os atr[aá]s)\b",
}

# Negation cues that, within NEGATION_WINDOW tokens before a match, cancel it.
NEGATIONS = {
    "en": r"\b(no|not|never|without|don't|doesn't|didn't|haven't|hasn't|denies|denied)\b",
    "es": r"\b(no|nunca|ni|sin|jam[aá]s|tampoco)\b",
}
NEGATION_WINDOW = 4
COMPILED = re.compile  # alias so callers can precompile with flags

# Negation scope ends at these hard boundaries; a comma ends it only when a new clause starts after it
# (see CLAUSE_STARTERS) or when the text before the comma is just a negation ("No, ...").
CLAUSE_BOUNDARY = {
    "en": r"[;:.!?]|\b(but|however|yet|although|though)\b",
    "es": r"[;:.!?¿¡]|\b(pero|aunque|sin embargo)\b",
}
CLAUSE_STARTERS = {
    "en": r"^\s*(i|i'm|i've|we|he|she|they|it|my|now|today|also|and then|then)\b",
    "es": r"^\s*(yo|tengo|tuve|hoy|ahora|estoy|siento|me|mi|tambi[eé]n|luego|entonces)\b",
}
# A coach line counts as responding to a flag only if it shows acknowledgement or a concrete action.
# Generic intent ("I will", "voy a", "let me") is NOT enough on its own.
RESPONSE_CUES = {
    "en": r"\b(thank(s| you) for (telling|sharing|letting)|i'?m (so )?sorry|i hear you|i'?m glad you told|call(ing)?|nurse|doctor|911|emergency|care team|(tell|notify|alert) (your|the) (team|nurse|doctor)|follow(ing)? up|check(ing)? on you|are you safe|go to the (er|hospital))\b",
    "es": r"\b(gracias por (decirme|dec[ií]rmelo|contarme|cont[aá]rmelo|avisarme|compartir)|avis\\w* a (tu|el|su) equipo|lamento|siento (mucho )?que|te escucho|me alegra que me lo dijeras|llam\w*|enfermer\w*|m[eé]dic\w*|doctor\w*|911|emergencia|equipo de cuidado|seguimiento|est[aá]s a salvo|ve al hospital|urgencias)\b",
}
# Look this many coach lines after a flag for a response.
RESPONSE_LOOKAHEAD = 3
