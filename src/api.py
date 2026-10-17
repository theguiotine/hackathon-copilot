"""Local JSON API from CONTRACT.md routes (stdlib only, no network calls out).

Run:  python3 -m src.api [--port 8000] [--conversations tests/fixtures/conversations.json ...]
Defaults to the fictional fixtures. It never reads COACH_DATA_DIR on its own.
"""
import argparse
import json
import mimetypes
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .flagger.rules import flag_conversation
from .loader import load_conversations
from .schema import Conversation, SchemaError
from . import safety_eval
from .score.card import score_conversation
from .tagger.rules import tag_conversation

FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
DEFAULT_FILES = [FIXTURES / "conversations.json", FIXTURES / "flag_cases.json"]
# Only the local UI may call this API from a browser; extra origins via COACH_UI_ORIGINS (comma-separated).
DEFAULT_ORIGINS = ("http://127.0.0.1:3000", "http://localhost:3000")


def allowed_origins():
    extra = [o.strip() for o in os.environ.get("COACH_UI_ORIGINS", "").split(",") if o.strip()]
    return set(DEFAULT_ORIGINS) | set(extra)


def host_ok(host):
    """Reject DNS-rebinding: only loopback host names are served, plus any named in COACH_ALLOWED_HOSTS (a deliberate
    deployment setting, comma-separated host names without ports)."""
    name = (host or "").rsplit(":", 1)[0].strip("[]")
    extra = {h.strip() for h in os.environ.get("COACH_ALLOWED_HOSTS", "").split(",") if h.strip()}
    if os.environ.get("RENDER_EXTERNAL_HOSTNAME"):  # the web host's own name, set by the platform
        extra.add(os.environ["RENDER_EXTERNAL_HOSTNAME"])
    return name in ("127.0.0.1", "localhost", "::1") or name in extra


def static_file(url_path):
    """For a single-service deployment: serve the built UI from $COACH_STATIC_DIR (never anything outside it).
    Unknown non-asset paths fall back to index.html so in-app routes work on reload. None if not configured."""
    root = os.environ.get("COACH_STATIC_DIR")
    if not root:
        return None
    base = Path(root).resolve()
    rel = url_path.lstrip("/") or "index.html"
    target = (base / rel).resolve()
    if base not in target.parents and target != base:
        return None
    if not target.is_file():
        if "." in rel.rsplit("/", 1)[-1]:
            return None  # a missing asset is a 404, not index.html
        target = base / "index.html"
        if not target.is_file():
            return None
    return target, mimetypes.guess_type(str(target))[0] or "application/octet-stream"


TIER_ORDER = {"S1": 0, "S2": 1, "S3": 2}


def eval_summary():
    """Aggregates the owner computed locally, from $COACH_CLASSIFIER_DIR/eval_summary.json; never stored in the repo.

    The file must be a regular file directly inside that folder: symlinks are refused and the resolved path must stay
    inside the resolved folder, so this route can never read anything else.
    """
    directory = os.environ.get("COACH_CLASSIFIER_DIR")
    if not directory:
        return {"available": False}
    base = Path(directory).expanduser().resolve()
    path = base / "eval_summary.json"
    if path.is_symlink() or not path.is_file() or path.resolve().parent != base:
        return {"available": False}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return {"available": False, "error": "eval_summary.json is not valid JSON"}
    return {"available": True, **data} if isinstance(data, dict) else {"available": False}


def _dump(o):
    return o.__dict__ if hasattr(o, "__dict__") else o


def analyze(conv: Conversation) -> dict:
    return {"conv_id": conv.id, "tags": [_dump(t) for t in tag_conversation(conv)],
            "flags": [_dump(f) for f in flag_conversation(conv)], "score": score_conversation(conv)}


BLIND_RESULTS = FIXTURES / "blind_results.json"


