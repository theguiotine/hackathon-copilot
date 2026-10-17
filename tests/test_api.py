import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from pathlib import Path

from src.api import DEFAULT_FILES, App, make_handler
from src.loader import load_conversations


class Api(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        convs = [c for f in DEFAULT_FILES for c in load_conversations(f)]
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(App(convs)))
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def req(self, path, data=None):
        r = urllib.request.Request(self.base + path, data=None if data is None else json.dumps(data).encode(),
                                   headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(r) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_queue_sorted_unhandled_first(self):
        code, q = self.req("/api/queue")
        self.assertEqual(code, 200)
        self.assertEqual([i["conv_id"] for i in q], ["fx-en-flag", "fx-es-flag"])
        self.assertTrue(q[0]["unhandled"] and not q[1]["unhandled"])

    def test_conversations_list(self):
        code, cs = self.req("/api/conversations")
        self.assertEqual(code, 200)
        self.assertIn("fx-es-flag", [c["id"] for c in cs])

    def test_call_and_why(self):
        code, c = self.req("/api/call/fx-es-flag")
        self.assertEqual(code, 200)
        self.assertEqual(len(c["conversation"]["lines"]), 3)
        self.assertIn("checklist", c["score"])
        code, w = self.req("/api/why/fx-es-flag")
        self.assertEqual(w["why"][0]["rule_id"], "F-CHEST")
        self.assertEqual(self.req("/api/call/nope")[0], 404)

    def test_analyze_and_bad_body(self):
        body = {"id": "z", "channel": "text", "language": "en",
                "lines": [{"idx": 0, "speaker": "participant", "text": "I have chest pain."}]}
        code, a = self.req("/api/analyze", body)
        self.assertEqual((code, a["flags"][0]["tier"]), (200, "S1"))
        self.assertEqual(self.req("/api/analyze", {"id": "z"})[0], 400)

    def test_eval_not_available_without_summary(self):
        os.environ.pop("COACH_CLASSIFIER_DIR", None)
        self.assertEqual(self.req("/api/eval"), (200, {"available": False}))
        with tempfile.TemporaryDirectory() as d:
            os.environ["COACH_CLASSIFIER_DIR"] = d
            try:
                self.assertEqual(self.req("/api/eval")[1], {"available": False})
                Path(d, "eval_summary.json").write_text("{bad")
                self.assertFalse(self.req("/api/eval")[1]["available"])
            finally:
                del os.environ["COACH_CLASSIFIER_DIR"]

    def test_eval_available_with_summary(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "eval_summary.json").write_text(json.dumps({"held_out_sessions": 21, "caveat": "test only"}))
            os.environ["COACH_CLASSIFIER_DIR"] = d
            try:
                code, body = self.req("/api/eval")
            finally:
                del os.environ["COACH_CLASSIFIER_DIR"]
        self.assertEqual((code, body["available"], body["held_out_sessions"]), (200, True, 21))

    def test_explain_409_unless_approved(self):
        os.environ.pop("LLM_APPROVED", None)
        self.assertEqual(self.req("/api/explain", {})[0], 409)


if __name__ == "__main__":
    unittest.main()
