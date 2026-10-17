# Coach's Copilot (eMerge AI Hackathon 2026, Healthcare, Challenge 5)

Bilingual (English/Spanish) tool that follows a health-coaching conversation, tags what the coach is doing,
scores the coach against motivational-interviewing practice, and flags anything a person must see today.

## Status
Skeleton only. No data, no keys, and no model calls are in this repo.

## Data (kept OUT of this repo, by the hackathon terms)
Set `COACH_DATA_DIR` to the folder that holds the organizers' files (default `~/hackathon-data/challenge5/Challenge5_Coaches_Copilot`).
Never commit data files. `.gitignore` excludes `*.csv`, `data/`, `.env` and keys.

## Sources to credit (the dataset README asks for this)
- AnnoMI: Wu Z, et al. Future Internet, 2023 (public domain, per the organizers' README).
- UIC coaching texts: Gupta I, et al. SIGDIAL 2020 (https://github.com/uic-nlp-lab/virtualcoachdata).
- Synthetic coaching program: Crane Lab, Sylvester Comprehensive Cancer Center.

## Layout
- `src/load_data.py` loads files from `COACH_DATA_DIR` (nothing runs on import).
- `SPEC.md`, `TASKS.md` coordinate the build lanes.
