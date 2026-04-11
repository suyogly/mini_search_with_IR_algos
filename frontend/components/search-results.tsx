import type { SearchHit } from "@/lib/search-types";

function formatScore(hit: SearchHit, algo: "keyword" | "tfidf" | "bm25") {
  const s = hit.score;
  if (algo === "keyword") return s.toFixed(0);
  if (algo === "tfidf") return s.toFixed(4);
  return s.toFixed(4);
}

export function SearchResults({
  hits,
  algo,
}: {
  hits: SearchHit[];
  algo: "keyword" | "tfidf" | "bm25";
}) {
  if (hits.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No results for this method.</p>
    );
  }

  return (
    <ul className="space-y-4">
      {hits.map((hit) => (
        <li
          key={hit.doc_id}
          className="border border-border p-4 text-sm leading-relaxed"
        >
          <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-border pb-2">
            <span className="font-mono text-xs text-muted-foreground">
              {hit.doc_id}
            </span>
            <span className="font-mono text-xs">
              score: {formatScore(hit, algo)}
            </span>
          </div>
          <p className="mt-3 whitespace-pre-wrap text-foreground">{hit.content}</p>
          <div className="mt-3 space-y-2 border-t border-border pt-3 text-xs text-muted-foreground">
            <p>{hit.explanation.summary}</p>
            {hit.explanation.matched_terms?.length ? (
              <p>
                <span className="text-foreground">Matched terms: </span>
                {hit.explanation.matched_terms.join(", ")}
              </p>
            ) : null}
            {hit.explanation.term_contributions?.length ? (
              <div>
                <p className="mb-1 text-foreground">Term breakdown</p>
                <ul className="font-mono text-[11px] leading-5">
                  {hit.explanation.term_contributions.map((t) => (
                    <li key={t.term}>
                      {t.term}
                      {typeof t.q_times_d === "number"
                        ? ` — q·d = ${t.q_times_d.toExponential(3)}`
                        : null}
                      {typeof t.bm25_partial === "number"
                        ? ` — ΔBM25 = ${t.bm25_partial.toFixed(4)}`
                        : null}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        </li>
      ))}
    </ul>
  );
}