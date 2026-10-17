"""Load the organizers' coaching files from an external folder (never from inside the repo)."""
import os
from pathlib import Path

DEFAULT = Path.home() / "hackathon-data" / "challenge5" / "Challenge5_Coaches_Copilot"


def data_dir() -> Path:
    path = Path(os.environ.get("COACH_DATA_DIR", str(DEFAULT))).expanduser()
    if not path.is_dir():
        raise FileNotFoundError(f"Set COACH_DATA_DIR to the data folder; not found: {path}")
    return path


def csv_path(name: str) -> Path:
    path = data_dir() / name
    if not path.is_file():
        raise FileNotFoundError(path)
    return path
