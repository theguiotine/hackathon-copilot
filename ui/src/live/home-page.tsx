// Welcome page (hand-written): what this tool is, and three obvious first steps. Judges land here cold.

const STEPS = [
  { href: '/live-analyzer?sample=es-chest', title: 'Try a sample call (Spanish, chest pain)',
    text: 'Watch the tool read a Spanish line, tag what the coach does, and flag the sentence a person must see.' },
  { href: '/call-queue', title: 'See the safety queue',
    text: 'Calls that need a human today, highest severity first, with the quoted sentence and why it was flagged.' },
  { href: '/evaluation', title: 'See how accurate it is',
    text: 'Measured on held-out sessions the tool never trained on, shown honestly with its limits.' },
];

export default function HomePage() {
  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 p-6" data-testid="home-page">
      <header className="flex flex-col gap-2">
        <p className="type-eyebrow uppercase text-text-muted">Coach's Copilot</p>
        <h1 className="type-page-title">Never miss the sentence a person needs to see</h1>
        <p className="type-body max-w-2xl text-text-muted">
          Coaches talk with cancer survivors every day, in English and Spanish. Coach's Copilot reads those
          conversations, tags what the coach is doing, scores the call against motivational-interviewing practice, and
          flags anything a person should follow up on today by quoting the exact sentence. It gives no diagnosis and no
          medical advice.
        </p>
      </header>
      <ol className="grid gap-4 md:grid-cols-3">
        {STEPS.map((s, i) => (
          <li key={s.href}>
            <a href={s.href} className="flex h-full flex-col gap-2 rounded-lg border border-border bg-background p-4 hover:bg-muted focus-visible:outline focus-visible:outline-2">
              <span className="type-meta text-text-muted">Step {i + 1}</span>
              <span className="text-lg font-semibold">{s.title}</span>
              <span className="text-sm text-text-muted">{s.text}</span>
            </a>
          </li>
        ))}
      </ol>
      <p className="type-meta text-text-muted">
        All people and calls shown are invented. Real accuracy is measured locally and is never published in the repo.
      </p>
    </div>
  );
}
