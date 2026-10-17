# TASKS (baton order, see AGENTS.md; each tool edits only its own rows; Status: todo / doing / review / done)

| # | Task | Owner | Branch | Files | Status | Done when (evidence) |
|---|---|---|---|---|---|---|
| 0 | Ask organizers which AI tools are approved on the Data (Wall post) | Esteban | n/a | n/a | todo | written answer saved; if yes create APPROVED.md |
| 1 | Loader + schema check against CONTRACT.md, 6 typed fictional lines per language | Claude Code | claude | src/, tests/fixtures/ | review | `python3 -m unittest discover -s tests -t .` : Ran 23 tests, OK (fixtures: 1 EN + 1 ES conversation, 6 invented lines each; pytest not installed) |
| 2 | Review of row 1 | Codex | codex | reviews/ | done | reviews/1.md: no findings |
| 3 | Rule tagger EN+ES (coach moves, participant talk) | Claude Code | claude | src/tagger/ | review-fixed-2 | 34 tests OK (`python3 -m unittest discover -s tests -t .`); 12 coach moves, 3 participant talk, 13 text intents (names from the brief, patterns are our heuristics) ; Codex High+Medium findings in reviews/3-4.md fixed, 48 tests OK ; Codex round 2 (reviews/3-4-6-round2.md) High+Medium fixed, 57 tests OK |
| 4 | Needs-human flagger with negation guard, tiers S1-S3, "unhandled" rule | Claude Code | claude | src/flagger/ | review-fixed-2 | same 34 tests OK incl. Spanish negated `no tengo dolor de pecho` and English negated `no fever and no chest pain` not flagged; S1-S3 are our own design (CONTRACT.md) ; Codex High+Medium findings in reviews/3-4.md fixed, 48 tests OK ; Codex round 2 (reviews/3-4-6-round2.md) High+Medium fixed, 57 tests OK |
| 5 | Review of rows 3-4 | Codex | codex | reviews/ | todo | reviews/3-4.md |
| 6 | Score card: counts, checklist, transparent formula | Claude Code | claude | src/score/ | review-fixed-2 | same suite OK (counts {num,den,lines}, 7 checklist items + safety_issue_handled) ; Codex High+Medium findings in reviews/6.md fixed, 48 tests OK ; Codex round 2 (reviews/3-4-6-round2.md) High+Medium fixed, 57 tests OK |
| 7 | UI shell: coach view, manager view, eval tab, from CONTRACT.md | Archie | n/a (ui/ export) | ui/ | review | ui/ committed (Archie export, React+Vite, no key values; env var names only); click path not yet verified |
| 8 | Eval harness script the human runs locally | Devin | devin | eval/ | done | PR #1 merged to main (28fcee6); 18 eval tests OK offline; only eval/ touched, no data, no network |
| 9 | Wire ui/ to src/, deploy, insurance video | Claude Code | main | all | doing | demo mode works: `cd ui && VITE_DEMO_MEMORY=1 npx vite --port 3000` loads call queue + scorecards on Archie's fictional fixtures, no sign-in; local API src/api.py ready; NOT yet reading src/ engine; deploy not done |
| 10 | README, limits slide, credits, AI_TOOLS.md, deck | Claude Code | main | README.md, AI_TOOLS.md | todo | repo opens logged out, no data inside |

Checkpoints: 12:20 gate (rows 1-4 green on fixtures) · 3:00 PM feature freeze · 4:40 PM submit target.
