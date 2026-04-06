from __future__ import annotations

import numpy as np

from app.rag.preprocessing.normaliser import normalize_query
from app.rag.retrievers.vectorizers import build_vocabulary, term_frequency_matrix


class BM25Vectorizer:
	def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
		self.k1 = k1
		self.b = b
		self.vocabulary_: list[str] = []
		self.token_to_index_: dict[str, int] = {}
		self.term_frequencies_: np.ndarray | None = None
		self.idf_: np.ndarray | None = None
		self.doc_lengths_: np.ndarray | None = None
		self.avg_doc_length_: float = 1.0

	def fit(self, tokenized_docs: list[list[str]]) -> "BM25Vectorizer":
		self.vocabulary_, self.token_to_index_ = build_vocabulary(tokenized_docs)
		self.term_frequencies_ = term_frequency_matrix(tokenized_docs, self.token_to_index_)

		total_docs = self.term_frequencies_.shape[0]
		document_frequency = np.count_nonzero(self.term_frequencies_ > 0, axis=0)
		self.idf_ = np.log(
			1.0 + (total_docs - document_frequency + 0.5) / (document_frequency + 0.5)
		)

		self.doc_lengths_ = self.term_frequencies_.sum(axis=1)
		mean_length = float(np.mean(self.doc_lengths_))
		self.avg_doc_length_ = mean_length if mean_length > 0 else 1.0
		return self

	def score_query(self, query_tokens: list[str]) -> np.ndarray:
		if self.term_frequencies_ is None or self.idf_ is None or self.doc_lengths_ is None:
			raise ValueError("BM25Vectorizer must be fit before scoring.")

		query_counts = np.zeros(len(self.vocabulary_), dtype=np.float64)
		for token in query_tokens:
			term_idx = self.token_to_index_.get(token)
			if term_idx is not None:
				query_counts[term_idx] += 1.0

		scores = np.zeros(self.term_frequencies_.shape[0], dtype=np.float64)
		term_indices = np.nonzero(query_counts)[0]
		length_norm = self.k1 * (
			1.0 - self.b + self.b * (self.doc_lengths_ / self.avg_doc_length_)
		)

		for term_idx in term_indices:
			term_freq = self.term_frequencies_[:, term_idx]
			numerator = term_freq * (self.k1 + 1.0)
			denominator = term_freq + length_norm
			contribution = self.idf_[term_idx] * np.divide(
				numerator,
				denominator,
				out=np.zeros_like(term_freq),
				where=denominator != 0,
			)

			# Repeated query terms carry more weight.
			scores += contribution * query_counts[term_idx]

		return scores

	def term_contributions_for_document(
		self, doc_idx: int, query_tokens: list[str]
	) -> list[tuple[str, float]]:
		if self.term_frequencies_ is None or self.idf_ is None or self.doc_lengths_ is None:
			raise ValueError("BM25Vectorizer must be fit before scoring.")

		query_counts = np.zeros(len(self.vocabulary_), dtype=np.float64)
		for token in query_tokens:
			term_idx = self.token_to_index_.get(token)
			if term_idx is not None:
				query_counts[term_idx] += 1.0

		length_norm = self.k1 * (
			1.0 - self.b + self.b * (self.doc_lengths_[doc_idx] / self.avg_doc_length_)
		)
		out: list[tuple[str, float]] = []
		for term_idx in np.nonzero(query_counts)[0]:
			tf = float(self.term_frequencies_[doc_idx, term_idx])
			numerator = tf * (self.k1 + 1.0)
			denominator = tf + length_norm
			if denominator == 0:
				continue
			contrib = float(self.idf_[term_idx] * (numerator / denominator) * query_counts[term_idx])
			if contrib > 0:
				term = self.vocabulary_[int(term_idx)]
				out.append((term, contrib))
		out.sort(key=lambda x: -x[1])
		return out


class BM25Retriever:
	def __init__(self, documents: list[dict], k1: float = 1.5, b: float = 0.75) -> None:
		self.documents = documents
		tokenized_docs = [doc["tokens"] for doc in documents]
		self.vectorizer = BM25Vectorizer(k1=k1, b=b).fit(tokenized_docs)

	def search(self, query: str, top_k: int = 5) -> list[dict]:
		if not query.strip():
			return []

		query_tokens = normalize_query(query)
		if not query_tokens:
			return []

		scores = self.vectorizer.score_query(query_tokens)
		ranked_indices = np.argsort(-scores)

		results: list[dict] = []
		for idx in ranked_indices:
			score = float(scores[idx])
			if score <= 0:
				continue

			doc = self.documents[int(idx)]
			term_parts = self.vectorizer.term_contributions_for_document(int(idx), query_tokens)
			top_terms = [t for t, _ in term_parts[:8]]
			matched_terms = sorted({t for t, _ in term_parts})
			explain = {
				"summary": (
					f"BM25 score {score:.4f} (Okapi BM25 with k1={self.vectorizer.k1}, b={self.vectorizer.b}): "
					f"sum of per-term IDF × length-normalized term frequency. "
					f"Largest term contributions: {', '.join(top_terms) if top_terms else '—'}."
				),
				"matched_terms": matched_terms,
				"term_contributions": [{"term": t, "bm25_partial": c} for t, c in term_parts[:12]],
			}
			results.append(
				{
					"doc_id": doc["doc_id"],
					"content": doc["content"],
					"metadata": doc["metadata"],
					"score": score,
					"explanation": explain,
				}
			)
			if len(results) >= top_k:
				break

		return results


def bm25_search(query: str, data: list[dict], top_k: int = 5) -> list[dict]:
	return BM25Retriever(data).search(query, top_k=top_k)
