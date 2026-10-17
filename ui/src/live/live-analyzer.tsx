// Live analyzer (hand-written, not generated): shows OUR engine (src/api.py) on fictional fixtures or on text the
// user types. Needs the local API: `python3 -m src.api` (default http://127.0.0.1:8000, override VITE_ENGINE_URL).
import { useEffect, useState } from 'react';

const BASE = (import.meta.env.VITE_ENGINE_URL as string | undefined) ?? 'http://127.0.0.1:8000';

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

async function getJson<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(BASE + path, body === undefined ? undefined : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error ?? res.statusText);
  return data as T;
}

export default function LiveAnalyzer() {
  const [metas, setMetas] = useState<Meta[]>([]);
  const [lines, setLines] = useState<Line[]>([]);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lang, setLang] = useState<'en' | 'es'>('es');
  const [speaker, setSpeaker] = useState<'coach' | 'participant'>('participant');
  const [text, setText] = useState('No puedo respirar');

  // ?sample=es-chest runs the Spanish chest-pain example straight away; otherwise the box is pre-filled and waits
  // for the Analyze button.
  useEffect(() => {
    if (new URLSearchParams(window.location.search).get('sample') === 'es-chest') {
      const sample = [{ idx: 0, speaker: 'coach', text: '¿Cómo te sientes hoy?' }, { idx: 1, speaker: 'participant', text: 'No puedo respirar bien y tengo dolor de pecho.' }];
      getJson<Analysis>('/api/analyze', { id: 'sample', channel: 'text', language: 'es', lines: sample })
        .then((a) => { setLines(sample as Line[]); setAnalysis(a); })
        .catch((e: Error) => setError(`Engine not reachable at ${BASE}: ${e.message}. Start it with: python3 -m src.api`));
    }
  }, []);

  useEffect(() => {
    getJson<Meta[]>('/api/conversations').then(setMetas).catch((e: Error) =>
      setError(`Engine not reachable at ${BASE}: ${e.message}. Start it with: python3 -m src.api`));
  }, []);

  async function openFixture(id: string) {
    setError(null);
    try {
      const call = await getJson<Analysis & { conversation: { lines: Line[]; language: 'en' | 'es' } }>(`/api/call/${id}`);
      setLines(call.conversation.lines);
      setLang(call.conversation.language);
      setAnalysis(call);
    } catch (e) { setError((e as Error).message); }
  }

  async function analyzeTyped() {
    if (!text.trim()) return;
    const next = [...lines, { idx: lines.length, speaker, text: text.trim() }];
    setError(null);
    try {
      const a = await getJson<Analysis>('/api/analyze', { id: 'typed', channel: 'text', language: lang, lines: next });
      setLines(next); setAnalysis(a); setText('');
    } catch (e) { setError((e as Error).message); }
  }

  const tagsFor = (i: number) => analysis?.tags.filter((t) => t.line_idx === i) ?? [];
  const flagFor = (i: number) => analysis?.flags.find((f) => f.line_idx === i);

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-6" data-testid="live-analyzer">
      <header>
        <p className="type-eyebrow uppercase text-text-muted">Coach's Copilot</p>
        <h1 className="type-page-title">Live analyzer</h1>
        <p className="type-body text-text-muted">
          Runs the real tagger, needs-a-human flagger and score card on fictional lines. It flags a person and quotes
          the sentence; it gives no medical advice.
        </p>
      </header>
      <p className="type-body">Type a line (it starts with a Spanish example) and press <strong>Analyze</strong>, or pick a fictional call below.</p>

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
            <option value="es">Español</option><option value="en">English</option>
          </select>
          <select aria-label="Speaker" value={speaker} onChange={(e) => setSpeaker(e.target.value as 'coach' | 'participant')} className="rounded border border-border p-1">
            <option value="participant">Participant</option><option value="coach">Coach</option>
          </select>
          <input aria-label="Line text" value={text} onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') void analyzeTyped(); }}
            placeholder={lang === 'es' ? 'Escribe una línea, p. ej. No puedo respirar bien' : 'Type a line, e.g. I have had chest pain since last night'}
            className="min-w-64 flex-1 rounded border border-border p-1" />
          <button type="button" onClick={() => void analyzeTyped()} className="rounded bg-primary px-3 py-1 text-primary-foreground">Analyze</button>
        </div>
      </section>

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
