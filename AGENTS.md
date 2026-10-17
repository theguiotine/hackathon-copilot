# AGENTS.md: rules for every AI tool in this repo (Claude Code, Codex, Devin, Archie)

Project: Coach's Copilot, eMerge AI Hackathon 2026, Healthcare track, Challenge 5. One human owner (Esteban). Read SPEC.md, CONTRACT.md and TASKS.md first.

## Hard rules (the Participant Agreement binds the human; do not make him breach it)
1. **Never read, open, print, summarize or upload anything in the local data folder or any file named in `COACH_DATA_DIR`.** That folder is challenge Data. Third-party AI tools may not receive Data or Derived Data (Agreement 2.3) unless the organizers approved the tool in writing. Until `APPROVED.md` exists in this repo root, work only from the schemas in CONTRACT.md and from fictional lines in `tests/fixtures/` that a human typed.
1b. **Ruling by the human, Sat Oct 17 ~10:30 (his words: "i dont care ... practically i need to read understand it"):** the dataset's README and other documentation files MAY be read to understand the schema. Data files (CSV, JSON, transcripts, labels, rows) still may NOT be read, printed or uploaded until the organizers approve tools in writing. He accepts the documentation-as-Data legal risk himself; do not widen this to rows.
1c. **Ruling by the human, Sat Oct 17 ~10:55 (his words: "presume organizers give permission and we build form there if not we can later backtrack or regroup ... Just build the opportunity"):** proceed on presumed approval; do not wait for the organizers. Staging that keeps the one irreversible step last: (a) build everything on fictional fixtures first; (b) only Claude Code and Claude API calls run on real Data rows, and only after you tell the human in HANDOFF.md which rows or files you are about to use; (c) Codex reads real rows only after the human confirms its "Improve the model for everyone" toggle is off; (d) Archie and Devin stay on mock data and code, because their default terms may train on inputs and anything sent cannot be taken back. If the organizers answer no, stop using rows at once and delete Derived Data.
2. **Derived Data counts too:** model weights, features, embeddings, labels, and accuracy tables computed from the Data. Do not paste them into any AI chat. The human runs the eval locally and reads the result.
3. **Public repo = code only.** No data, no labels, no weights, no keys, no `.env`. Never commit anything under `data/`.
4. No network calls from the app at run time on Data. The LLM explanation module is off (`LLM_APPROVED` unset) and returns 409.
5. No medical advice, no diagnosis. The tool flags a human and quotes the sentence.
6. Every AI tool that wrote code must be listed in `AI_TOOLS.md` (Agreement 4.9: disclosure to the organizers). Append a line when you contribute.

## The baton (strict sequence; one active tool at a time on `main`)
1. **Claude Code** (owner of `main`, the deploy and the final say) takes the next row in TASKS.md, writes code plus tests on branch `claude`, marks the row `review`.
2. **Codex** reviews that diff only, read-only: it writes findings to `reviews/<row>.md` (real bugs, edge cases, test gaps, rule violations of this file). It does not edit code on `claude`.
3. **Claude Code** fixes the findings, runs the tests, and merges to `main` with a pathspec commit. Marks the row `done` and writes one line to HANDOFF.md.
4. **Archie** builds UI shells from CONTRACT.md in its own export folder (`ui/`), never touching `src/`. Claude Code wires `ui/` to `src/`.
5. **Devin** gets one isolated chunk at a time on branch `devin`, in one folder, from a mock-data spec. Claude Code merges or rejects.
Handoff means: update your row's Status and Evidence in TASKS.md, append one dated line to HANDOFF.md saying what the next tool needs, then stop.

## Checkpoints (Sat Oct 17, Eastern)
12:20 Gate: tagger runs on fixtures · 3:00 PM feature freeze · 4:40 PM submit target (OFFICIAL close 6:00 PM).

## Style
Small commits, tests with every module, no dependencies you cannot explain. Say "not run" when you did not run something.
- ui/AGENTS.md is Archie's; root rules win; never put keys in ui/ (env var names only).
