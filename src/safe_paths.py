"""Output-path guards shared by every script that writes derived files (predictions, labels, weights).

A destination is refused if it is a symlink or if it resolves inside the repo, so real-data outputs can never be
written into a tracked folder, even through a symlink planted inside an otherwise allowed output folder.
"""
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


class AdapterError(Exception):
    """A problem described without echoing any cell content."""


def _inside_repo(p: Path) -> bool:
    return p == REPO or REPO in p.parents


def safe_dir(out_dir) -> Path:
    out = Path(out_dir).expanduser()
    if out.is_symlink():
        raise AdapterError("refusing a symlinked output folder")
    out = out.resolve()
    if _inside_repo(out):
        raise AdapterError("refusing to write predictions inside the repo; set COACH_OUT_DIR outside it")
    out.mkdir(parents=True, exist_ok=True)
    return out


def safe_dest(path) -> Path:
    """Validate one destination file before writing: no symlink, not inside the repo."""
    path = Path(path).expanduser()
    if path.is_symlink():
        raise AdapterError("refusing to write through a symlink")
    if _inside_repo(path.parent.resolve() / path.name):
        raise AdapterError("refusing to write inside the repo")
    return path
