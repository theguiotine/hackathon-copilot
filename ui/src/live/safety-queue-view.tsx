// Safety queue as cards: one per call, grouped by what to do, oldest unhandled first.
// Labels and layout only: every number comes from the same repositories; no rule or score is changed here.
import { useMemo, useState } from 'react';
import { Link } from 'react-router';
import { useSafety } from './safety-net';
import type { CallQueueScreenViewModel } from '../application/view-models/call-queue.vm';

type Tier = 'S1' | 'S2' | 'S3';
const WORD: Record<Tier, string> = { S1: 'Needs a person now', S2: 'Review today', S3: 'Check when time allows' };
const DETAIL: Record<Tier, string> = {
  S1: 'S1: highest severity (for example chest pain, thoughts of self-harm)',
  S2: 'S2: medium severity (for example fever, bleeding, new lump)',
  S3: 'S3: lower severity (for example sounding overwhelmed or alone)',
};
const BAR: Record<Tier, string> = { S1: 'border-l-red-600 bg-red-50/70', S2: 'border-l-amber-500 bg-amber-50/70', S3: 'border-l-sky-500 bg-sky-50/70' };
const CHIP: Record<Tier, string> = { S1: 'border-red-300 bg-red-100 text-red-900', S2: 'border-amber-300 bg-amber-100 text-amber-900', S3: 'border-sky-300 bg-sky-100 text-sky-900' };
const RANK: Record<string, number> = { S1: 1, S2: 2, S3: 3 };
const STATUS: Record<string, string> = {
  COMPLETED_COACHING_CALLS: 'Completed',
  COACHES_REVIEW_CALLS_FIRST: 'Waiting for coach review',
  THEN_MANAGERS: 'Needs manager follow-up',
};
const NOW = Date.now();
const DAY = 86_400_000;

const fmtDate = (iso: string) => new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
const plural = (n: number, w: string) => `${n} ${w}${n === 1 ? '' : 's'}`;
/** "The participant mentions chest pain. Rule F-CHEST, ..." -> { why: "mentions chest pain", rule: "F-CHEST", replied } */
function parseReason(reason: string) {
  const first = reason.split(/\.\s+Rule\b|\.\s/)[0] ?? reason;
  return {
    why: first.replace(/^The participant\s+/i, '').replace(/\.$/, ''),
    rule: /Rule\s+(F-[A-Z0-9-]+)/.exec(reason)?.[1] ?? '',
    replied: /coach reply acknowledged/i.test(reason),
  };
}

type Card = {
  id: string; participant: string; coach: string; status: string; completedAt: string;
  tier: Tier | null; flags: number; quote: string; why: string; rule: string; replied: boolean;
  waitDays: number; oldest: number; search: string;
};
type Filter = 'all' | 'S1' | 'S2' | 'none';

function CardView({ c, href }: { c: Card; href: string }) {
  const t = c.tier;
  // Tinted cards are always light, so their text is fixed dark (4.5:1 or better) in both themes.
  const muted = t ? 'text-slate-700' : 'text-text-muted';
  const neutral = t ? 'border-border bg-white text-slate-900' : 'border-border bg-background text-foreground';
  return (
    <li className={`relative rounded-card border border-border border-l-4 p-3 ${t ? `${BAR[t]} text-slate-900` : 'border-l-border bg-card'}`}>
      <p className={`type-row-title ${t ? 'text-slate-900' : 'text-foreground'}`}>
        <Link to={href} className="after:absolute after:inset-0 focus-visible:outline-none focus-visible:after:ring-2 focus-visible:after:ring-ring focus-visible:after:rounded-card">
          {c.participant}
        </Link>
        <span className={`font-normal ${muted}`}> · coach {c.coach}</span>
      </p>
      {t && c.quote ? (
        <p className="mt-1 line-clamp-2 text-base italic text-slate-900" title={c.quote}>“{c.quote}”</p>
      ) : null}
      {t ? (
        <p className="mt-1 text-sm text-slate-700">
          Flagged because: {c.why}.{' '}
          <details className="relative z-10 inline">
            <summary className="inline-block min-h-8 cursor-pointer px-1 py-1.5 underline">details</summary>
            <span className="block text-xs">Rule {c.rule || 'n/a'} · {DETAIL[t]}</span>
          </details>
        </p>
      ) : null}
      <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs">
        <span className={`rounded border px-2 py-0.5 font-semibold ${t ? CHIP[t] : 'border-border bg-background text-text-muted'}`} title={t ? DETAIL[t] : undefined}>
          {t ? WORD[t] : 'No action'}
        </span>
        {t ? <span className={`rounded border px-2 py-0.5 ${neutral}`}>{plural(c.flags, 'flag')}</span> : null}
        {t ? (
          c.replied
            ? <span className="rounded border border-green-300 bg-green-100 px-2 py-0.5 text-green-900">Coach replied</span>
            : <span className="rounded border border-red-300 bg-red-100 px-2 py-0.5 font-semibold text-red-900">No coach reply yet</span>
        ) : null}
        {t && !c.replied && c.waitDays > 0 ? <span className={`rounded border px-2 py-0.5 ${neutral}`}>Waiting {plural(c.waitDays, 'day')}</span> : null}
        <span className={`rounded border px-2 py-0.5 ${neutral}`}>{c.status}</span>
        <span className={muted}>{fmtDate(c.completedAt)}</span>
      </div>
    </li>
  );
}

