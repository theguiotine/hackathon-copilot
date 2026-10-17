"""Seeded GENERATOR of invented health-coaching conversations with ground truth by construction.

Code only. No real, challenge or patient data is read; nothing here opens ~/hackathon-data.
Every sentence is invented from the templates below. Ground truth is attached to each template:
  - participant lines: truth flag category (CRISIS, CHEST, SYMPTOM, DISTRESS) or a decoy kind
    (NEG negated, OTHER about another person, PAST long ago, BENIGN, NEUTRAL) that must NOT flag;
  - coach lines: the coach move present.
Phrasings may be easier or harder than real speech; this is not clinical validation.

generate(n, seed) returns (conversations_as_dicts, truth) where truth[conv_id][line_idx] =
{"kind": "flag"|"decoy"|"neutral"|"coach", "cat": ..., "tid": template id, "variant": ...}
"""
import random
import unicodedata

# (template id, text, variant)   variant: base | plural | order | selfneg
FLAG_T = {
    "en": {
        "CRISIS": [
            ("CRISIS-01", "Sometimes I think about ending my life", "base"),
            ("CRISIS-02", "I keep thinking about hurting myself", "base"),
            ("CRISIS-03", "I want to die", "base"),
            ("CRISIS-04", "I don't want to live anymore", "selfneg"),
            ("CRISIS-05", "everyone would be better off without me", "order"),
        ],
        "CHEST": [
            ("CHEST-01", "I get chest pain when I walk up the stairs", "base"),
            ("CHEST-02", "these chest pains woke me up twice this week", "plural"),
            ("CHEST-03", "my chest hurts when I climb the stairs", "order"),
            ("CHEST-04", "there is a sharp pain in my chest", "order"),
            ("CHEST-05", "I feel pressure in my chest after dinner", "order"),
            ("CHEST-06", "I can't breathe when I lie down", "selfneg"),
            ("CHEST-07", "I got really short of breath on the stairs", "base"),
            ("CHEST-08", "my chest feels tight and my heart is racing", "order"),
            ("CHEST-09", "chest pains again this morning", "plural"),
        ],
        "SYMPTOM": [
            ("SYMPTOM-01", "I fainted yesterday at work", "base"),
            ("SYMPTOM-02", "I keep getting dizzy when I stand up", "base"),
            ("SYMPTOM-03", "I've had a fever for two days", "base"),
            ("SYMPTOM-04", "my legs are swollen at night", "order"),
            ("SYMPTOM-05", "I've been vomiting since this morning", "base"),
            ("SYMPTOM-06", "there is blood in my urine", "order"),
            ("SYMPTOM-07", "my vision went blurry this afternoon", "order"),
            ("SYMPTOM-08", "these dizzy spells keep coming back", "plural"),
        ],
        "DISTRESS": [
            ("DISTRESS-01", "I feel completely hopeless lately", "base"),
            ("DISTRESS-02", "I'm so overwhelmed I can't cope", "selfneg"),
            ("DISTRESS-03", "I've been crying every single day", "base"),
            ("DISTRESS-04", "I feel like I'm falling apart", "base"),
        ],
    },
    "es": {
        "CRISIS": [
            ("CRISIS-01", "A veces pienso en quitarme la vida", "base"),
            ("CRISIS-02", "sigo pensando en hacerme daño", "base"),
            ("CRISIS-03", "quiero morirme", "base"),
            ("CRISIS-04", "no quiero vivir más", "selfneg"),
            ("CRISIS-05", "todos estarían mejor sin mí", "order"),
        ],
        "CHEST": [
            ("CHEST-01", "tengo dolor en el pecho cuando subo las escaleras", "base"),
            ("CHEST-02", "estos dolores en el pecho me despertaron dos veces esta semana", "plural"),
            ("CHEST-03", "me duele el pecho cuando subo las escaleras", "order"),
            ("CHEST-04", "siento un dolor fuerte en el pecho", "order"),
            ("CHEST-05", "siento presión en el pecho después de cenar", "order"),
            ("CHEST-06", "no puedo respirar cuando me acuesto", "selfneg"),
            ("CHEST-07", "me faltó el aire en las escaleras", "base"),
            ("CHEST-08", "tengo el pecho apretado y el corazón acelerado", "order"),
            ("CHEST-09", "otra vez dolores de pecho esta mañana", "plural"),
        ],
        "SYMPTOM": [
            ("SYMPTOM-01", "me desmayé ayer en el trabajo", "base"),
            ("SYMPTOM-02", "me mareo cada vez que me levanto", "base"),
            ("SYMPTOM-03", "tengo fiebre desde hace dos días", "base"),
            ("SYMPTOM-04", "tengo las piernas hinchadas por la noche", "order"),
            ("SYMPTOM-05", "he estado vomitando desde esta mañana", "base"),
            ("SYMPTOM-06", "hay sangre en mi orina", "order"),
            ("SYMPTOM-07", "se me nubló la vista esta tarde", "order"),
            ("SYMPTOM-08", "estos mareos siguen volviendo", "plural"),
        ],
        "DISTRESS": [
            ("DISTRESS-01", "me siento completamente sin esperanza últimamente", "base"),
            ("DISTRESS-02", "estoy tan abrumada que no puedo más", "selfneg"),
            ("DISTRESS-03", "he estado llorando todos los días", "base"),
            ("DISTRESS-04", "siento que me estoy derrumbando", "base"),
        ],
    },
}

