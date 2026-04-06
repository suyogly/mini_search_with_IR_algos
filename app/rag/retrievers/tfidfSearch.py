from __future__ import annotations

import numpy as np

from app.rag.preprocessing.normaliser import normalize_query
from app.rag.retrievers.vectorizers import build_vocabulary, term_frequency_matrix


class TfidfVectorizer:
	def __init__(self) -> None:
		self.vocabulary_: list[str] = []
		self.token_to_index_: dict[str, int] = {}
		self.idf_: np.ndarray | None = None

	def fit(self, tokenized_docs: list[list[str]]) -> "TfidfVectorizer":
		self.vocabulary_, self.token_to_index_ = build_vocabulary(tokenized_docs)
		term_counts = term_frequency_matrix(tokenized_docs, self.token_to_index_)

		total_docs = term_counts.shape[0]
		document_frequency = np.count_nonzero(term_counts > 0, axis=0)
		self.idf_ = np.log((1.0 + total_docs) / (1.0 + document_frequency)) + 1.0
		return self

	def fit_transform(self, tokenized_docs: list[list[str]]) -> np.ndarray:
		self.fit(tokenized_docs)
		term_counts = term_frequency_matrix(tokenized_docs, self.token_to_index_)
		return self._to_tfidf(term_counts)

	def transform_query(self, query_tokens: list[str]) -> np.ndarray:
		query_counts = np.zeros((1, len(self.vocabulary_)), dtype=np.float64)
		for token in query_tokens:
			term_idx = self.token_to_index_.get(token)
			if term_idx is not None:
				query_counts[0, term_idx] += 1.0
		return self._to_tfidf(query_counts)[0]

	def _to_tfidf(self, term_counts: np.ndarray) -> np.ndarray:
		if self.idf_ is None:
			raise ValueError("TfidfVectorizer must be fit before transform.")

		row_sums = term_counts.sum(axis=1, keepdims=True)
		tf = np.divide(
			term_counts,
			row_sums,
			out=np.zeros_like(term_counts),
			where=row_sums != 0,
		)
		return tf * self.idf_


def cosine_similarity(query_vector: np.ndarray, document_matrix: np.ndarray) -> np.ndarray:
	query_norm = np.linalg.norm(query_vector)
	doc_norms = np.linalg.norm(document_matrix, axis=1)
	denominator = query_norm * doc_norms
	return np.divide(
		document_matrix @ query_vector,
		denominator,
		out=np.zeros_like(doc_norms),
		where=denominator != 0,
	)


class TfidfRetriever:
	def __init__(self, documents: list[dict]) -> None:
		self.documents = documents
		tokenized_docs = [doc["tokens"] for doc in documents]
		self.vectorizer = TfidfVectorizer()
		self.document_vectors = self.vectorizer.fit_transform(tokenized_docs)

	def search(self, query: str, top_k: int = 5) -> list[dict]:
		if not query.strip():
			return []

		query_tokens = normalize_query(query)
		if not query_tokens:
			return []

		query_vector = self.vectorizer.transform_query(query_tokens)
		scores = cosine_similarity(query_vector, self.document_vectors)
		ranked_indices = np.argsort(-scores)

		results: list[dict] = []
		ti = self.vectorizer.token_to_index_
		for idx in ranked_indices:
			score = float(scores[idx])
			if score <= 0:
				continue

			doc = self.documents[int(idx)]
			doc_row = self.document_vectors[int(idx)]
			term_parts: list[tuple[str, float]] = []
			for t in set(query_tokens):
				j = ti.get(t)
				if j is None:
					continue
				p = float(query_vector[j] * doc_row[j])
				if p > 0:
					term_parts.append((t, p))
			term_parts.sort(key=lambda x: -x[1])
			top_terms = [t for t, _ in term_parts[:8]]
			explain = {
				"summary": (
					f"Cosine similarity {score:.4f} between L2-normalized TF-IDF query and document vectors "
					f"(dot product / product of norms). "
					f"Strongest overlapping weighted terms: {', '.join(top_terms) if top_terms else '—'}."
				),
				"matched_terms": sorted({t for t in query_tokens if ti.get(t) is not None and doc_row[ti[t]] > 0}),
				"term_contributions": [{"term": t, "q_times_d": p} for t, p in term_parts[:12]],
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


def tfidf_search(query: str, data: list[dict], top_k: int = 5) -> list[dict]:
	return TfidfRetriever(data).search(query, top_k=top_k)