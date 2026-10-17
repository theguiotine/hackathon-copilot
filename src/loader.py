"""Load Conversation records from a JSON file (a list, or one object) and validate them.

Takes an explicit path; it does not locate or read the challenge data folder (see load_data.py).
"""
import json
from pathlib import Path

from .schema import Conversation, SchemaError


def parse_conversations(obj) -> list:
    """Validate a decoded JSON value: one Conversation object or a list of them."""
    items = [obj] if isinstance(obj, dict) else obj
    if not isinstance(items, list):
        raise SchemaError("expected a Conversation object or a list of them")
    convs = [Conversation.from_dict(x) for x in items]
    ids = [c.id for c in convs]
    if len(set(ids)) != len(ids):
        raise SchemaError("duplicate Conversation.id in file")
    return convs


def load_conversations(path) -> list:
    path = Path(path)
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SchemaError(f"{path.name}: invalid JSON: {e}") from e
    return parse_conversations(obj)
