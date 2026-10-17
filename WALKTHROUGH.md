# WALKTHROUGH: what was built, why, and how to defend it

Written Sat Oct 17, 2026 for the human owner. No data, no code, plain prose. Everything below was built and tested only on invented, fictional lines. Nothing here has been measured against the organizers' real data, so never quote an accuracy number you have not run yourself.

The one-line pitch: Hear Me Out reads a health-coaching conversation in English or Spanish, tags what the coach is doing, scores the call against motivational-interviewing practice, and flags any sentence a person should see today by quoting it. It does not diagnose and gives no medical advice.

## 1. Loader and schema check

- **What it does:** It reads a conversation file and refuses anything that does not match the shapes in CONTRACT.md (conversation, line, tag, flag), with a clear error naming what is wrong.
- **Why it is built that way:** Every other part trusts these shapes, so a bad record must fail loudly at the door and not as a strange score later. Unknown fields, gaps in line numbers, and tags that claim a rule but name none are all rejected.
- **If a judge challenges it:** "A tagger is only as trustworthy as its input, so the boundary is strict and tested, and a malformed call can never silently produce a score."
- **Honest limit:** It validates shape, not truth. It cannot tell a real transcript from a made-up one, and it only reads our own JSON format; the organizers' CSV files need a converter that is not written yet.

## 2. Tagger (coach moves and participant talk)

- **What it does:** For each coach line it picks one move from the organizers' 12 (open question, reflection, affirm, ask permission, persuade, and so on). For each participant line it picks change talk, sustain talk or neutral. Text-message lines also get an intent such as thanks or reminder.
- **Why it is built that way:** Phrase rules in both languages, checked in a fixed priority order, so the same line always gets the same label and a reviewer can see which rule fired. A feeling question like "¿Cómo te sientes?" counts as a question, not a reflection.
- **If a judge challenges it:** "Rules are transparent and auditable, which matters when a manager asks why a coach was scored a certain way; a classifier can be added behind the same shape later."
- **Honest limit:** These are our own heuristics. They were written from the label names, not from the organizers' definitions or data, so accuracy on real calls is unknown and probably modest. They miss paraphrase, sarcasm, and mixed-language lines.

## 3. Needs-a-human flagger and negation guard

- **What it does:** It looks only at participant lines for crisis, chest or breathing trouble, symptoms and distress, in three tiers. It quotes the sentence, ignores denials such as "no tengo dolor de pecho" or "no fever, vomiting or bleeding", and says whether the coach responded.
- **Why it is built that way:** A false alarm wastes a coach's time but a missed symptom is worse, so it errs toward flagging. Denial cancels a match only inside the same clause, a phrase like "no puedo respirar" is never cancelled by its own "no", and a coach reply counts as handling the flag only if it acknowledges or acts (for example "llamo a la enfermera"), not for an unrelated next line.
- **If a judge challenges it:** "It never decides what is wrong with anyone; it points a person to the exact sentence and shows why, and the unhandled ones sort first."
- **Honest limit:** The three tiers (S1 to S3) are our own design, not the organizers'. Negation is a word-window heuristic, so tricky phrasing will slip through either way. The response check looks only at the next three coach lines and matches keywords, so it can be fooled. It is a triage aid, not a safety system.

## 4. Score card

- **What it does:** For one call it shows plain counts (for example open questions out of all questions, reflections per question) and a yes/no checklist of the organizers' items (set agenda, checked feelings, set next contact, and so on), each with the lines that justify it, plus whether any safety issue was handled.
- **Why it is built that way:** Counts with their evidence lines can be checked by a supervisor line by line. There is deliberately no single secret number, so no one can say the score is a black box.
- **If a judge challenges it:** "A coach can challenge any item by clicking the evidence line, which is how supervisors actually review calls."
- **Honest limit:** Checklist cues are keyword guesses, so "no" often means "we did not find the wording", not "the coach did not do it". It does not produce the organizers' supervisor ratings (empathy, partnership, overall).