DECOY_T = {
    "en": [
        ("NEG-01", "NEG", "no chest pain this week, which is great"),
        ("NEG-02", "NEG", "I haven't had any dizziness since Monday"),
        ("NEG-03", "NEG", "no fever at all, I checked this morning"),
        ("NEG-04", "NEG", "I don't feel hopeless anymore"),
        ("NEG-05", "NEG", "never had chest pains, just a sore back"),
        ("NEG-06", "NEG", "I didn't faint, I just sat down fast"),
        ("OTHER-01", "OTHER", "my mother had chest pain last year, so I worry"),
        ("OTHER-02", "OTHER", "my husband gets dizzy when he skips lunch"),
        ("OTHER-03", "OTHER", "my neighbor was feeling hopeless after her surgery"),
        ("PAST-01", "PAST", "years ago I fainted once at a wedding"),
        ("PAST-02", "PAST", "I used to feel hopeless before I started the program"),
        ("PAST-03", "PAST", "back in college I had chest pains but it was just stress"),
        ("BENIGN-01", "BENIGN", "my back is a little stiff but I'm fine"),
        ("BENIGN-02", "BENIGN", "I'm a bit tired but I slept okay"),
        ("BENIGN-03", "BENIGN", "I walked past the chest freezer in the garage"),
    ],
    "es": [
        ("NEG-01", "NEG", "no tengo dolor en el pecho esta semana, qué bien"),
        ("NEG-02", "NEG", "no he tenido mareos desde el lunes"),
        ("NEG-03", "NEG", "sin fiebre, me tomé la temperatura esta mañana"),
        ("NEG-04", "NEG", "ya no me siento sin esperanza"),
        ("NEG-05", "NEG", "nunca he tenido dolores de pecho, solo me duele la espalda"),
        ("NEG-06", "NEG", "no me desmayé, solo me senté rápido"),
        ("OTHER-01", "OTHER", "mi mamá tuvo dolor de pecho el año pasado y me preocupo"),
        ("OTHER-02", "OTHER", "mi esposo se marea cuando no almuerza"),
        ("OTHER-03", "OTHER", "mi vecina se sentía sin esperanza después de su operación"),
        ("PAST-01", "PAST", "hace años me desmayé una vez en una boda"),
        ("PAST-02", "PAST", "antes me sentía sin esperanza, antes del programa"),
        ("PAST-03", "PAST", "en la universidad tuve dolores de pecho pero era estrés"),
        ("BENIGN-01", "BENIGN", "tengo la espalda un poco rígida pero estoy bien"),
        ("BENIGN-02", "BENIGN", "estoy un poco cansada pero dormí bien"),
        ("BENIGN-03", "BENIGN", "pasé junto al congelador grande del garaje"),
    ],
}

NEUTRAL_T = {
    "en": ["I walked three days this week", "dinner was mostly vegetables and rice", "work has been busy but fine",
           "I skipped the evening snack twice", "my sister is visiting next week", "I drank more water than usual",
           "the weather made it hard to go out", "I tried the new recipe you mentioned"],
    "es": ["caminé tres días esta semana", "la cena fue casi toda verduras y arroz", "el trabajo ha estado ocupado pero bien",
           "dejé la merienda de la noche dos veces", "mi hermana nos visita la próxima semana", "tomé más agua que de costumbre",
           "el clima hizo difícil salir", "probé la receta nueva que mencionó"],
}

