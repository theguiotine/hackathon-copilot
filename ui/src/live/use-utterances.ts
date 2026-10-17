// Number of lines (utterances) in a call, read from the same repositories as the screens; null while loading.
import { useEffect, useState } from 'react';
import { useRepositories } from '../presentation/app-context';

export const MIN_LINES_FOR_RATIOS = 20;

export function useUtteranceCount(callId: string | undefined): number | null {
  const repos = useRepositories();
  const [n, setN] = useState<number | null>(null);
  useEffect(() => {
    if (!callId) { setN(null); return; }
    void repos.callLine.listAll({ filter: { callId } }).then((r) => setN(r.ok === false ? null : r.data.items.length));
  }, [repos, callId]);
  return n;
}
