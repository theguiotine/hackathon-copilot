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
        "es": r"\b(quiero morir|quiero morirme|me quiero morir|quiero matarme|quitarme la vida|matarme|hacerme da[ñn]o|acabar con todo|no quiero (vivir|seguir viviendo)|quiero desaparecer|ya no quiero estar aqu[ií]|suicid\w+)\b"}),
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
               r"|\b(me )?(estoy )?vomit\w+|\b(devuelvo|devolviendo)\b|\bsangre (en|al) (la orina|el excremento|las heces|toser)\b|\bme sale sangre\b|\btosiendo sangre\b|\b(estoy |sigo |sigue )?sangrando\b|\bsangro (mucho|bastante)\b"
               r"|\b(me voy a desmayar|me desmay[oóé]|desmay\w+|me desvanezco|mareo fuerte|muy maread[oa])\b|\bno puedo (comer|retener|aguantar) nada\b")}),
    ("F-DISTRESS", "S3", {
        "en": r"\b(hopeless|overwhelmed|can'?t cope|so alone|can'?t go on|can'?t take it any ?more|giving up|want to disappear|nothing matters|no point)\b",
        "es": r"\b(sin esperanza|abrumad[oa]|no puedo m[aá]s|muy sol[oa]|no aguanto m[aá]s|ya no aguanto|me quiero rendir|nada tiene sentido|sin ganas de vivir|me siento perdid[oa])\b"}),
]

# Expanded natural variants of the EXISTING flag ideas (added Sat Oct 17 2026 17:2x, after a live test found
# "I'm dying" and "chest pains" unflagged). Same rule ids and tiers; wording is "a person should see this
# today", never a diagnosis. The negation guard, other-person and long-ago filters in flagger/rules.py still apply.
_AP = "['’]?"
_EXTRA_FLAG_PATTERNS = {
    "F-CRISIS": {
        "en": (
            r"\bi(?:" + _AP + r"m| am| feel like i" + _AP + r"m| feel like i am| think i" + _AP + r"m| think i am) (?:dying|going to die|gonna die)\b"
            r"|\b(?:wanna|want to|going to|gonna) die\b"
            r"|\b(?:ending|end|ended) (?:it all|my life|everything)\b"
            r"|\b(?:take|taking|took) my own life\b"
            r"|\b(?:(?:everyone|everybody|they|you|people|my family)(?:" + _AP + r"d| would| will)(?: all)? be )?better off without me\b|\b(?:hurting|harming) myself\b"
            r"|\bwant to (?:disappear|vanish)\b"
            r"|\bwish i (?:could )?(?:disappear|wasn" + _AP + r"t here|was dead|were dead)\b"
            r"|\boverdos(?:e|ed|ing)\b"
            r"|\b(?:took|taken|swallowed|downed) (?:too many|too much|a bunch of|a handful of|a whole bottle of|the whole bottle of|a lot of) (?:my |the )?(?:pills?|tablets?|meds|medications?|medicine)\b"
            r"|\b(?:took|swallowed|downed) (?:all|every one) (?:of )?(?:my|the) (?:pills?|tablets?|meds|medication)(?: at once| all at once| on purpose| tonight| just now| on purpose)\b"
        ),
        "es": (
            r"\bme estoy muriendo\b|\bme voy a morir\b|\bquiero morir(?:me)?\b"
            r"|\b(?:acabar|terminar) con (?:mi vida|todo)\b"
            r"|\bestar(?:ía|ia|ían|ian) mejor sin m[ií]\b"
            r"|\bquiero (?:desaparecer|no estar aqu[ií])\b"
            r"|\bsobredosis\b|\bme sobredos(?:i|í)\b"
            r"|\b(?:tom[eé]|me tom[eé]|trague|me tragu[eé]) (?:demasiadas|muchas|un mont[oó]n de|un puñado de|toda la caja de|el frasco entero de) pastillas\b"
            r"|\b(?:tom[eé]|me tom[eé]|me tragu[eé]) (?:todas|todas mis|todas las) pastillas (?:de una vez|de golpe|a prop[oó]sito|esta noche|ahora mismo)\b"
        ),
    },
    "F-SYMPTOM": {
        "en": (
            r"\b(?:leg|legs|ankles?|feet|foot|knee|arm|hand)\b(?:(?!\b(?:not|no|never|without|isn't|aren't|wasn't|weren't)\b)[^.!?;]){0,25}\b(?:swollen|swelling)\b|\b(?:swollen|swelling) (?:in )?(?:my )?(?:leg|legs|ankles?|feet|foot|knee|arm)\b"
            r"|\b(?:a lot of|so much|lots of|terrible|horrible|awful|unbearable|really bad) pain\b|\bin (?:a lot of|so much|terrible|severe|unbearable) pain\b"
        ),
        "es": (
            r"\b(?:pierna|piernas|tobillos?|pies|pie|rodilla|brazo)\b(?:(?!\b(?:no|nunca|sin|ni|tampoco)\b)[^.!?;]){0,25}\b(?:hinchad[oa]s?|inflamad[oa]s?)\b|\b(?:mucho|demasiado|terrible|insoportable) dolor\b"
        ),
    },
    "F-DISTRESS": {
        "en": r"\b(?:i )?(?:feel|am|i'm|im) (?:very|so|really|extremely) (?:sad|down|depressed|low)\b|\bfeeling (?:very|so|really) (?:sad|depressed)\b",
        "es": r"\bno puedo dormir y me siento (?:muy |tan |bien )?(?:triste|deprimid[oa]|mal)\b|\bme siento (?:muy|tan|bien|demasiado) (?:triste|deprimid[oa]|mal)\b|\bestoy (?:muy|tan) (?:triste|deprimid[oa])\b",
    },
    "F-CHEST": {
        "en": (
            r"\b(?:tightness|pressure|heaviness) in (?:my |the )?chest\b|\bchest pains?\b|\bpains (?:in|on) (?:my |the )?chest\b|\btight chest\b|\b(?:my )?chest (?:is |feels |has been )?(?:so |really |very )?(?:tight|heavy|squeezed)\b"
            r"|\bheart (?:is |was )?(?:racing|pounding)\b[^.!?;]{0,30}\b(?:hurts?|aches?|pain|tight)\b|\bmy heart (?:hurts|aches)\b"
            r"|\b(?:hard|tough|difficult) (?:time )?(?:to )?(?:catch(?:ing)? my breath|breath(?:e|ing))\b"
            r"|\bbreathing (?:is|has been|feels) (?:really |very |so )?(?:hard|difficult|tough|labou?red)\b"
            r"|\bhard to take a breath\b"
        ),
        "es": (
            r"\bdolores (?:de|en el|en mi) pecho\b|\bpresi[oó]n (?:en|sobre) (?:el |mi )?pecho\b"
            r"|\bme duele(?:n)? el pecho\b|\bpecho me duele\b|\bme falta el aire\b|\brespiro con dificultad\b|\brespirar (?:es|está) (?:muy )?(?:difícil|duro)\b"
        ),
    },
}
FLAG_RULES = [
    (rid, tier, {l: (p if rid not in _EXTRA_FLAG_PATTERNS else "(?:%s)|(?:%s)" % (p, _EXTRA_FLAG_PATTERNS[rid][l])) for l, p in pats.items()})
    for rid, tier, pats in FLAG_RULES
]