## 5. JSON API

- **What it does:** A small local web service with the routes in CONTRACT.md: analyze a conversation, list the flagged queue (highest tier and unhandled first), fetch one call, explain why a line was flagged. The explain route that would call a language model answers "off" unless explicitly enabled.
- **Why it is built that way:** Plain Python with no outside packages, running only on this machine, so there is nothing to leak and nothing to install. The model-calling route is deliberately off because the Participant Agreement bars sending challenge data to third-party AI.
- **If a judge challenges it:** "The model is optional and isolated, so the product still works if data rules forbid sending anything out."
- **Honest limit:** It serves our fictional fixtures only. It has no login, no database and no saved reviewer decisions, and it is not deployed anywhere public.

## 6. UI

- **What it does:** A React app generated by Archie: a call queue, a call review screen with flagged lines and a "why this line needs a human" panel, and scorecards. Demo mode runs without any account. We added a Live analyzer page where you pick a fictional call or type a line in English or Spanish and see our real tags, flags, counts and checklist.
- **Why it is built that way:** Archie gave a complete, polished interface quickly (it also competes for the Archie prize). The Live analyzer is the honest bridge: it shows our actual engine working in front of a judge, with a typed Spanish sentence.
- **If a judge challenges it:** "The queue-to-flag-to-why path is real and clickable, and the live page proves the engine, not a mockup, is behind it."
- **Honest limit:** The queue, review and scorecard screens still show Archie's invented sample data, not our engine's output; only the Live analyzer uses our engine. Archie's own backend is off in demo mode and ends tonight. It is not deployed yet and has not been tested on a phone.

## 7. Eval harness

- **What it does:** A script you run yourself, offline, on your own machine. Given a file of our predictions and a file of the organizers' labels, it prints precision, recall and F1 for each label, an overall macro score, an agreement score (kappa), a confusion table, and the same by language, plus precision and recall for needs-a-human. It also has an error measure for the 1-to-5 supervisor ratings.
- **Why it is built that way:** It lets the human measure the tool without any real label ever going into an AI chat, which the agreement requires. It was built by Devin on invented data only.
- **If a judge challenges it:** "We report per-label and per-language results, not one flattering average, and we show the hard cases in the confusion table."
- **Honest limit:** It has been run only on made-up data, so it proves the script works, not that the tagger is good. We have no real accuracy number yet.

## Five improvements, ranked by rubric points gained per effort

Rubric: Innovation 25, Technical Execution 25, Impact and Viability 20, Design and UX 15, Pitch 15.

1. **Run the eval on the real data yourself, and put the honest number on a slide (about 20 minutes; Technical Execution, Impact).** It turns "we built a tagger" into "here is how well it works and where it fails", and honest results beat a bigger claim you cannot back. Read the numbers yourself and do not paste them into an AI chat.
2. **Rehearse a three-minute demo around the live Spanish line (about 20 minutes; Pitch, Innovation).** Type "no puedo respirar" and watch the flag, then type "no tengo dolor de pecho" and watch it stay quiet. Judges remember the negation moment; it is the one thing that visibly separates this from a keyword search.
3. **Point the queue and review screens at our engine (about 45 minutes; Technical Execution, Design).** Right now the main screens show Archie's sample data. Making them show our flags removes the one gap a sharp judge could find.
4. **Tune the rules against the organizers' label definitions from the brief (about 30 minutes; Technical Execution).** You can read the definitions; we wrote the patterns without them. Fixing the most common mislabels will move the number in item 1 more than any new feature.
5. **Add a limits and safety slide (about 10 minutes; Impact and Viability).** State what it does not do (no diagnosis, human decides, triage aid), who reviews, and that no data left the machine. Judges reward knowing the limits, and this is the cheapest points on the board.

A sixth idea, if the organizers approve in writing: add a language-model classifier next to the rules and compare both in the eval. It is the strongest Innovation story but it needs approval and about 45 minutes, so only start it if items 1 to 5 are done.
