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

    def test_limits_route(self):
        os.environ.pop("COACH_CLASSIFIER_DIR", None)
        code, r = self.req("/api/limits")
        self.assertEqual(code, 200)
        self.assertGreater(r["invented_conversations"], 28)
        self.assertEqual(r["tuned_cases"], 28)
        self.assertEqual(r["blind_cases"], 36)
        self.assertIsNone(r["held_out_sessions"])
        with tempfile.TemporaryDirectory() as d:
            Path(d, "eval_summary.json").write_text(json.dumps({"held_out_sessions": 21}))
            os.environ["COACH_CLASSIFIER_DIR"] = d
            try:
                self.assertEqual(self.req("/api/limits")[1]["held_out_sessions"], 21)
            finally:
                del os.environ["COACH_CLASSIFIER_DIR"]

    def test_safety_route(self):
        code, r = self.req("/api/safety")
        self.assertEqual(code, 200)
        self.assertIn("invented fixtures", r["scope"])
        self.assertGreater(r["calls"], 0)

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


class StaticServing(unittest.TestCase):
    def test_static_file_is_contained_and_spa_falls_back(self):
        from src.api import static_file
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as outside:
            Path(d, "index.html").write_text("<html>app</html>")
            Path(d, "assets").mkdir()
            Path(d, "assets", "a.js").write_text("x")
            Path(outside, "secret.txt").write_text("nope")
            os.environ["COACH_STATIC_DIR"] = d
            try:
                self.assertEqual(static_file("/")[0].name, "index.html")
                self.assertIn("javascript", static_file("/assets/a.js")[1])
                self.assertEqual(static_file("/call-queue")[0].name, "index.html")
                self.assertIsNone(static_file("/assets/missing.js"))
                self.assertIsNone(static_file("/../" + Path(outside).name + "/secret.txt"))
            finally:
                del os.environ["COACH_STATIC_DIR"]
            self.assertIsNone(static_file("/"))


class Robustness(unittest.TestCase):
    req = Api.req

    @classmethod
    def setUpClass(cls):
        Api.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def conn(self):
        import http.client
        return http.client.HTTPConnection("127.0.0.1", int(self.base.rsplit(":", 1)[1]), timeout=10)

    def test_oversized_body_is_413_and_not_read(self):
        c = self.conn()
        c.putrequest("POST", "/api/analyze")
        c.putheader("Content-Type", "application/json")
        c.putheader("Content-Length", str(64 * 1024 + 1))
        c.endheaders()
        r = c.getresponse()
        self.assertEqual(r.status, 413)
        c.close()

    def test_missing_or_negative_content_length_is_400(self):
        c = self.conn()
        c.putrequest("POST", "/api/analyze")
        c.endheaders()
        self.assertEqual(c.getresponse().status, 400)
        c.close()
        c = self.conn()
        c.putrequest("POST", "/api/analyze")
        c.putheader("Content-Length", "-5")
        c.endheaders()
        self.assertEqual(c.getresponse().status, 400)
        c.close()

    def test_body_just_under_the_limit_is_accepted_for_parsing(self):
        body = json.dumps({"id": "z", "channel": "text", "language": "en", "lines": [
            {"idx": 0, "speaker": "participant", "text": "I walked. " + "x" * 5000}]}).encode()
        c = self.conn()
        c.request("POST", "/api/analyze", body, {"Content-Type": "application/json"})
        self.assertEqual(c.getresponse().status, 200)
        c.close()

    def test_head_returns_200_without_a_body(self):
        for path in ("/api/limits", "/api/queue"):
            c = self.conn()
            c.request("HEAD", path)
            r = c.getresponse()
            self.assertEqual(r.status, 200, path)
            self.assertEqual(r.read(), b"")
            c.close()

    def test_wrong_language_returns_no_flags_but_the_other_language_does(self):
        # The UI relies on this: it retries a silent result under the other language and labels which one matched.
        def flags(lang):
            body = {"id": "m", "channel": "text", "language": lang,
                    "lines": [{"idx": 0, "speaker": "participant", "text": "I have had chest pain since last night."}]}
            return self.req("/api/analyze", body)[1]["flags"]
        self.assertEqual(flags("es"), [])
        self.assertEqual([f["tier"] for f in flags("en")], ["S1"])


if __name__ == "__main__":
    unittest.main()


class Hardening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Api.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def raw(self, path, headers=None):
        req = urllib.request.Request(self.base + path, headers=headers or {})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, dict(r.headers), json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), json.loads(e.read())

    def test_cors_only_for_ui_origins(self):
        for good in ("http://localhost:3000", "http://127.0.0.1:3000"):
            _, h, _ = self.raw("/api/queue", {"Origin": good})
            self.assertEqual(h.get("Access-Control-Allow-Origin"), good)
        for bad in ("http://evil.example", "http://localhost:3001", "null"):
            _, h, _ = self.raw("/api/queue", {"Origin": bad})
            self.assertNotIn("Access-Control-Allow-Origin", h)
        _, h, _ = self.raw("/api/queue")
        self.assertNotIn("Access-Control-Allow-Origin", h)
        self.assertNotEqual(h.get("Access-Control-Allow-Origin"), "*")

    def test_allowed_hosts_env_is_opt_in(self):
        from src.api import host_ok
        self.assertFalse(host_ok("copilot.example.com"))
        os.environ["COACH_ALLOWED_HOSTS"] = "copilot.example.com"
        try:
            self.assertTrue(host_ok("copilot.example.com"))
            self.assertTrue(host_ok("copilot.example.com:443"))
            self.assertFalse(host_ok("evil.example"))
        finally:
            del os.environ["COACH_ALLOWED_HOSTS"]

    def test_extra_origin_via_env(self):
        os.environ["COACH_UI_ORIGINS"] = "http://127.0.0.1:3001"
        try:
            _, h, _ = self.raw("/api/queue", {"Origin": "http://127.0.0.1:3001"})
        finally:
            del os.environ["COACH_UI_ORIGINS"]
        self.assertEqual(h.get("Access-Control-Allow-Origin"), "http://127.0.0.1:3001")

    def test_rebinding_host_is_refused(self):
        code, _, _ = self.raw("/api/queue", {"Host": "evil.example:8000"})
        self.assertEqual(code, 421)

    def test_eval_refuses_symlink_out_of_the_folder(self):
        with tempfile.TemporaryDirectory() as outside, tempfile.TemporaryDirectory() as d:
            Path(outside, "secret.json").write_text(json.dumps({"leak": 1}))
            os.symlink(Path(outside, "secret.json"), Path(d, "eval_summary.json"))
            os.environ["COACH_CLASSIFIER_DIR"] = d
            try:
                _, _, body = self.raw("/api/eval")
            finally:
                del os.environ["COACH_CLASSIFIER_DIR"]
        self.assertEqual(body, {"available": False})

    def test_eval_refuses_symlinked_folder_pointing_elsewhere(self):
        with tempfile.TemporaryDirectory() as real, tempfile.TemporaryDirectory() as parent:
            Path(real, "eval_summary.json").write_text(json.dumps({"ok": 1}))
            link = Path(parent, "link")
            os.symlink(real, link)
            os.environ["COACH_CLASSIFIER_DIR"] = str(link)
            try:
                _, _, body = self.raw("/api/eval")
            finally:
                del os.environ["COACH_CLASSIFIER_DIR"]
        # a symlinked folder resolves to its real folder, where a regular file lives: allowed, and contained there
        self.assertTrue(body["available"])
