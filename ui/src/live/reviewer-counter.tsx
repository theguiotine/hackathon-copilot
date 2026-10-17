// Reviewer counter for the top of the Safety queue: flags to review, decided, and the share marked "not a real flag".
// Read from the same repositories as the screens, so it updates after decisions.
import { useEffect, useState } from 'react';
import { useRepositories } from '../presentation/app-context';

export function ReviewerCounter() {
  const repos = useRepositories();
  const [c, setC] = useState<{ total: number; decided: number; notReal: number } | null>(null);
  useEffect(() => {
    void repos.humanReviewFlag.listAll().then((r) => {
      if (r.ok === false) return;
      const items = r.data.items;
      const decided = items.filter((f) => f.decision);
      setC({ total: items.length, decided: decided.length, notReal: decided.filter((f) => f.decision === 'DISMISSED_AS_FALSE_ALARMS').length });
    });
  }, [repos]);
  if (!c) return null;
  const share = c.decided === 0 ? 'none decided yet' : `${Math.round((100 * c.notReal) / c.decided)}% (${c.notReal} of ${c.decided} decided)`;
  return (
    <p className="text-sm" data-testid="reviewer-counter">
      <strong>Today's review:</strong> {c.total} flags to review · {c.decided} decided · marked “not a real flag”: {share}
    </p>
  );
}
