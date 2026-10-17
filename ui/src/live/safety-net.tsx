// "Caught vs missed" for the needs-a-human flagger, computed by the engine (GET /api/safety) on INVENTED fixtures.
// Nothing here is typed in: every number comes from the API.
import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { WAKING_MESSAGE, getJsonRetry } from './api-client';


type Row = { id: string; language: string; text: string; tier: string | null; gold_tier: string | null; outcome: string };
export type Blind = {
  scope: string; calls: number; flags_raised: number; correct_catches: number; misses: number; false_alarms: number;
  recall: number; s1_recall: number | null; false_alarms_per_10_calls: number; run_at: string;
  by_language: Record<string, { cases: number; positives: number; caught: number; misses: number; false_alarms: number }>;
  misses_list: { language: string; text: string; gold_tier: string }[]; false_alarms_list: { language: string; text: string }[];
};
export type Safety = {
  blind: Blind | null;
  scope: string; calls: number; flags_raised: number; correct_catches: number; misses: number; false_alarms: number;
  recall: number; s1_recall: number | null; false_alarms_per_10_calls: number;
  misses_list: Row[]; false_alarms_list: Row[]; quiet_list: Row[]; sentence: string;
};

export function useSafety(): Safety | null | undefined {
  const [data, setData] = useState<Safety | null | undefined>(undefined);
  useEffect(() => {
    getJsonRetry<Safety>('/api/safety').then((d) => setData(d)).catch(() => setData(null));
  }, []);
  return data;
}

const pct = (x: number) => `${Math.round(x * 100)}%`;

/** One line for the top of the Safety queue. */
export function SafetyLine() {
  const s = useSafety();
  if (!s) return null;
  const b = s.blind;
  return (
    <p className="text-sm text-text-muted" data-testid="safety-line">
      <strong className="text-foreground">Safety net, on invented fixtures only:</strong> {b
        ? <>on a blind set it caught {b.correct_catches} of {b.correct_catches + b.misses} cases that needed a human ({pct(b.recall)}) and missed {b.misses}; on the set the rules were tuned on, {s.correct_catches} of {s.correct_catches + s.misses}.</>
        : <>caught {s.correct_catches} of {s.correct_catches + s.misses} cases that needed a human ({pct(s.recall)}), missed {s.misses}.</>} <Link className="underline" to="/evaluation">See the misses</Link>
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

function BlindCompare({ s }: { s: Safety }) {
  const b = s.blind;
  if (!b) return null;
  const langs = Object.entries(b.by_language).map(([l, v]) => `${l === 'es' ? 'Spanish' : 'English'}: caught ${v.caught} of ${v.positives}`).join(' · ');
  return (
    <div className="flex flex-col gap-2" data-testid="blind-compare">
      <h3 className="font-medium">Two numbers, because the first one flatters</h3>
      <table className="w-full border-collapse text-sm"><thead><tr className="border-b border-border text-left text-text-muted">
        <th className="py-1 pr-4 font-normal">Set</th><th className="py-1 pr-4 font-normal">Recall, S1 to S3</th><th className="py-1 pr-4 font-normal">Recall, S1 only</th><th className="py-1 font-normal">False alarms per 10 calls</th></tr></thead>
        <tbody>
          <tr className="border-b border-border"><td className="py-1 pr-4">Tuned set ({s.calls} invented cases; the rules were adjusted while looking at it)</td><td className="py-1 pr-4 tabular-nums">{pct(s.recall)}</td><td className="py-1 pr-4 tabular-nums">{s.s1_recall === null ? 'n/a' : pct(s.s1_recall)}</td><td className="py-1 tabular-nums">{s.false_alarms_per_10_calls}</td></tr>
          <tr className="border-b border-border"><td className="py-1 pr-4"><strong>Blind set</strong> ({b.calls} invented phrasings, written separately, run once)</td><td className="py-1 pr-4 tabular-nums"><strong>{pct(b.recall)}</strong></td><td className="py-1 pr-4 tabular-nums"><strong>{b.s1_recall === null ? 'n/a' : pct(b.s1_recall)}</strong></td><td className="py-1 tabular-nums">{b.false_alarms_per_10_calls}</td></tr>
        </tbody></table>
      <p className="text-sm text-text-muted">Blind set by language: {langs}. The rules were not changed after this run. The gap between the two rows is the honest warning: the rules catch common wording and miss everyday, informal and indirect phrasing. Invented sentences only; this says nothing about real conversations.</p>
      <Cases title="Missed on the blind set (the rules did not flag these)" rows={b.misses_list.map((m, i) => ({ id: `bm${i}`, language: m.language, text: m.text, tier: null, gold_tier: m.gold_tier, outcome: 'missed' }))} />
      <Cases title="False alarms on the blind set" rows={b.false_alarms_list.map((m, i) => ({ id: `bf${i}`, language: m.language, text: m.text, tier: null, gold_tier: null, outcome: 'false alarm' }))} />
    </div>
  );
}

/** The full section for the Accuracy page. */
export function SafetyNet() {
  const s = useSafety();
  if (s === undefined) return <p className="text-text-muted">{WAKING_MESSAGE}</p>;
  if (s === null) return <p role="status">The server did not answer, so the safety-net check cannot be shown. Reload in a minute.</p>;
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
      <BlindCompare s={s} />
      <Cases title="Missed on the tuned set (the rules did not flag these)" rows={s.misses_list} />
      <Cases title="False alarms (flagged, but a human would not act)" rows={s.false_alarms_list} />
      <Cases title="Stayed quiet, correctly (denials and ordinary talk)" rows={s.quiet_list.slice(0, 4)} />
    </section>
  );
}

/** The plain limits sentence; N comes from the engine (GET /api/limits). */
export function LimitsLine({ className = '' }: { className?: string }) {
  const [d, setD] = useState<{ tuned_cases: number; held_out_sessions: number | null; blind_cases: number | null } | null>(null);
  useEffect(() => {
    getJsonRetry<{ tuned_cases: number; held_out_sessions: number | null; blind_cases: number | null }>('/api/limits').then(setD).catch(() => setD(null));
  }, []);
  if (!d) return null;
  const blind = d.blind_cases === null ? '' : ` and ${d.blind_cases} blind phrasings written separately`;
  const held = d.held_out_sessions === null ? '' : `, plus ${d.held_out_sessions} held-out sessions`;
  return (
    <p className={`text-sm text-text-muted ${className}`} data-testid="limits-line">
      This tool flags sentences for a human to read today. It does not diagnose, rank patients or replace nurse judgment, it can miss things,
      and it was tested only on invented text: {d.tuned_cases} tuned cases{blind}{held}.
    </p>
  );
}
