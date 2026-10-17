// Demo FHIR R4 "Flag" export and a small decision log. Hand-built, no library, no real identifiers.
// DEMO STRUCTURE: not validated against any EHR profile or implementation guide.

export const FHIR_DEMO_LABEL = 'Demo structure, not validated against an EHR profile.';

export type FlagForExport = {
  id: string;
  severity: string;            // S1 | S2 | S3
  reason: string;              // contains "Rule F-XXXX"
  decision?: string;           // CONFIRMED | ANNOTATED_WITH_A_NOTE | DISMISSED_AS_FALSE_ALARMS
  decisionNote?: string;
  createdAt: string;
  decidedAt?: string;
  lineNumber?: number;
  callTitle?: string;
};

const RULE_NAMES: Record<string, string> = {
  'F-CRISIS': 'Possible thoughts of self-harm',
  'F-CHEST': 'Chest pain or trouble breathing',
  'F-SYMPTOM': 'Symptom needing same-day review (fever, bleeding, vomiting, lump, severe pain, fainting)',
  'F-DISTRESS': 'Emotional distress',
};
const DECISION_LABEL: Record<string, string> = {
  CONFIRMED: 'Escalate to nurse today',
  ANNOTATED_WITH_A_NOTE: 'Coach already handled it',
  DISMISSED_AS_FALSE_ALARMS: 'Not a real flag',
};

export const ruleOf = (reason: string): string => /Rule (F-[A-Z]+)/.exec(reason)?.[1] ?? 'F-UNKNOWN';
export const ruleName = (reason: string): string => RULE_NAMES[ruleOf(reason)] ?? 'Flag for human review';
export const decisionLabel = (d?: string): string => (d ? DECISION_LABEL[d] ?? d : 'No decision yet');

/** status: a confirmed (escalated) flag stays active; handled or dismissed flags are inactive; undecided flags are active. */
export function buildFhirFlag(f: FlagForExport) {
  const note = [decisionLabel(f.decision), f.decisionNote].filter(Boolean).join(': ');
  return {
    resourceType: 'Flag',
    id: `demo-flag-${f.id}`,
    status: !f.decision || f.decision === 'CONFIRMED' ? 'active' : 'inactive',
    category: [{ coding: [{ system: 'http://terminology.hl7.org/CodeSystem/flag-category', code: 'clinical', display: 'Clinical' }] }],
    code: { text: ruleName(f.reason) },
    subject: { display: 'Invented participant' },
    period: { start: f.createdAt, ...(f.decision && f.decidedAt ? { end: f.decidedAt } : {}) },
    author: { display: 'Coach (demo)' },
    extension: [
      { url: 'http://example.org/demo/StructureDefinition/severity-tier', valueString: f.severity },
      { url: 'http://example.org/demo/StructureDefinition/reviewer-decision', valueString: note },
      { url: 'http://example.org/demo/StructureDefinition/disclaimer', valueString: FHIR_DEMO_LABEL },
    ],
  };
}

const csvCell = (v: unknown): string => `"${String(v ?? '').replace(/"/g, '""')}"`;

/** Decisions made in this session, as CSV (header plus one row per decided flag). */
export function decisionLogCsv(flags: FlagForExport[]): string {
  const head = ['call', 'line', 'severity', 'rule', 'decision', 'note', 'decided_at'];
  const rows = flags.filter((f) => f.decision).map((f) =>
    [f.callTitle, f.lineNumber, f.severity, ruleOf(f.reason), decisionLabel(f.decision), f.decisionNote, f.decidedAt].map(csvCell).join(','));
  return [head.join(','), ...rows].join('\n');
}

export function downloadText(filename: string, text: string, mime: string): void {
  const url = URL.createObjectURL(new Blob([text], { type: mime }));
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
