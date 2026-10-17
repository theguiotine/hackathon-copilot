"""Load the organizers' coaching files from an external folder (never from inside the repo)."""
import os
from pathlib import Path


def data_dir() -> Path:
    value = os.environ.get("COACH_DATA_DIR")
    if not value:
        raise FileNotFoundError("Set COACH_DATA_DIR to the local data folder")
    path = Path(value).expanduser()
    if not path.is_dir():
        raise FileNotFoundError(f"COACH_DATA_DIR is not a folder: {path}")
    return path


def csv_path(name: str) -> Path:
    path = data_dir() / name
    if not path.is_file():
        raise FileNotFoundError(path)
    return path