COACH_T = {
    "en": {
        "open_question": ["What would you like to focus on this week?", "How did the week go for you?", "What got in the way of your plan?"],
        "closed_question": ["Did you walk yesterday?", "Did you take your medication this morning?", "Was that on a weekday?"],
        "simple_reflection": ["You walked three days this week.", "So the evenings are the hard part.", "You skipped the snack twice."],
        "complex_reflection": ["It sounds like evenings are tough and that is where the snacking creeps in.",
                               "You want to keep going, and part of you is worn out by the schedule."],
        "affirm": ["You did really well sticking with your plan.", "That took real effort, well done."],
        "give_information": ["Walking after dinner can help keep blood sugar steady.", "Most people notice sleep changes within two weeks."],
        "ask_permission": ["Would it be okay if I shared an idea?", "May I offer a suggestion?"],
        "seek_collaboration": ["Let's work out a plan together.", "How about we pick one small step together?"],
    },
    "es": {
        "open_question": ["¿En qué le gustaría enfocarse esta semana?", "¿Cómo le fue la semana?", "¿Qué se interpuso en su plan?"],
        "closed_question": ["¿Caminó ayer?", "¿Tomó su medicina esta mañana?", "¿Fue entre semana?"],
        "simple_reflection": ["Caminó tres días esta semana.", "Entonces las noches son lo difícil.", "Se saltó la merienda dos veces."],
        "complex_reflection": ["Parece que las noches son difíciles y ahí es donde se cuela el picoteo.",
                               "Quiere seguir adelante, y una parte de usted está cansada del horario."],
        "affirm": ["Lo hizo muy bien siguiendo su plan.", "Eso requirió esfuerzo de verdad, muy bien."],
        "give_information": ["Caminar después de cenar puede ayudar a mantener estable el azúcar.", "La mayoría nota cambios en el sueño en dos semanas."],
        "ask_permission": ["¿Le parece bien si comparto una idea?", "¿Puedo ofrecerle una sugerencia?"],
        "seek_collaboration": ["Armemos un plan juntos.", "¿Qué tal si elegimos un paso pequeño juntos?"],
    },
}

FILL_PRE = {"en": ["um,", "well,", "yeah so", "honestly", "okay so"], "es": ["pues,", "eh,", "bueno,", "la verdad", "mira,"]}
FILL_POST = {"en": ["you know", "lately", "I guess", "to be honest"], "es": ["la verdad", "últimamente", "no sé", "digo yo"]}


def _strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _noise(text, lang, rng):
    """Return (noisy_text, noisy_bool). Noise never removes the key words on purpose, only decorates."""
    noisy = False
    if rng.random() < 0.35:
        text = rng.choice(FILL_PRE[lang]) + " " + text
        noisy = True
    if rng.random() < 0.30:
        text = text + " " + rng.choice(FILL_POST[lang])
        noisy = True
    if rng.random() < 0.25:
        text = text.lower()
        noisy = True
    if lang == "es" and rng.random() < 0.30:
        text = _strip_accents(text)
        noisy = True
    if rng.random() < 0.20:
        text = text.rstrip(".")
    else:
        text = text + "."
    return text, noisy


def generate(n=300, seed=20261017):
    rng = random.Random(seed)
    convs, truth = [], {}
    cats = ("CRISIS", "CHEST", "SYMPTOM", "DISTRESS")
    for i in range(n):
        lang = "en" if i % 2 == 0 else "es"
        cid = "syn-%04d" % i
        n_pairs = rng.randint(4, 9)
        n_flags = rng.choice([0, 0, 1, 1, 2])
        n_decoys = rng.choice([0, 1, 1, 2, 3])
        slots = ["flag"] * n_flags + ["decoy"] * n_decoys
        slots += ["neutral"] * max(0, n_pairs - len(slots))
        slots = slots[:max(n_pairs, len(slots))]
        rng.shuffle(slots)
        lines, tr = [], {}
        for slot in slots:
            move = rng.choice(list(COACH_T[lang].keys()))
            ctext, _ = _noise(rng.choice(COACH_T[lang][move]), lang, rng)
            tr[len(lines)] = {"kind": "coach", "cat": move, "tid": "COACH-" + move, "variant": "base"}
            lines.append({"idx": len(lines), "speaker": "coach", "text": ctext})
            if slot == "flag":
                cat = rng.choice(cats)
                tid, text, var = rng.choice(FLAG_T[lang][cat])
                kind, key = "flag", cat
            elif slot == "decoy":
                tid, key, text = rng.choice(DECOY_T[lang])
                var, kind = "base", "decoy"
            else:
                text = rng.choice(NEUTRAL_T[lang]); tid, key, var, kind = "NEUTRAL", "NEUTRAL", "base", "neutral"
            ptext, noisy = _noise(text, lang, rng)
            tr[len(lines)] = {"kind": kind, "cat": key, "tid": tid, "variant": ("noisy" if noisy else var), "base_variant": var}
            lines.append({"idx": len(lines), "speaker": "participant", "text": ptext})
        convs.append({"id": cid, "channel": rng.choice(["call", "text"]), "language": lang, "lines": lines})
        truth[cid] = tr
    return convs, truth
