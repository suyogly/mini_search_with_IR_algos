"use client";

import { Menu, Search } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { HistoryPanel } from "@/components/history-panel";
import { SearchResults } from "@/components/search-results";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { searchPost } from "@/lib/api";
import { loadHistory, prependQuery, type HistoryEntry } from "@/lib/search-history";
import type { SearchResponse } from "@/lib/search-types";

export default function HomePage() {
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [data, setData] = useState<{
    keyword: SearchResponse | null;
    tfidf: SearchResponse | null;
    bm25: SearchResponse | null;
  }>({ keyword: null, tfidf: null, bm25: null });
  const [sheetOpen, setSheetOpen] = useState(false);

  useEffect(() => {
    setHistory(loadHistory());
  }, []);

  const runSearch = useCallback(async (raw: string) => {
    const query = raw.trim();
    if (!query) return;
    setLoading(true);
    setErr(null);
    try {
      const [keyword, tfidf, bm25] = await Promise.all([
        searchPost("keyword", query),
        searchPost("tfidf", query),
        searchPost("bm25", query),
      ]);
      setData({ keyword, tfidf, bm25 });
      setHistory(prependQuery(query));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Search failed.");
    } finally {
      setLoading(false);
    }
  }, []);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    void runSearch(q);
  };

  const pickHistory = useCallback(
    (text: string) => {
      setQ(text);
      void runSearch(text);
      setSheetOpen(false);
    },
    [runSearch]
  );

  return (
    <div className="flex min-h-screen">
      <main className="flex min-w-0 flex-1 flex-col items-center px-4 pb-24 pt-[min(20vh,8rem)]">
        <div className="w-full max-w-xl">
          <h1 className="text-center text-2xl font-semibold tracking-tight">
            Search
          </h1>
          <p className="mt-2 text-center text-sm text-muted-foreground">
            Keyword overlap, TF‑IDF cosine, and BM25 over indexed snippets.
          </p>

          <form onSubmit={onSubmit} className="mt-10 flex w-full gap-2">
            <Input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Type a query…"
              className="h-11"
              disabled={loading}
              aria-label="Search query"
            />
            <Button type="submit" disabled={loading || !q.trim()} size="icon" className="h-11 w-11 shrink-0" aria-label="Run search">
              <Search className="h-4 w-4" />
            </Button>
          </form>

          {err ? (
            <div
              className="mt-4 rounded-md border border-border bg-muted/50 px-3 py-3 text-left text-sm text-foreground"
              role="alert"
            >
              <p className="font-medium">Search unavailable</p>
              <p className="mt-2 whitespace-pre-line leading-relaxed">{err}</p>
            </div>
          ) : null}

          {data.keyword || data.tfidf || data.bm25 ? (
            <Tabs defaultValue="keyword" className="mt-12 w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="keyword">Keyword</TabsTrigger>
                <TabsTrigger value="tfidf">TF‑IDF</TabsTrigger>
                <TabsTrigger value="bm25">BM25</TabsTrigger>
              </TabsList>
              <TabsContent value="keyword">
                <SearchResults
                  hits={data.keyword?.results ?? []}
                  algo="keyword"
                />
              </TabsContent>
              <TabsContent value="tfidf">
                <SearchResults hits={data.tfidf?.results ?? []} algo="tfidf" />
              </TabsContent>
              <TabsContent value="bm25">
                <SearchResults hits={data.bm25?.results ?? []} algo="bm25" />
              </TabsContent>
            </Tabs>
          ) : (
            <p className="mt-12 text-center text-sm text-muted-foreground">
              Results appear here after you search.
            </p>
          )}
        </div>
      </main>

      <aside className="hidden w-72 shrink-0 border-l border-border lg:block">
        <div className="sticky top-0 h-screen overflow-hidden p-6">
          <p className="mb-4 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Panel
          </p>
          <HistoryPanel entries={history} onSelectQuery={pickHistory} />
        </div>
      </aside>

      <div className="fixed bottom-4 right-4 z-40 lg:hidden">
        <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
          <SheetTrigger asChild>
            <Button size="icon" variant="outline" className="h-11 w-11 border-border bg-background" aria-label="Open panel">
              <Menu className="h-4 w-4" />
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="w-[min(100vw,20rem)]">
            <SheetHeader>
              <SheetTitle>Panel</SheetTitle>
            </SheetHeader>
            <div className="mt-6">
              <HistoryPanel entries={history} onSelectQuery={pickHistory} />
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </div>
  );
}