# A match is NOT about the participant right now when its sentence is about another person or about long ago.
OTHER_PERSON = {
    "en": r"\b(my (dad|father|mom|mother|sister|brother|friend|wife|husband|son|daughter|neighbou?r|grand(ma|mother|pa|father)|aunt|uncle|cousin|coworker|boss)|he|she|they|someone|somebody)\b",
    "es": r"\b(mi (mam[aá]|pap[aá]|madre|padre|hermano|hermana|amig[oa]|espos[oa]|marido|mujer|hij[oa]|vecin[oa]|abuel[oa]|t[ií][oa]|prim[oa]|jefe)|él|ella|ellos|ellas|alguien)\b",
}
LONG_AGO = {
    "en": r"\b(last year|years? ago|months? ago|when I was (a kid|little|young|younger)|as a (kid|child)|a long time ago|back in (college|school|high school|the day)|in (college|high school))\b",
    "es": r"\b(el a[ñn]o pasado|hace (\w+ )?(a[ñn]os|meses)|cuando era (ni[ñn][oa]|chic[oa]|joven|peque[ñn][oa])|a[ñn]os atr[aá]s|en la universidad|en la secundaria|en la preparatoria)\b",
}

# Negation cues that, within NEGATION_WINDOW tokens before a match, cancel it.
NEGATIONS = {
    "en": r"\b(no|not|never|without|don't|doesn't|didn't|haven't|hasn't|isn't|aren't|wasn't|weren't|hadn't|denies|denied)\b",
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
