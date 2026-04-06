"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import type { HistoryEntry } from "@/lib/search-history";

type Props = {
  entries: HistoryEntry[];
  onSelectQuery: (q: string) => void;
};

export function HistoryPanel({ entries, onSelectQuery }: Props) {
  const [filter, setFilter] = useState("");

  const filtered = useMemo(() => {
    const f = filter.trim().toLowerCase();
    if (!f) return entries;
    return entries.filter((e) => e.query.toLowerCase().includes(f));
  }, [entries, filter]);

  return (
    <div className="flex h-full flex-col gap-4">
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Actions
        </p>
        <Link
          href="/upload"
          className="mt-2 block text-sm underline underline-offset-4 hover:text-muted-foreground"
        >
          Upload snippets
        </Link>
      </div>
      <Separator />
      <div className="space-y-2">
        <Label htmlFor="hist-filter" className="text-xs uppercase tracking-wide">
          Search history
        </Label>
        <Input
          id="hist-filter"
          placeholder="Filter past queries…"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="h-8 text-xs"
        />
      </div>
      <ScrollArea className="h-[min(60vh,420px)] pr-3">
        <ul className="space-y-1">
          {filtered.length === 0 ? (
            <li className="text-xs text-muted-foreground">No entries.</li>
          ) : (
            filtered.map((e) => (
              <li key={`${e.at}-${e.query}`}>
                <button
                  type="button"
                  onClick={() => onSelectQuery(e.query)}
                  className="w-full rounded-sm px-2 py-1.5 text-left text-sm text-foreground hover:underline"
                >
                  <span className="line-clamp-2">{e.query}</span>
                  <span className="block text-[10px] text-muted-foreground">
                    {new Date(e.at).toLocaleString()}
                  </span>
                </button>
              </li>
            ))
          )}
        </ul>
      </ScrollArea>
    </div>
  );
}
