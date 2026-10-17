// Try a conversation (route /live-analyzer; hand-written, not generated): shows OUR engine (src/api.py) on fictional fixtures or on text the
// user types. Talks to the engine API (same origin when deployed; locally http://127.0.0.1:8000).
import { useEffect, useState } from 'react';
import { WAKING_MESSAGE, getJsonRetry } from './api-client';

type Line = { idx: number; speaker: 'coach' | 'participant'; text: string };
type Tag = { line_idx: number; kind: string; label: string; rule_id: string | null };
type Flag = { line_idx: number; tier: string; rule_id: string; quote: string; coach_responded: boolean };
type Count = { num: number; den: number; lines: number[] };
type Check = { value: string; evidence_lines: number[] };
type Analysis = {
  conv_id: string;
  tags: Tag[];
  flags: Flag[];
  score: { counts: Record<string, Count>; checklist: Record<string, Check> };
};
type Meta = { id: string; language: string; channel: string; lines: number };

const TIER_CLASS: Record<string, string> = {
  S1: 'bg-red-100 text-red-900 border-red-300',
  S2: 'bg-amber-100 text-amber-900 border-amber-300',
  S3: 'bg-sky-100 text-sky-900 border-sky-300',
};

export default function LiveAnalyzer() {
  const [metas, setMetas] = useState<Meta[]>([]);
  const [lines, setLines] = useState<Line[]>([]);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lang, setLang] = useState<'en' | 'es'>('en');
  const [waiting, setWaiting] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [speaker, setSpeaker] = useState<'coach' | 'participant'>('participant');
  const [text, setText] = useState('No puedo respirar');
  const [ruleCount, setRuleCount] = useState<number | null>(null);

  // ?sample=es-chest runs the Spanish chest-pain example straight away; otherwise the box is pre-filled and waits
  // for the Analyze button.
  useEffect(() => {
    if (new URLSearchParams(window.location.search).get('sample') === 'es-chest') {
      const sample = [{ idx: 0, speaker: 'coach', text: '¿Cómo te sientes hoy?' }, { idx: 1, speaker: 'participant', text: 'No puedo respirar bien y tengo dolor de pecho.' }];
      getJsonRetry<Analysis>('/api/analyze', { id: 'sample', channel: 'text', language: 'es', lines: sample }, setWaiting)
        .then((a) => { setLines(sample as Line[]); setAnalysis(a); })
        .catch(() => setError('The server did not answer. Reload this page in a minute.'));
    }
  }, []);

  useEffect(() => {
    getJsonRetry<{ flag_rules?: number }>('/api/limits').then((l) => setRuleCount(l.flag_rules ?? null)).catch(() => setRuleCount(null));
  }, []);

  useEffect(() => {
    getJsonRetry<Meta[]>('/api/conversations', undefined, setWaiting).then(setMetas).catch(() =>
      setError('The server did not answer. Reload this page in a minute.'));
  }, []);

  async function openFixture(id: string) {
    setError(null);
    try {
      const call = await getJsonRetry<Analysis & { conversation: { lines: Line[]; language: 'en' | 'es' } }>(`/api/call/${id}`, undefined, setWaiting);
      setNote(null);
      setLines(call.conversation.lines);
      setLang(call.conversation.language);
      setAnalysis(call);
    } catch (e) { setError((e as Error).message); }
  }

  const langName = (l: 'en' | 'es') => (l === 'es' ? 'Spanish' : 'English');

  async function analyzeTyped() {
    if (!text.trim()) return;
    const next = [...lines, { idx: lines.length, speaker, text: text.trim() }];
    setError(null);
    try {
      const run = (language: 'en' | 'es') => getJsonRetry<Analysis>('/api/analyze', { id: 'typed', channel: 'text', language, lines: next }, setWaiting);
      let a = await run(lang);
      let message: string | null = null;
      if (a.flags.length === 0) {
        // Never hide which language matched: if the other language's rules flag it, show that and say so.
        const other = lang === 'en' ? 'es' : 'en';
        const b = await run(other);
        if (b.flags.length > 0) { a = b; message = `No flag under ${langName(lang)} rules; this conversation matched under ${langName(other)} rules.`; }
      }
      setNote(message); setLines(next); setAnalysis(a); setText('');
    } catch (e) { setError((e as Error).message); }
  }

  const tagsFor = (i: number) => analysis?.tags.filter((t) => t.line_idx === i) ?? [];
  const flagFor = (i: number) => analysis?.flags.find((f) => f.line_idx === i);

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-6" data-testid="live-analyzer">
      <header>
        <p className="type-eyebrow uppercase text-text-muted">Hear Me Out</p>
        <h1 className="type-page-title">Try a conversation</h1>
        <p className="type-body text-text-muted">
          Type or paste a coaching conversation. We highlight any sentence a person should see. It gives no medical advice.
        </p>
      </header>
      <p className="type-body">Type a line in English or Spanish (it starts with a Spanish example) and press <strong>Check this conversation</strong>, or pick a fictional call below.</p>

      {waiting && <p role="status" className="rounded border border-border bg-muted p-3 text-sm">{WAKING_MESSAGE}</p>}
      {note && <p role="status" className="rounded border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900" data-testid="language-note">{note}</p>}
      {error && <p role="alert" className="rounded border border-red-300 bg-red-50 p-3 text-red-900">{error}</p>}

      <section className="flex flex-wrap items-center gap-2">
        <span className="type-meta">Fictional examples:</span>
        {metas.map((m) => (
          <button key={m.id} type="button" onClick={() => openFixture(m.id)}
            className="rounded border border-border bg-background px-3 py-1 text-sm hover:bg-muted">
            {m.id} ({m.language}, {m.channel})
          </button>
        ))}
        <button type="button" onClick={() => { setLines([]); setAnalysis(null); }}
          className="rounded border border-border px-3 py-1 text-sm hover:bg-muted">Clear</button>
      </section>

      <section className="flex flex-col gap-2 rounded border border-border p-3">
        <div className="flex flex-wrap gap-2">
          <select aria-label="Language" value={lang} onChange={(e) => setLang(e.target.value as 'en' | 'es')} className="rounded border border-border p-1">
            <option value="en">English</option><option value="es">Español</option>
          </select>
          <select aria-label="Speaker" value={speaker} onChange={(e) => setSpeaker(e.target.value as 'coach' | 'participant')} className="rounded border border-border p-1">
            <option value="participant">Participant</option><option value="coach">Coach</option>
          </select>
          <input aria-label="Line text" value={text} onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') void analyzeTyped(); }}
            placeholder={lang === 'es' ? 'Escribe una línea, p. ej. No puedo respirar bien' : 'Type a line, e.g. I have had chest pain since last night'}
            className="min-w-64 flex-1 rounded border border-border p-1" />
          <button type="button" onClick={() => void analyzeTyped()} className="rounded bg-primary px-3 py-1 text-primary-foreground">Check this conversation</button>
        </div>
      </section>

      {analysis && analysis.flags.length === 0 && lines.length > 0 && (
        <p role="status" className="rounded border border-border bg-muted p-3 text-sm" data-testid="no-flag-found">
          <strong>No flag found.</strong> {ruleCount !== null ? `Rules checked: ${ruleCount}. ` : ''}This is not a medical clearance.
        </p>
      )}

      {analysis && (
        <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <ol className="flex flex-col gap-3">
            {lines.map((l) => {
              const f = flagFor(l.idx);
              return (
                <li key={l.idx} className={`rounded border p-3 ${f ? TIER_CLASS[f.tier] : 'border-border'}`}>
                  <div className="type-meta flex flex-wrap items-center gap-2">
                    <strong>{l.idx + 1}. {l.speaker}</strong>
                    {tagsFor(l.idx).map((t) => (
                      <span key={t.kind + t.label} className="rounded bg-muted px-2 py-0.5" title={t.rule_id ?? ''}>{t.label}</span>
                    ))}
                    {f && <span className="rounded border px-2 py-0.5 font-semibold">{f.tier} needs a human · {f.coach_responded ? 'coach responded' : 'unhandled'}</span>}
                  </div>
                  <p className="mt-1">{l.text}</p>
                  {f && <p className="type-meta mt-1">Why: rule {f.rule_id} matched, negation checked. Quote: “{f.quote}”</p>}
                </li>
              );
            })}
          </ol>
          <aside className="flex flex-col gap-4">
            <div>
              <h2 className="type-section-title">Counts (num / den)</h2>
              <ul className="type-meta">
                {Object.entries(analysis.score.counts).map(([k, v]) => (
                  <li key={k}>{k}: {v.num} / {v.den}{v.lines.length ? ` (lines ${v.lines.map((n) => n + 1).join(', ')})` : ''}</li>
                ))}
              </ul>
            </div>
            <div>
              <h2 className="type-section-title">Checklist</h2>
              <ul className="type-meta">
                {Object.entries(analysis.score.checklist).map(([k, v]) => (
                  <li key={k}>{k}: <strong>{v.value}</strong>{v.evidence_lines.length ? ` (lines ${v.evidence_lines.map((n) => n + 1).join(', ')})` : ''}</li>
                ))}
              </ul>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
