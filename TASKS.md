# TASKS (baton order, see AGENTS.md; each tool edits only its own rows; Status: todo / doing / review / done)

| # | Task | Owner | Branch | Files | Status | Done when (evidence) |
|---|---|---|---|---|---|---|
| 0 | Ask organizers which AI tools are approved on the Data (Wall post) | Esteban | n/a | n/a | todo | written answer saved; if yes create APPROVED.md |
| 1 | Loader + schema check against CONTRACT.md, 6 typed fictional lines per language | Claude Code | claude | src/, tests/fixtures/ | review | `python3 -m unittest discover -s tests -t .` : Ran 23 tests, OK (fixtures: 1 EN + 1 ES conversation, 6 invented lines each; pytest not installed) |
| 2 | Review of row 1 | Codex | codex | reviews/ | todo | reviews/1.md lists real bugs or says none |
| 3 | Rule tagger EN+ES (coach moves, participant talk) | Claude Code | claude | src/tagger/ | review | 34 tests OK (`python3 -m unittest discover -s tests -t .`); labels are PLACEHOLDERS in src/config.py |
| 4 | Needs-human flagger with negation guard, tiers S1-S3, "unhandled" rule | Claude Code | claude | src/flagger/ | review | same 34 tests OK incl. Spanish negated `no tengo dolor de pecho` and English negated `no fever and no chest pain` not flagged; tiers/rule names are PLACEHOLDERS in src/config.py |
| 5 | Review of rows 3-4 | Codex | codex | reviews/ | todo | reviews/3-4.md |
| 6 | Score card: counts, checklist, transparent formula | Claude Code | claude | src/score/ | todo | tests pass |
| 7 | UI shell: coach view, manager view, eval tab, from CONTRACT.md | Archie | n/a (ui/ export) | ui/ | todo | click path queue to call to flag to why works on mock data |
| 8 | Eval harness script the human runs locally | Devin | devin | eval/ | todo | script runs on a mock CSV with the schema |
| 9 | Wire ui/ to src/, deploy, insurance video | Claude Code | main | all | todo | demo works on phone |
| 10 | README, limits slide, credits, AI_TOOLS.md, deck | Claude Code | main | README.md, AI_TOOLS.md | todo | repo opens logged out, no data inside |

Checkpoints: 12:20 gate (rows 1-4 green on fixtures) · 3:00 PM feature freeze · 4:40 PM submit target.
