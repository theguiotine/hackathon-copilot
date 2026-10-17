import { Link } from 'react-router';
// Welcome page (hand-written): what this tool is, and three obvious first steps. Judges land here cold.

const STEPS = [
  { href: '/live-analyzer?sample=es-chest', title: 'Try a sample call (Spanish, chest pain)',
    text: 'Watch the tool read a Spanish line, tag what the coach does, and flag the sentence a person must see.' },
  { href: '/call-queue', title: 'See the safety queue',
    text: 'Calls that need a human today, highest severity first, with the quoted sentence and why it was flagged.' },
  { href: '/evaluation', title: 'See what it catches and misses',
    text: 'A caught-versus-missed check on invented cases, with the misses shown and the limits stated.' },
];

export default function HomePage() {
  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 p-6" data-testid="home-page">
      <header className="flex flex-col gap-2">
        <p className="type-eyebrow uppercase text-text-muted">Hear Me Out</p>
        <h1 className="type-page-title">Never miss the sentence a person needs to see</h1>
        <p className="type-body font-medium">A second listener for health-coaching calls (eMerge Challenge 5, Coach's Copilot)</p>
        <p className="type-body max-w-2xl text-text-muted">
          Coaches talk with cancer survivors every day, in English and Spanish. Hear Me Out reads those
          conversations, tags what the coach is doing, scores the call against motivational-interviewing practice, and
          flags anything a person should follow up on today by quoting the exact sentence. It gives no diagnosis and no
          medical advice.
        </p>
      </header>
      <ol className="grid gap-4 md:grid-cols-3">
        {STEPS.map((s, i) => (
          <li key={s.href}>
            <Link to={s.href} className="flex h-full flex-col gap-2 rounded-lg border border-border bg-background p-4 hover:bg-muted focus-visible:outline focus-visible:outline-2">
              <span className="type-meta text-text-muted">Step {i + 1}</span>
              <span className="text-lg font-semibold">{s.title}</span>
              <span className="text-sm text-text-muted">{s.text}</span>
            </Link>
          </li>
        ))}
      </ol>
      <section aria-labelledby="real-run" className="rounded-lg border border-border p-4" data-testid="whats-next">
        <h2 id="real-run" className="text-lg font-semibold">What it takes to run this for real</h2>
        <ol className="mt-2 flex list-decimal flex-col gap-1 pl-5 text-sm">
          <li><strong>Delivery:</strong> a flag reaches a person through the program's own consented, secure channel. Today it shows a queue and sends nothing.</li>
          <li><strong>Validation:</strong> a clinician reviews the safety tiers and rules before any real use. Today they are our own design.</li>
          <li><strong>Pilot:</strong> four weeks on real, consented calls to measure how many missed flags a human catches.</li>
        </ol>
      </section>
      <p className="type-meta text-text-muted">
        All people and calls shown are invented. Real accuracy is measured locally and is never published in the repo.
      </p>
    </div>
  );
}
