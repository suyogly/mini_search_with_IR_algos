from __future__ import annotations

import numpy as np

from app.rag.preprocessing.normaliser import normalize_query
from app.rag.retrievers.vectorizers import binary_matrix, build_vocabulary, term_frequency_matrix


class KeywordVectorizer:
    def __init__(self) -> None:
        self.vocabulary_: list[str] = []
        self.token_to_index_: dict[str, int] = {}

    def fit(self, tokenized_docs: list[list[str]]) -> "KeywordVectorizer":
        self.vocabulary_, self.token_to_index_ = build_vocabulary(tokenized_docs)
        return self

    def fit_transform(self, tokenized_docs: list[list[str]]) -> np.ndarray:
        self.fit(tokenized_docs)
        counts = term_frequency_matrix(tokenized_docs, self.token_to_index_)
        return binary_matrix(counts)

    def transform_query(self, query_tokens: list[str]) -> np.ndarray:
        query_vector = np.zeros(len(self.vocabulary_), dtype=np.float64)
        for token in query_tokens:
            term_idx = self.token_to_index_.get(token)
            if term_idx is not None:
                query_vector[term_idx] = 1.0
        return query_vector


class KeywordRetriever:
    def __init__(self, documents: list[dict]) -> None:
        self.documents = documents
        tokenized_docs = [doc["tokens"] for doc in documents]
        self.vectorizer = KeywordVectorizer()
        self.document_vectors = self.vectorizer.fit_transform(tokenized_docs)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not query.strip():
            return []

        query_tokens = normalize_query(query)
        if not query_tokens:
            return []

        query_vector = self.vectorizer.transform_query(query_tokens)
        overlap_scores = self.document_vectors @ query_vector

        matched = np.where(overlap_scores > 0)[0]
        ranked_matches = matched[np.argsort(-overlap_scores[matched])]

        results: list[dict] = []
        distinct_query = sorted(set(query_tokens))
        for idx in ranked_matches:
            score = float(overlap_scores[idx])
            doc = self.documents[int(idx)]
            doc_token_set = set(doc["tokens"])
            matched_terms = sorted({t for t in query_tokens if t in doc_token_set})
            item: dict = {
                "doc_id": doc["doc_id"],
                "content": doc["content"],
                "metadata": doc["metadata"],
                "score": score,
                "explanation": {
                    "summary": (
                        f"Overlap score {score:.0f}: count of vocabulary terms shared between "
                        f"the query and this document (binary vectors). "
                        f"{len(matched_terms)} of {len(distinct_query)} distinct query terms match."
                    ),
                    "matched_terms": matched_terms,
                },
            }
            results.append(item)
            if len(results) >= top_k:
                break

        return results


def keyword_search(query: str, data: list[dict], top_k: int = 5) -> list[dict]:
    return KeywordRetriever(data).search(query, top_k=top_k)