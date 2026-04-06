export type TermContribution = {
  term: string;
  q_times_d?: number;
  bm25_partial?: number;
};

export type SearchHit = {
  doc_id: string;
  content: string;
  metadata: Record<string, unknown>;
  score: number;
  explanation: {
    summary: string;
    matched_terms: string[];
    term_contributions?: TermContribution[];
  };
};

export type SearchResponse = {
  algorithm: string;
  query: string;
  count: number;
  results: SearchHit[];
};
