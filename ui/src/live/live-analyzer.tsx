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

// Plain labels for the fictional examples (confirmed from the fixture files); unknown ids keep the old label.
const EXAMPLE_LABELS: Record<string, string> = {
  'fx-en-1': 'English call: routine walking check-in',
  'fx-es-1': 'Spanish text: routine check-in',
  'fx-en-flag': 'English text: chest pain (needs a person)',
  'fx-es-flag': 'Spanish text: dolor de pecho (needs a person)',
  'fx-en-neg': 'English call: denies chest pain (stays quiet)',
  'fx-es-neg': 'Spanish call: denies chest pain (stays quiet)',
};

const MOVE_LABELS: Record<string, string> = {
  open_question: 'Open question', closed_question: 'Closed question', simple_reflection: 'Simple reflection',
  complex_reflection: 'Deeper reflection', affirm: 'Affirmation', seek_collaboration: 'Seeks collaboration',
  emphasize_autonomy: 'Respects their choice', ask_permission: 'Asks permission', give_information: 'Gives information',
  persuade: 'Persuading', confront: 'Confronting', other: 'Other',
  change: 'Change talk', sustain: 'Sustain talk', neutral: 'Neutral',
};
const humanize = (k: string) => MOVE_LABELS[k] ?? k.replace(/_/g, ' ');

const COUNT_LABELS: Record<string, [string, string]> = {
  open_question_share: ['Open questions', 'of the coach\'s questions invited a longer answer'],
  reflection_to_question: ['Reflections per question', 'how often the coach reflected back instead of asking'],
  complex_reflection_share: ['Deeper reflections', 'of the coach\'s reflections added meaning, not just repeated'],
  mi_consistent_share: ['Moves that support change', 'of the coach\'s moves fit motivational interviewing'],
  mi_inconsistent: ['Moves that work against change', 'such as persuading or confronting'],
};
const CHECK_LABELS: Record<string, string> = {
  set_agenda: 'Set the agenda for the call', checked_feelings: 'Checked in on feelings', reviewed_last_goal: 'Reviewed the last goal',
  set_new_goal: 'Set a new goal', planned_for_barriers: 'Planned for barriers', summarized: 'Summarized the call',
  set_next_contact: 'Set the next contact', safety_issue_handled: 'Coach responded to a safety line',
};
const WHY_RULE: Record<string, string> = {
  'F-CRISIS': 'mentions thoughts of ending their life', 'F-CHEST': 'mentions chest pain or trouble breathing',
  'F-SYMPTOM': 'mentions a symptom (fever, bleeding, vomiting, a new lump or severe pain)', 'F-DISTRESS': 'sounds overwhelmed, hopeless or alone',
};

export default function LiveAnalyzer() {
  const [metas, setMetas] = useState<Meta[]>([]);
  const [lines, setLines] = useState<Line[]>([]);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lang, setLang] = useState<'en' | 'es'>('es'); // the box starts with a Spanish example
  const [waiting, setWaiting] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [speaker, setSpeaker] = useState<'coach' | 'participant'>('participant');
  const [text, setText] = useState('No puedo respirar');
  const [ruleCount, setRuleCount] = useState<number | null>(null);

  // ?sample=es-chest runs the Spanish chest-pain example straight away; otherwise the box is pre-filled and waits
  // for the "Check this conversation" button.
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
            {EXAMPLE_LABELS[m.id] ?? `${m.id} (${m.language}, ${m.channel})`}
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
          <select aria-label="Who said this line?" title="Who said this line?" value={speaker} onChange={(e) => setSpeaker(e.target.value as 'coach' | 'participant')} className="rounded border border-border p-1">
            <option value="participant">Patient said it</option><option value="coach">Coach said it</option>
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
                      <span key={t.kind + t.label} className="rounded bg-muted px-2 py-0.5" title={t.rule_id ?? ''}>{humanize(t.label)}</span>
                    ))}
                    {f && <span className="rounded border px-2 py-0.5 font-semibold" title={`${f.tier}: ${f.rule_id}`}>{f.tier === 'S1' ? 'Needs a person now' : f.tier === 'S2' ? 'Review today' : 'Check when time allows'} · {f.coach_responded ? 'coach replied' : 'no coach reply yet'}</span>}
                  </div>
                  <p className="mt-1">{l.text}</p>
                  {f && <p className="type-meta mt-1">Flagged because the participant {WHY_RULE[f.rule_id] ?? 'said something a person should read'}. <span className="text-text-muted">(rule {f.rule_id}, denials checked)</span></p>}
                </li>
              );
            })}
          </ol>
          <aside className="flex flex-col gap-4">
            <div>
              <h2 className="type-section-title">How the coach did</h2>
              {!lines.some((l) => l.speaker === 'coach') ? (
                <p className="type-meta text-text-muted">Coach scorecards need a coach on the call. Open a fictional example above to see a full call.</p>
              ) : Object.values(analysis.score.counts).every((v) => v.den === 0) ? (
                <p className="type-meta text-text-muted">Not enough coach lines to score yet. Add a few coach lines (choose "Coach said it") to see these measures.</p>
              ) : (
                <ul className="type-meta flex flex-col gap-1">
                  {Object.entries(analysis.score.counts).filter(([, v]) => v.den > 0).map(([k, v]) => {
                    const [name, meaning] = COUNT_LABELS[k] ?? [humanize(k), ''];
                    return <li key={k}><strong>{name}:</strong> {v.num} of {v.den} <span className="text-text-muted">{meaning}</span></li>;
                  })}
                </ul>
              )}
            </div>
            <div>
              <h2 className="type-section-title">Call checklist</h2>
              <ul className="type-meta flex flex-col gap-1">
                {Object.entries(analysis.score.checklist).map(([k, v]) => (
                  <li key={k}>
                    <span aria-hidden="true">{v.value === 'yes' ? '✓' : v.value === 'n/a' ? '–' : '○'}</span>{' '}
                    {CHECK_LABELS[k] ?? humanize(k)}:{' '}
                    <strong>{v.value === 'yes' ? 'seen' : v.value === 'n/a' ? 'not needed' : 'not seen'}</strong>
                    {v.evidence_lines.length ? ` (line ${v.evidence_lines.map((n) => n + 1).join(', ')})` : ''}
                  </li>
                ))}
              </ul>
              <p className="type-meta mt-1 text-text-muted">A coaching aid, not for HR action. Short examples will show most items as "not seen".</p>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
