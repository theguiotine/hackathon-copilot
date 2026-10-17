// Small always-visible links shared by the hand-written pages, so nobody lands on a screen with no next step.
const LINKS = [
  { href: '/', label: 'Home' },
  { href: '/live-analyzer', label: 'Live analyzer' },
  { href: '/call-queue', label: 'Safety queue' },
  { href: '/evaluation', label: 'Accuracy' },
];

export function TopNav({ current }: { current: string }) {
  return (
    <nav aria-label="Quick links" className="flex flex-wrap gap-2 text-sm">
      {LINKS.map((l) => (
        <a key={l.href} href={l.href} aria-current={l.href === current ? 'page' : undefined}
          className={`rounded-md border px-3 py-1 ${l.href === current ? 'border-primary bg-primary text-primary-foreground' : 'border-border hover:bg-muted'}`}>
          {l.label}
        </a>
      ))}
    </nav>
  );
}
