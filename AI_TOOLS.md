- Claude Code (Anthropic, desktop session, Sonnet 5.5 per commit trailers, other Claude models possible): wrote code and tests in src/ and tests/ (row 1 onward).
- Devin (Cognition): wrote eval/ (offline eval harness, row 8, PR #1; synthetic data only).
- Archie (Archie Labs): generated the React/Vite UI in ui/ (row 7); model not shown in the tool.
- OpenAI Codex (model not recorded): created src/i18n/labels.py (~10:06 AM Sat Oct 17, on the owner's request) and wrote the read-only code reviews in reviews/.
- Claude (Anthropic), Claude desktop app "Hackathon event notes" session (model not recorded): wrote the starter README.md, .gitignore, src/load_data.py stub, and the starter SPEC.md and TASKS.md.
- Claude Code (Anthropic, Sonnet 5.5) also wrote src/ (schema, loader, tagger, flagger, score card, API, AnnoMI eval adapter), tests/, the UI demo mode and Live analyzer in ui/, and WALKTHROUGH.md.
- A model API is NOT called by the app: /api/explain returns 409 unless LLM_APPROVED=1, and it is off. Add a line here only if it is ever enabled.

## Data note

Data note: No challenge rows or file contents were put into any AI tool's prompt, as far as I have checked. Summary figures computed from the challenge data were: in my own Claude Code sessions, and one accuracy figure in a Codex code-review prompt (Codex ran read-only on this repository). I have not audited Codex's, Devin's or Archie's own logs. No challenge rows, file contents or accuracy figures are in this repository; a count of held-out sessions appeared in an earlier test file's history.
