# TASKS (baton order, see AGENTS.md; each tool edits only its own rows; Status: todo / doing / review / done)

| # | Task | Owner | Branch | Files | Status | Done when (evidence) |
|---|---|---|---|---|---|---|
| 0 | Ask organizers which AI tools are approved on the Data (Wall post) | Esteban | n/a | n/a | todo | written answer saved; if yes create APPROVED.md |
| 1 | Loader + schema check against CONTRACT.md, 6 typed fictional lines per language | Claude Code | claude | src/, tests/fixtures/ | done | 23+ loader/schema tests OK; reviews/1.md: no findings |
| 2 | Review of row 1 | Codex | codex | reviews/ | done | reviews/1.md: no findings |
| 3 | Rule tagger EN+ES (coach moves, participant talk) | Claude Code | claude | src/tagger/ | done | Codex rounds 1-2 and final (reviews/) fixed; 91 tests OK |
| 4 | Needs-human flagger with negation guard, tiers S1-S3, "unhandled" rule | Claude Code | claude | src/flagger/ | done | Codex rounds 1-2 and final (reviews/) fixed; 91 tests OK |
| 5 | Review of rows 3-4 | Codex | codex | reviews/ | done | reviews/3-4.md, reviews/6.md, reviews/3-4-6-round2.md, reviews/final.md; all High/Medium fixed |
| 6 | Score card: counts, checklist, transparent formula | Claude Code | claude | src/score/ | done | Codex rounds 1-2 fixed; 91 tests OK |
| 7 | UI shell: coach view, manager view, eval tab, from CONTRACT.md | Archie | n/a (ui/ export) | ui/ | done | ui/ committed; demo mode + Live analyzer + Evaluation screen; tsc clean; click path queue-call-flag-why verified in browser |
| 8 | Eval harness script the human runs locally | Devin | devin | eval/ | done | PR #1 merged to main (28fcee6); 18 eval tests OK offline; only eval/ touched, no data, no network |
| 9 | Wire ui/ to src/, deploy, insurance video | Claude Code | main | all | doing | demo screens driven by our engine (scripts/gen_ui_fixtures.py); /api/eval; API hardened (CORS, symlinks); NOT deployed (demo runs locally); insurance video not made |
| 10 | README, limits slide, credits, AI_TOOLS.md, deck | Claude Code | main | README.md, AI_TOOLS.md | doing | README.md written (what/run/data policy/limits/credits/AI tools); limits slide, deck, public-repo check still open |

Checkpoints: 12:20 gate (rows 1-4 green on fixtures) · 3:00 PM feature freeze · 4:40 PM submit target.