def blind_results():
    """The one-time blind-set run (counts plus the missed invented sentences), if its results file is present."""
    try:
        return json.loads(BLIND_RESULTS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def safety_payload():
    out = safety_eval.run()
    out["blind"] = blind_results()
    return out


def limits(app):
    """Counts for the plain limits line, computed here: invented conversations tested, and held-out sessions if the
    owner's local summary names them."""
    cases = safety_eval.run()["calls"]
    held = eval_summary().get("held_out_sessions")
    blind = blind_results()
    return {"invented_conversations": cases + len(app.convs),
            "held_out_sessions": held if isinstance(held, int) else None,
            "blind_cases": blind["calls"] if blind else None}


class App:
    def __init__(self, convs):
        self.convs = {c.id: c for c in convs}

    def queue(self):
        items = []
        for c in self.convs.values():
            flags = flag_conversation(c)
            if flags:
                best = min(flags, key=lambda f: (TIER_ORDER[f.tier], f.coach_responded))
                items.append({"conv_id": c.id, "language": c.language, "channel": c.channel, "tier": best.tier,
                              "unhandled": any(not f.coach_responded for f in flags), "flags": [_dump(f) for f in flags]})
        return sorted(items, key=lambda i: (TIER_ORDER[i["tier"]], not i["unhandled"], i["conv_id"]))

    def call(self, cid):
        c = self.convs.get(cid)
        if not c:
            return None
        out = analyze(c)
        out["conversation"] = {"id": c.id, "channel": c.channel, "language": c.language, "lines": [_dump(l) for l in c.lines]}
        return out

    def why(self, cid):
        c = self.convs.get(cid)
        if not c:
            return None
        return {"conv_id": cid, "why": [{"line_idx": f.line_idx, "tier": f.tier, "rule_id": f.rule_id, "quote": f.quote,
                                         "negation_checked": f.negation_checked, "coach_responded": f.coach_responded}
                                        for f in flag_conversation(c)]}


def make_handler(app: App):
    class H(BaseHTTPRequestHandler):
        def _send(self, code, obj):
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            origin = self.headers.get("Origin")
            self.send_header("Vary", "Origin")
            if origin and origin in allowed_origins():
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Access-Control-Allow-Headers", "content-type")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):
            self._send(204, {})

        def do_GET(self):
            if not host_ok(self.headers.get("Host")):
                return self._send(421, {"error": "unexpected host"})
            path = self.path.split("?")[0]
            if path == "/api/conversations":
                return self._send(200, [{"id": c.id, "language": c.language, "channel": c.channel, "lines": len(c.lines)}
                                        for c in app.convs.values()])
            if path == "/api/limits":
                return self._send(200, limits(app))
            if path == "/api/safety":
                return self._send(200, safety_payload())
            if path == "/api/queue":
                return self._send(200, app.queue())
            m = re.fullmatch(r"/api/(call|why)/(.+)", path)
            if m:
                res = getattr(app, m.group(1))(m.group(2))
                return self._send(200, res) if res else self._send(404, {"error": "unknown conversation"})
            if path == "/api/eval":
                return self._send(200, eval_summary())
            hit = static_file(path)
            if hit is not None and not path.startswith("/api/"):
                target, ctype = hit
                body = target.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self._send(404, {"error": "not found"})

        def do_POST(self):
            if not host_ok(self.headers.get("Host")):
                return self._send(421, {"error": "unexpected host"})
            path = self.path.split("?")[0]
            if path == "/api/explain":
                if os.environ.get("LLM_APPROVED") != "1":
                    return self._send(409, {"error": "LLM module is off (LLM_APPROVED not set)"})
                return self._send(501, {"error": "not implemented"})
            if path == "/api/analyze":
                try:
                    n = int(self.headers.get("Content-Length", "0"))
                    conv = Conversation.from_dict(json.loads(self.rfile.read(n).decode("utf-8")))
                except (SchemaError, ValueError) as e:
                    return self._send(400, {"error": str(e)})
                return self._send(200, analyze(conv))
            self._send(404, {"error": "not found"})

        def log_message(self, *a):
            pass
    return H


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    ap.add_argument("--host", default=os.environ.get("COACH_HOST", "127.0.0.1"),
                    help="bind address; 127.0.0.1 locally, 0.0.0.0 only for a deliberate public deployment")
    ap.add_argument("--conversations", nargs="*", default=[str(p) for p in DEFAULT_FILES])
    args = ap.parse_args(argv)
    convs = [c for f in args.conversations for c in load_conversations(f)]
    print(f"Serving {len(convs)} conversations on http://{args.host}:{args.port}")
    ThreadingHTTPServer((args.host, args.port), make_handler(App(convs))).serve_forever()


if __name__ == "__main__":
    main()
