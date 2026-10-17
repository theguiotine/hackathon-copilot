# CONTRACT.md: shapes every tool builds against (no challenge data in this file)

## Records
```
Conversation { id, channel: "call"|"text", language: "en"|"es", lines: Line[] }
Line         { idx, speaker: "coach"|"participant", text }
Tag          { conv_id, line_idx, kind, label, method: "rule"|"classifier", rule_id? }
Flag         { conv_id, line_idx, tier: "S1"|"S2"|"S3", rule_id, quote, negation_checked, coach_responded }
CallScore    { conv_id, counts: {metric: {num, den, lines[]}}, checklist: {item: {value, evidence_lines[]}} }
EvalReport   { by_label: {p, r, f1, n}, by_language: {...} }   // computed locally by the human, never pasted into an AI chat
```
Tag labels, checklist items and tiers follow the organizers' brief; take the exact names from the brief in the human's hands, not from this file.

## Routes (all local)
- `POST /api/analyze` body: Conversation; returns tags, flags, score
- `GET /api/queue` today's flagged conversations, sorted by tier then unhandled
- `GET /api/call/:id`, `GET /api/why/:id`, `GET /api/eval`
- `POST /api/explain` returns 409 unless `LLM_APPROVED=1` (the isolated LLM module)

## File ownership
`src/` Claude Code · `reviews/` Codex · `ui/` Archie export · `branches/devin` one folder at a time · `tests/fixtures/` typed fictional lines only (a human types them).
