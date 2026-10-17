# Codex round 2 (non-interactive, read-only), rows 3, 4, 6 fixes

1. **High — unrelated replies still mark safety issues handled.** [src/config.py:87](../src/config.py:87): after “I have chest pain,” “I will send your walking plan tomorrow” produces `coach_responded=True` and `safety_issue_handled=yes`. Generic cues such as `I will` do not establish a response to the flag. The prior High finding remains; existing tests miss this case.

2. **Medium — Spanish response stems cannot match complete words.** [src/config.py:88](../src/config.py:88): enclosing `llam`, `enfermer`, and `médic` in word boundaries prevents matching `llama`, `enfermera`, and `médico`. “No puedo respirar” followed by “Llama al médico” incorrectly remains unhandled. No regression test covers this.

3. **Medium — response detection stops at the first coach line.** [src/flagger/rules.py:36](../src/flagger/rules.py:36): “How long has this been happening?” followed by “I will call the nurse now” leaves the preceding chest-pain flag unhandled and omits the actual response from score evidence. No test covers a follow-up spanning multiple coach lines.

4. **Medium — commas break negation in symptom lists.** [src/config.py:83](../src/config.py:83): “No tengo fiebre, vómitos ni sangrado” incorrectly emits `F-SYMPTOM` for `vómitos`. The comma ends negation scope despite the coordinated denial. Existing negation tests omit comma-separated lists.

