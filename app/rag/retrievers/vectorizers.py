from __future__ import annotations

import numpy as np


def build_vocabulary(tokenized_docs: list[list[str]]) -> tuple[list[str], dict[str, int]]:
    vocabulary = sorted({token for doc in tokenized_docs for token in doc})
    token_to_index = {token: idx for idx, token in enumerate(vocabulary)}
    return vocabulary, token_to_index


def term_frequency_matrix(
    tokenized_docs: list[list[str]], token_to_index: dict[str, int]
) -> np.ndarray:
    matrix = np.zeros((len(tokenized_docs), len(token_to_index)), dtype=np.float64)
    for doc_idx, tokens in enumerate(tokenized_docs):
        for token in tokens:
            term_idx = token_to_index.get(token)
            if term_idx is not None:
                matrix[doc_idx, term_idx] += 1.0
    return matrix


def binary_matrix(count_matrix: np.ndarray) -> np.ndarray:
    return (count_matrix > 0).astype(np.float64)