// "Caught vs missed" for the needs-a-human flagger, computed by the engine (GET /api/safety) on INVENTED fixtures.
// Nothing here is typed in: every number comes from the API.
import { useEffect, useState } from 'react';

const BASE = (import.meta.env.VITE_ENGINE_URL as string | undefined) ?? 'http://127.0.0.1:8000';

type Row = { id: string; language: string; text: string; tier: string | null; gold_tier: string | null; outcome: string };
export type Safety = {
  scope: string; calls: number; flags_raised: number; correct_catches: number; misses: number; false_alarms: number;
  recall: number; s1_recall: number | null; false_alarms_per_10_calls: number;
  misses_list: Row[]; false_alarms_list: Row[]; quiet_list: Row[]; sentence: string;
};

export function useSafety(): Safety | null | undefined {
  const [data, setData] = useState<Safety | null | undefined>(undefined);
  useEffect(() => {
    fetch(`${BASE}/api/safety`).then((r) => r.json()).then((d: Safety) => setData(d)).catch(() => setData(null));
  }, []);
  return data;
}

const pct = (x: number) => `${Math.round(x * 100)}%`;

/** One line for the top of the Safety queue. */
export function SafetyLine() {
  const s = useSafety();
  if (!s) return null;
  return (
    <p className="text-sm text-text-muted" data-testid="safety-line">
      <strong className="text-foreground">Safety net, on invented fixtures:</strong> caught {s.correct_catches} of {s.correct_catches + s.misses} cases that
      needed a human ({pct(s.recall)}), missed {s.misses}, {s.false_alarms_per_10_calls} false alarms per 10 calls. <a className="underline" href="/evaluation">See the misses</a>
    </p>
  );
}

function Cases({ title, rows }: { title: string; rows: Row[] }) {
  if (rows.length === 0) return null;
  return (
    <div className="mb-3">
      <h4 className="font-medium">{title}</h4>
      <ul className="list-disc pl-5 text-sm">
        {rows.map((r) => <li key={r.id}>“{r.text}” <span className="text-text-muted">({r.language === 'es' ? 'Spanish' : 'English'}{r.gold_tier ? `, should be ${r.gold_tier}` : ''})</span></li>)}
      </ul>
    </div>
  );
}

/** The full section for the Accuracy page. */
export function SafetyNet() {
  const s = useSafety();
  if (s === undefined) return <p className="text-text-muted">Loading the safety-net check…</p>;
  if (s === null) return <p role="status">The engine is not running, so the safety-net check cannot be shown.</p>;
  const cells: [string, string | number][] = [
    ['Cases checked', s.calls], ['Flags raised', s.flags_raised], ['Correct catches', s.correct_catches], ['Misses', s.misses],
    ['False alarms', s.false_alarms], ['Recall, S1 to S3', pct(s.recall)], ['Recall, S1 only', s.s1_recall === null ? 'n/a' : pct(s.s1_recall)],
    ['False alarms per 10 calls', s.false_alarms_per_10_calls],
  ];
  return (
    <section className="flex max-w-3xl flex-col gap-3" data-testid="safety-net">
      <h2 className="type-section-title">Safety net: caught versus missed</h2>
      <p className="rounded border border-border bg-muted p-3 text-sm"><strong>{s.sentence}</strong></p>
      <p className="text-sm text-text-muted">{s.scope} Every number below is computed by the engine just now.</p>
      <table className="w-full border-collapse text-sm"><tbody>
        {cells.map(([k, v]) => (
          <tr key={k} className="border-b border-border"><th scope="row" className="py-1 pr-4 text-left font-normal text-text-muted">{k}</th><td className="py-1 text-right tabular-nums">{v}</td></tr>
        ))}
      </tbody></table>
      <Cases title="Missed (the rules did not flag these)" rows={s.misses_list} />
      <Cases title="False alarms (flagged, but a human would not act)" rows={s.false_alarms_list} />
      <Cases title="Stayed quiet, correctly (denials and ordinary talk)" rows={s.quiet_list.slice(0, 4)} />
    </section>
  );
}

/** The plain limits sentence; N comes from the engine (GET /api/limits). */
export function LimitsLine({ className = '' }: { className?: string }) {
  const [d, setD] = useState<{ invented_conversations: number; held_out_sessions: number | null } | null>(null);
  useEffect(() => {
    fetch(`${BASE}/api/limits`).then((r) => r.json()).then(setD).catch(() => setD(null));
  }, []);
  if (!d) return null;
  const held = d.held_out_sessions === null ? '' : ` plus ${d.held_out_sessions} held-out sessions`;
  return (
    <p className={`text-sm text-text-muted ${className}`} data-testid="limits-line">
      This tool flags sentences for a human to read today. It does not diagnose, rank patients or replace nurse judgment, it can miss things,
      and it was tested only on {d.invented_conversations} invented sample conversations{held}.
    </p>
  );
}
