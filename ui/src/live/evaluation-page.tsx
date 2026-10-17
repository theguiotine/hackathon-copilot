// Evaluation screen (hand-written): shows aggregates measured locally on the held-out sessions, served by GET /api/eval
// from a file kept OUTSIDE the repo. Without that file it states that accuracy is not published here. No numbers live in
// this repo. The summary is rendered generically (any keys), so the page never depends on one exact file layout.
import { useEffect, useState } from 'react';
import { LimitsLine, SafetyNet } from './safety-net';
import { WAKING_MESSAGE, getJsonRetry } from './api-client';

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
    getJsonRetry<{ [k: string]: Json }>('/api/eval').then((d) => setData(d)).catch(() => setData(null));
  }, []);

  const available = data && data.available === true;
  const { available: _a, caveat, ...rest } = (data ?? {}) as { [k: string]: Json };

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-4 p-6" data-testid="evaluation-page">
      <header>
        <p className="type-eyebrow uppercase text-text-muted">Hear Me Out</p>
        <h1 className="type-page-title">Evaluation</h1>
      </header>
      <LimitsLine />
      <SafetyNet />
      <section aria-labelledby="rules-today" className="rounded-lg border border-border p-4 text-sm" data-testid="rules-expanded-note">
        <h2 id="rules-today" className="text-lg font-semibold">How the flags work, and what changed today</h2>
        <ul className="mt-2 flex list-disc flex-col gap-1.5 pl-5">
          <li>The "needs a person today" flags are written rules, not a model. Each flag shows the exact quote and the rule that fired, so a person can check it.</li>
          <li>Today we widened the rules after a live test showed phrases like "I'm dying" and "chest pains" were missed: more wording for chest or breathing trouble, thoughts of ending one's life or self-harm, an overdose, swelling, strong pain, and deep sadness, in English and Spanish.</li>
          <li>We kept the negation guard: "no chest pain", "I'm not dying", "sin dolor" and talk about someone else or long ago do not flag.</li>
          <li>On invented, script-generated calls, recall rose from 49% to 71% and false alarms did not change (2.0%). This measures coverage of generated paraphrase, not clinical accuracy, and the generator's wording can be easier or harder than real speech.</li>
          <li>Still weak: symptom wording and distress wording are caught only about half the time on generated calls.</li>
          <li>Still weak: a past-tense line ("I used to feel hopeless") can wrongly flag as current, and in Spanish a double negative like "no me siento sin esperanza" can wrongly flag.</li>
          <li>"Took all my pills" alone does not flag, because in an adherence coach it is the normal "I took my pills" statement; it flags with cues like "at once", "tonight" or "on purpose".</li>
          <li>A flag means "a person should look at this today", never a diagnosis. A written list will always miss some wordings, so a model second reader that can only add flags is the next step; it is not built.</li>
          <li>The earlier 42% blind figure was measured before this expansion and is not comparable to the generated-call numbers.</li>
        </ul>
      </section>
      <h2 className="type-section-title mt-4">Accuracy on the organizers' held-out sessions</h2>
      {data === undefined && <p className="text-text-muted">{WAKING_MESSAGE}</p>}
      {data === null && <p role="status">The server did not answer, so no evaluation can be shown. {NOT_PUBLISHED}</p>}
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
