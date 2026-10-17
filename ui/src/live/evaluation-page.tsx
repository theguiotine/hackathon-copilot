// Evaluation screen (hand-written): shows aggregates measured locally on the held-out sessions, served by GET /api/eval
// from a file kept OUTSIDE the repo. Without that file it states that accuracy is not published here. No numbers live in
// this repo. The summary is rendered generically (any keys), so the page never depends on one exact file layout.
import { useEffect, useState } from 'react';
import { SafetyNet } from './safety-net';

const BASE = (import.meta.env.VITE_ENGINE_URL as string | undefined) ?? 'http://127.0.0.1:8000';
type Json = string | number | boolean | null | Json[] | { [k: string]: Json };

const NOT_PUBLISHED = "Accuracy is measured locally on the organizers' data and is not published in this repo.";

const pretty = (key: string) => key.replace(/_/g, ' ');
const fmt = (v: Json) => (typeof v === 'number' ? (Number.isInteger(v) ? String(v) : v.toFixed(3)) : String(v));

function Node({ name, value, depth }: { name: string; value: Json; depth: number }) {
  if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
    return (
      <section className="mb-4">
        {depth > 0 && <h3 className="type-section-title capitalize">{pretty(name)}</h3>}
        <table className="w-full max-w-3xl border-collapse text-sm">
          <tbody>
            {Object.entries(value).map(([k, v]) =>
              v !== null && typeof v === 'object' ? (
                <tr key={k}><td colSpan={2} className="pt-3"><Node name={k} value={v} depth={depth + 1} /></td></tr>
              ) : (
                <tr key={k} className="border-b border-border">
                  <th scope="row" className="py-1 pr-4 text-left font-normal capitalize text-text-muted">{pretty(k)}</th>
                  <td className="py-1 text-right tabular-nums">{fmt(v)}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </section>
    );
  }
  if (Array.isArray(value)) {
    return (
      <section className="mb-4">
        <h3 className="type-section-title capitalize">{pretty(name)}</h3>
        <ul className="list-disc pl-5 text-sm">{value.map((v, i) => <li key={i}>{typeof v === 'object' ? JSON.stringify(v) : fmt(v)}</li>)}</ul>
      </section>
    );
  }
  return <p className="text-sm">{fmt(value)}</p>;
}

export default function EvaluationPage() {
  const [data, setData] = useState<{ [k: string]: Json } | null | undefined>(undefined);

  useEffect(() => {
    fetch(`${BASE}/api/eval`).then((r) => r.json()).then((d: { [k: string]: Json }) => setData(d)).catch(() => setData(null));
  }, []);

  const available = data && data.available === true;
  const { available: _a, caveat, ...rest } = (data ?? {}) as { [k: string]: Json };

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-4 p-6" data-testid="evaluation-page">
      <header>
        <p className="type-eyebrow uppercase text-text-muted">Coach's Copilot</p>
        <h1 className="type-page-title">Evaluation</h1>
      </header>
      <SafetyNet />
      <h2 className="type-section-title mt-4">Accuracy on the organizers' held-out sessions</h2>
      {data === undefined && <p className="text-text-muted">Loading…</p>}
      {data === null && <p role="status">The engine is not running, so no evaluation can be shown. {NOT_PUBLISHED}</p>}
      {data && !available && <p role="status">{NOT_PUBLISHED}</p>}
      {available && (
        <>
          <p className="text-sm text-text-muted">Measured on held-out sessions the classifier never trained on. These figures come from a local file, not from this repo.</p>
          <Node name="summary" value={rest as { [k: string]: Json }} depth={0} />
          {typeof caveat === 'string' && <p className="max-w-3xl rounded border border-border bg-muted p-3 text-sm"><strong>Caveat: </strong>{caveat}</p>}
        </>
      )}
    </div>
  );
}
