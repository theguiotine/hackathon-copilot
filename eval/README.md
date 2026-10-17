# eval/: offline evaluation harness (row 8)
Run locally: `python3 eval/run_eval.py predictions.csv labels.csv` (no network, plain Python).
CSV columns: call_id, line_number, language (en/es), label, optional needs_human (yes/no).
Prints per-label precision/recall/F1/support, macro-F1, kappa, confusion matrix, per-language tables.
`metrics.py` also has MAE and within-one agreement for 1-5 ratings. Tests: `python3 -m unittest discover -s eval`.
Tests use synthetic data from `mock_data.py` only; keep real labels and results out of git and AI chats.