function Section({ title, hint, cards, hrefFor }: { title: string; hint: string; cards: Card[]; hrefFor: (id: string) => string }) {
  if (cards.length === 0) return null;
  return (
    <section aria-label={title}>
      <h2 className="sticky top-0 z-10 -mx-1 bg-background/95 px-1 py-2 text-sm font-semibold backdrop-blur">
        {title} <span className="font-normal text-text-muted">· {cards.length} · {hint}</span>
      </h2>
      <ul className="flex flex-col gap-3">{cards.map((c) => <CardView key={c.id} c={c} href={hrefFor(c.id)} />)}</ul>
    </section>
  );
}

export function SafetyQueueView(props: CallQueueScreenViewModel) {
  const { CoachingCall, CallLine, HumanReviewFlag, Coach, Participant, href } = props;
  const blind = useSafety()?.blind ?? null;
  const [filter, setFilter] = useState<Filter>('all');
  const [q, setQ] = useState('');

  const { cards, totals } = useMemo(() => {
    const coachName = Object.fromEntries(Coach.map((c) => [c.id, c.name]));
    const partName = Object.fromEntries(Participant.map((p) => [p.id, p.name]));
    const lineById = Object.fromEntries(CallLine.map((l) => [l.id, l]));
    const cards: Card[] = CoachingCall.map((c) => {
      const flags = HumanReviewFlag.filter((f) => lineById[f.lineId]?.callId === c.id);
      const sorted = [...flags].sort((a, b) => (RANK[a.severity] ?? 9) - (RANK[b.severity] ?? 9));
      const top = sorted[0];
      const parsed = top ? parseReason(top.reason) : null;
      const open = flags.filter((f) => !f.decision && !parseReason(f.reason).replied);
      const oldest = Math.min(...(open.length ? open : flags).map((f) => Date.parse(f.createdAt)), Infinity);
      return {
        id: c.id, participant: partName[c.participantId] ?? '—', coach: coachName[c.coachId] ?? '—',
        status: STATUS[c.status] ?? c.status, completedAt: c.completedAt,
        tier: (top?.severity as Tier) ?? null, flags: flags.length,
        quote: top ? (lineById[top.lineId]?.text ?? '') : '', why: parsed?.why ?? '', rule: parsed?.rule ?? '',
        replied: flags.length > 0 && open.length === 0,
        waitDays: open.length && Number.isFinite(oldest) ? Math.max(0, Math.floor((NOW - oldest) / DAY)) : 0,
        oldest: Number.isFinite(oldest) ? oldest : Infinity,
        search: `${partName[c.participantId] ?? ''} ${c.title} ${coachName[c.coachId] ?? ''}`.toLowerCase(),
      };
    });
    const decided = HumanReviewFlag.filter((f) => f.decision).length;
    return { cards, totals: { flags: HumanReviewFlag.length, decided } };
  }, [CoachingCall, CallLine, HumanReviewFlag, Coach, Participant]);

  const shown = cards.filter((c) => (!q || c.search.includes(q.toLowerCase())) &&
    (filter === 'all' || (filter === 'none' ? !c.tier : c.tier === filter)));
  const byAge = (a: Card, b: Card) => a.oldest - b.oldest;
  const now = shown.filter((c) => c.tier === 'S1').sort(byAge);
  const today = shown.filter((c) => c.tier === 'S2').sort(byAge);
  const later = shown.filter((c) => c.tier === 'S3').sort(byAge);
  const none = shown.filter((c) => !c.tier);
  const needNow = cards.filter((c) => c.tier === 'S1').length;
  const flaggedCalls = cards.filter((c) => c.tier).length;
  const hrefFor = (id: string) => href('call-review', { id });
  const pct = totals.flags ? Math.round((100 * totals.decided) / totals.flags) : 0;
  const chips: [Filter, string][] = [['all', 'All'], ['S1', 'Needs a person now'], ['S2', 'Review today'], ['none', 'No flags']];

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 px-4 pb-10 pt-4">
      <header className="flex flex-col gap-2">
        <h1 className="type-page-title text-foreground">Safety queue</h1>
        <p className="text-2xl font-semibold" data-testid="queue-headline">
          {needNow > 0 ? `${plural(needNow, 'call')} ${needNow === 1 ? 'needs' : 'need'} a person now` : 'Nothing flagged right now. This is not a medical clearance.'}
        </p>
        <p className="text-sm text-text-muted">{plural(flaggedCalls, 'call')} flagged · {plural(totals.flags, 'flag')} · {totals.decided} decided</p>
        <div role="progressbar" aria-valuemin={0} aria-valuemax={totals.flags} aria-valuenow={totals.decided}
          aria-label={`${totals.decided} of ${totals.flags} flags decided`} className="h-1.5 w-full overflow-hidden rounded bg-border">
          <div className="h-full bg-foreground" style={{ width: `${pct}%` }} />
        </div>
        <p className="text-xs text-text-muted">{totals.decided} of {totals.flags} flags decided</p>
        {blind ? (
          <Link to="/evaluation" className="w-fit rounded-full border border-border px-3 py-1 text-xs text-text-muted underline-offset-2 hover:underline">
            Blind test: caught {blind.correct_catches} of {blind.correct_catches + blind.misses} ({Math.round(blind.recall * 100)}%) · See the misses
          </Link>
        ) : null}
      </header>

      <div className="flex flex-col gap-2">
        <div role="group" aria-label="Filter calls" className="flex flex-wrap gap-2">
          {chips.map(([k, label]) => (
            <button key={k} type="button" aria-pressed={filter === k} onClick={() => setFilter(k)}
              className={`min-h-11 rounded-full border px-4 text-sm focus-visible:ring-2 focus-visible:ring-ring ${filter === k ? 'border-foreground bg-foreground text-background' : 'border-border-strong bg-background'}`}>
              {label}
            </button>
          ))}
        </div>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search by participant or coach" aria-label="Search calls"
          className="min-h-11 w-full rounded-control border border-border-strong bg-background px-3 text-base focus-visible:ring-2 focus-visible:ring-ring" />
      </div>

      {shown.length === 0 ? (
        <div className="rounded-card border border-border bg-card p-4 text-sm">
          {cards.length === 0 ? 'No calls yet.' : 'No calls match. '}
          {cards.length > 0 ? <button type="button" className="underline" onClick={() => { setQ(''); setFilter('all'); }}>Clear filters</button> : null}
        </div>
      ) : (
        <>
          <Section title="Needs a person now" hint="open a call, then decide on the flagged line" cards={now} hrefFor={hrefFor} />
          <Section title="Review today" hint="oldest waiting first" cards={today} hrefFor={hrefFor} />
          <Section title="Check when time allows" hint="lower severity" cards={later} hrefFor={hrefFor} />
          {none.length > 0 ? (
            <details className="rounded-card border border-border bg-card" open={filter === 'none'}>
              <summary className="min-h-11 cursor-pointer px-3 py-3 text-sm font-semibold">{plural(none.length, 'call')} with no flags</summary>
              <ul className="flex flex-col gap-3 p-3 pt-0">{none.map((c) => <CardView key={c.id} c={c} href={hrefFor(c.id)} />)}</ul>
            </details>
          ) : null}
        </>
      )}
    </div>
  );
}
