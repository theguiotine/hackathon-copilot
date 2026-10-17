import json
import shutil
import subprocess
import unittest
from pathlib import Path

FHIR_TS = Path(__file__).resolve().parent.parent / "ui" / "src" / "live" / "fhir.ts"
NODE = shutil.which("node")

SAMPLE = {"id": "hf-001", "severity": "S1", "reason": "The participant mentions chest pain or trouble breathing. Rule F-CHEST, negation checked.",
          "decision": "CONFIRMED", "decisionNote": "Escalated to a nurse today. Reason: x.", "createdAt": "2026-10-09T14:26:00Z",
          "decidedAt": "2026-10-17T13:00:00Z", "lineNumber": 2, "callTitle": "Blood pressure readings"}


def run_node(expr):
    code = f"import * as m from {json.dumps(FHIR_TS.as_uri())}; console.log(JSON.stringify({expr}));"
    out = subprocess.run([NODE, "--input-type=module", "-e", code], capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


@unittest.skipUnless(NODE, "node not installed")
class FhirExport(unittest.TestCase):
    def test_flag_resource_shape(self):
        r = run_node(f"m.buildFhirFlag({json.dumps(SAMPLE)})")
        self.assertEqual(r["resourceType"], "Flag")
        self.assertIn(r["status"], ("active", "inactive"))
        self.assertEqual(r["status"], "active")  # CONFIRMED stays active
        self.assertEqual(r["code"]["text"], "Chest pain or trouble breathing")
        self.assertEqual(r["subject"]["display"], "Invented participant")
        self.assertEqual(r["author"]["display"], "Coach (demo)")
        self.assertEqual(r["period"]["start"], SAMPLE["createdAt"])
        text = json.dumps(r)
        self.assertIn("Escalate to nurse today", text)
        self.assertIn("not validated against an EHR profile", text)
        self.assertNotIn("identifier", r)       # no real identifiers
        self.assertNotIn("@", text)

    def test_inactive_when_handled_or_dismissed(self):
        for d in ("ANNOTATED_WITH_A_NOTE", "DISMISSED_AS_FALSE_ALARMS"):
            r = run_node(f"m.buildFhirFlag({json.dumps(dict(SAMPLE, decision=d))})")
            self.assertEqual(r["status"], "inactive")

    def test_decision_log_csv(self):
        csv = run_node(f"m.decisionLogCsv({json.dumps([SAMPLE, dict(SAMPLE, id='hf-2', decision=None)])})")
        lines = csv.splitlines()
        self.assertEqual(lines[0], "call,line,severity,rule,decision,note,decided_at")
        self.assertEqual(len(lines), 2)         # the undecided flag is not logged
        self.assertIn("Escalate to nurse today", lines[1])
        self.assertIn("F-CHEST", lines[1])


if __name__ == "__main__":
    unittest.main()
