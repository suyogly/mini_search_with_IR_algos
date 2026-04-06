const KEY = "mini-search-history-v1";

export type HistoryEntry = {
  query: string;
  at: number;
};

export function loadHistory(): HistoryEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as HistoryEntry[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveHistory(entries: HistoryEntry[]): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(KEY, JSON.stringify(entries.slice(0, 50)));
}

export function prependQuery(query: string): HistoryEntry[] {
  const q = query.trim();
  if (!q) return loadHistory();
  const prev = loadHistory().filter((e) => e.query.toLowerCase() !== q.toLowerCase());
  const next: HistoryEntry[] = [{ query: q, at: Date.now() }, ...prev].slice(0, 50);
  saveHistory(next);
  return next;
}
