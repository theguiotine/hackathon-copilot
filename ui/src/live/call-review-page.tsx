// Call review screen (hand-written, replaces the generated one): read the flagged line, pick one of three plain
// decisions, see a confirmation and the "N of M flags decided" counter, then move to the next call.
// Reads and writes through the same repositories as the rest of the app (in-memory fixtures in demo mode).
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router';
import type { CallLine } from '../domain/entities/callLine';
import type { CoachingCall } from '../domain/entities/coachingCall';
import type { HumanReviewFlag } from '../domain/entities/humanReviewFlag';
import { useRepositories } from '../presentation/app-context';
import { TopNav } from './top-nav';

const CHOICES = [
  { label: 'Escalate to nurse today', decision: 'CONFIRMED', note: 'Escalated to a nurse today.' },
  { label: 'Coach already handled it', decision: 'ANNOTATED_WITH_A_NOTE', note: 'Coach already handled it.' },
  { label: 'Not a real flag', decision: 'DISMISSED_AS_FALSE_ALARMS', note: 'Marked as not a real flag.' },
] as const;

const TIER_CLASS: Record<string, string> = {
  S1: 'border-red-300 bg-red-50 text-red-900',
  S2: 'border-amber-300 bg-amber-50 text-amber-900',
  S3: 'border-sky-300 bg-sky-50 text-sky-900',
};

const choiceFor = (flag: HumanReviewFlag) => CHOICES.find((c) => c.decision === flag.decision);

export default function CallReviewPage() {
  const repos = useRepositories();
  const navigate = useNavigate();
  const { id } = useParams();
  const [calls, setCalls] = useState<CoachingCall[]>([]);
  const [lines, setLines] = useState<CallLine[]>([]);
  const [flags, setFlags] = useState<HumanReviewFlag[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [c, l, f] = await Promise.all([repos.coachingCall.listAll(), repos.callLine.listAll(), repos.humanReviewFlag.listAll()]);
    if (c.ok === false || l.ok === false || f.ok === false) { setError('Could not load calls. Reload the page.'); return; }
    setCalls(c.data.items); setLines(l.data.items); setFlags(f.data.items); setLoaded(true);
  }, [repos]);

  useEffect(() => { void load(); }, [load]);

  const lineById = useMemo(() => new Map(lines.map((l) => [l.id, l])), [lines]);
  const flagsOfCall = useCallback((callId: string) => flags.filter((f) => lineById.get(f.lineId)?.callId === callId), [flags, lineById]);
  const severityRank = (callId: string) => Math.min(9, ...flagsOfCall(callId).map((f) => Number(f.severity.slice(1))));
  // Calls that need a human: those with flags, undecided first, then by highest severity.
  const queue = useMemo(() => calls.filter((c) => flagsOfCall(c.id).length > 0).sort((a, b) => {
    const open = (c: CoachingCall) => (flagsOfCall(c.id).some((f) => !f.decision) ? 0 : 1);
    return open(a) - open(b) || severityRank(a.id) - severityRank(b.id) || a.id.localeCompare(b.id);
  }), [calls, flagsOfCall]); // eslint-disable-line react-hooks/exhaustive-deps

  const call = calls.find((c) => c.id === id) ?? queue[0] ?? calls[0];
  const callLines = lines.filter((l) => l.callId === call?.id).sort((a, b) => a.lineNumber - b.lineNumber);
  const callFlags = call ? flagsOfCall(call.id).sort((a, b) => (lineById.get(a.lineId)?.lineNumber ?? 0) - (lineById.get(b.lineId)?.lineNumber ?? 0)) : [];
  const decided = callFlags.filter((f) => f.decision).length;
  const nextCall = queue.find((c) => c.id !== call?.id && flagsOfCall(c.id).some((f) => !f.decision)) ?? queue.find((c) => c.id !== call?.id);

  async function decide(flag: HumanReviewFlag, choice: (typeof CHOICES)[number]) {
    setError(null);
    const res = await repos.humanReviewFlag.update(flag.id, { decision: choice.decision, decisionNote: choice.note, decidedAt: new Date().toISOString() });
    if (res.ok === false) { setError('Could not save that decision. Try again.'); return; }
    const n = lineById.get(flag.lineId)?.lineNumber;
    setMessage(`Saved: "${choice.label}" for line ${n}.`);
    await load();
  }

  if (error && !loaded) return <p role="alert" className="p-6">{error}</p>;
  if (!loaded) return <p className="p-6 text-text-muted">Loading…</p>;
  if (!call) return <div className="p-6"><TopNav current="/call-queue" /><p className="mt-4">There are no calls yet.</p></div>;

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-4 p-6" data-testid="call-review-page">
      <TopNav current="/call-queue" />
      <p className="rounded border border-border bg-muted p-3 text-sm"><strong>Step 1:</strong> read the flagged line. <strong>Step 2:</strong> pick a decision.</p>
      <header>
        <h1 className="type-page-title">{call.title}</h1>
        <p className="type-meta text-text-muted">{call.language === 'ES' ? 'Spanish' : 'English'} · {call.duration} min</p>
        <p className="mt-1 font-medium" aria-live="polite" data-testid="decided-counter">
          {callFlags.length === 0 ? 'No flags on this call.' : `${decided} of ${callFlags.length} flags decided`}
        </p>
      </header>

      {message && <p role="status" className="rounded border border-green-300 bg-green-50 p-3 text-green-900">{message}</p>}
      {error && <p role="alert" className="rounded border border-red-300 bg-red-50 p-3 text-red-900">{error}</p>}

      <ol className="flex flex-col gap-3">
        {callLines.map((l) => {
          const lineFlags = callFlags.filter((f) => f.lineId === l.id);
          return (
            <li key={l.id} className={`rounded border p-3 ${lineFlags.length ? TIER_CLASS[lineFlags[0].severity] : 'border-border'}`}>
              <p className="type-meta"><strong>{l.lineNumber}. {l.speaker === 'COACH' ? 'Coach' : 'Participant'}</strong></p>
              <p className="mt-1">{l.text}</p>
              {lineFlags.map((f) => {
                const chosen = choiceFor(f);
                return (
                  <div key={f.id} className="mt-3 rounded border border-border bg-background p-3 text-foreground">
                    <p className="text-sm"><strong>{f.severity} needs a human.</strong> {f.reason}</p>
                    <p className="mt-2 text-sm font-medium">{chosen ? `Decision: ${chosen.label}` : 'Waiting for your decision:'}</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {CHOICES.map((c) => (
                        <button key={c.decision} type="button" onClick={() => void decide(f, c)} aria-pressed={chosen?.decision === c.decision}
                          className={`rounded-md border px-3 py-2 text-sm font-medium ${chosen?.decision === c.decision ? 'border-primary bg-primary text-primary-foreground' : 'border-border hover:bg-muted'}`}>
                          {c.label}
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </li>
          );
        })}
      </ol>

      <div className="flex flex-wrap gap-2">
        {nextCall
          ? <button type="button" onClick={() => { setMessage(null); navigate(`/call-review/${nextCall.id}`); }} className="rounded-md bg-primary px-4 py-2 text-primary-foreground">Next call</button>
          : <a href="/call-queue" className="rounded-md bg-primary px-4 py-2 text-primary-foreground">Back to the safety queue</a>}
        <a href="/call-queue" className="rounded-md border border-border px-4 py-2 hover:bg-muted">All calls</a>
      </div>
    </div>
  );
}
