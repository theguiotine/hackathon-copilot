# Codex final review (non-interactive, read-only): main...claude

1. **[High] `src/api.py:28–31` — `/api/eval` can read outside `COACH_CLASSIFIER_DIR`.** `is_file()` and `read_text()` follow symlinks. An `eval_summary.json` symlink to an external JSON file causes that file’s contents to be returned. Resolve and validate containment before reading.

2. **[High] `src/train_annomi.py:60`, `src/classifier.py:116–117`, `src/eval_annomi.py:139–151` — Output-file symlinks bypass the repo guard.** `_safe_out()` validates only the directory. An existing `classifier_coach.json` symlink inside an allowed output directory can point into the repo; training then writes real weights there. Prediction and label writers have the same issue. Validate each destination and refuse symlinks before writing.

3. **[High] `src/api.py:86` — Wildcard CORS exposes local data to other origins.** Every response includes `Access-Control-Allow-Origin: *`, allowing another origin that can reach the API to read `/api/eval` aggregates and any loaded conversations without authentication. Restrict access to the intended UI origin.
