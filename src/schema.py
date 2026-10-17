"""Record shapes from CONTRACT.md (Conversation, Line, Tag, Flag) with strict validation."""
from dataclasses import dataclass, field
from typing import Optional

CHANNELS = ("call", "text")
LANGUAGES = ("en", "es")
SPEAKERS = ("coach", "participant")
METHODS = ("rule", "classifier")
TIERS = ("S1", "S2", "S3")


class SchemaError(ValueError):
    """Raised when a record does not match CONTRACT.md."""


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise SchemaError(msg)


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _check_keys(d, required, optional, name):
    _require(isinstance(d, dict), f"{name} must be an object")
    missing = [k for k in required if k not in d]
    _require(not missing, f"{name} missing keys: {missing}")
    extra = [k for k in d if k not in required and k not in optional]
    _require(not extra, f"{name} has unknown keys: {extra}")


@dataclass(frozen=True)
class Line:
    idx: int
    speaker: str
    text: str

    @staticmethod
    def from_dict(d) -> "Line":
        _check_keys(d, ("idx", "speaker", "text"), (), "Line")
        _require(_is_int(d["idx"]) and d["idx"] >= 0, "Line.idx must be a non-negative int")
        _require(d["speaker"] in SPEAKERS, f"Line.speaker must be one of {SPEAKERS}")
        _require(isinstance(d["text"], str) and d["text"].strip() != "", "Line.text must be a non-empty string")
        return Line(d["idx"], d["speaker"], d["text"])


@dataclass(frozen=True)
class Conversation:
    id: str
    channel: str
    language: str
    lines: tuple = field(default_factory=tuple)

    @staticmethod
    def from_dict(d) -> "Conversation":
        _check_keys(d, ("id", "channel", "language", "lines"), (), "Conversation")
        _require(isinstance(d["id"], str) and d["id"] != "", "Conversation.id must be a non-empty string")
        _require(d["channel"] in CHANNELS, f"Conversation.channel must be one of {CHANNELS}")
        _require(d["language"] in LANGUAGES, f"Conversation.language must be one of {LANGUAGES}")
        _require(isinstance(d["lines"], list), "Conversation.lines must be a list")
        lines = tuple(Line.from_dict(x) for x in d["lines"])
        _require([l.idx for l in lines] == list(range(len(lines))), "Conversation.lines idx must run 0..n-1 in order")
        return Conversation(d["id"], d["channel"], d["language"], lines)


@dataclass(frozen=True)
class Tag:
    conv_id: str
    line_idx: int
    kind: str
    label: str
    method: str
    rule_id: Optional[str] = None

    @staticmethod
    def from_dict(d) -> "Tag":
        _check_keys(d, ("conv_id", "line_idx", "kind", "label", "method"), ("rule_id",), "Tag")
        _require(isinstance(d["conv_id"], str) and d["conv_id"], "Tag.conv_id must be a non-empty string")
        _require(_is_int(d["line_idx"]) and d["line_idx"] >= 0, "Tag.line_idx must be a non-negative int")
        _require(isinstance(d["kind"], str) and d["kind"], "Tag.kind must be a non-empty string")
        _require(isinstance(d["label"], str) and d["label"], "Tag.label must be a non-empty string")
        _require(d["method"] in METHODS, f"Tag.method must be one of {METHODS}")
        rid = d.get("rule_id")
        _require(rid is None or (isinstance(rid, str) and rid), "Tag.rule_id must be a non-empty string if present")
        _require(d["method"] != "rule" or rid is not None, "Tag.rule_id is required when method is 'rule'")
        return Tag(d["conv_id"], d["line_idx"], d["kind"], d["label"], d["method"], rid)


@dataclass(frozen=True)
class Flag:
    conv_id: str
    line_idx: int
    tier: str
    rule_id: str
    quote: str
    negation_checked: bool
    coach_responded: bool

    @staticmethod
    def from_dict(d) -> "Flag":
        keys = ("conv_id", "line_idx", "tier", "rule_id", "quote", "negation_checked", "coach_responded")
        _check_keys(d, keys, (), "Flag")
        _require(isinstance(d["conv_id"], str) and d["conv_id"], "Flag.conv_id must be a non-empty string")
        _require(_is_int(d["line_idx"]) and d["line_idx"] >= 0, "Flag.line_idx must be a non-negative int")
        _require(d["tier"] in TIERS, f"Flag.tier must be one of {TIERS}")
        _require(isinstance(d["rule_id"], str) and d["rule_id"], "Flag.rule_id must be a non-empty string")
        _require(isinstance(d["quote"], str) and d["quote"].strip(), "Flag.quote must be a non-empty string")
        _require(isinstance(d["negation_checked"], bool), "Flag.negation_checked must be a bool")
        _require(isinstance(d["coach_responded"], bool), "Flag.coach_responded must be a bool")
        return Flag(**{k: d[k] for k in keys})
