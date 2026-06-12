"""TF-IDF + cosine similarity retrieval using jieba segmentation.

Designed for small corpora (~30-100 documents). No external services required.
"""
from __future__ import annotations

import math
from collections import Counter

import jieba
import numpy as np


def _tokenize(text: str) -> list[str]:
    """Segment Chinese text with jieba + character unigrams for robust matching.

    Combines jieba word segments with individual CJK characters so that
    partial matches (e.g. "窃" in "偷窃" vs "窃盗") still score.
    """
    tokens = list(jieba.cut(text))
    result: list[str] = []
    for t in tokens:
        t = t.strip().lower()
        if not t:
            continue
        result.append(t)
        # For CJK tokens longer than 1 char, also add individual characters
        # This ensures partial overlap between jieba segmentations
        if len(t) > 1:
            for ch in t:
                if '\u4e00' <= ch <= '\u9fff':  # CJK Unified Ideographs
                    result.append(ch)
    return result


class TfidfIndex:
    """In-memory TF-IDF index over a list of document dicts.

    Each document must have at minimum an ``id`` field.
    The ``text_fields`` parameter specifies which dict keys to index.
    """

    def __init__(
        self,
        docs: list[dict],
        text_fields: tuple[str, ...] = ("text", "keywords", "category", "id"),
    ):
        self._docs = docs
        self._text_fields = text_fields
        self._vocab: dict[str, int] = {}
        self._idf: np.ndarray | None = None
        self._doc_vectors: np.ndarray | None = None
        self._doc_norms: np.ndarray | None = None
        if docs:
            self._build()

    # ------------------------------------------------------------------
    # Index construction
    # ------------------------------------------------------------------

    def _doc_text(self, doc: dict) -> str:
        """Concatenate selected text fields from a document."""
        parts: list[str] = []
        for field in self._text_fields:
            val = doc.get(field)
            if isinstance(val, list):
                parts.extend(str(v) for v in val)
            elif val is not None:
                parts.append(str(val))
        return " ".join(parts)

    def _build(self) -> None:
        """Build TF-IDF vectors for all documents."""
        # Tokenize all documents
        doc_tokens: list[list[str]] = [
            _tokenize(self._doc_text(d)) for d in self._docs
        ]

        # Build vocabulary
        all_terms: set[str] = set()
        for tokens in doc_tokens:
            all_terms.update(tokens)
        self._vocab = {term: idx for idx, term in enumerate(sorted(all_terms))}
        vocab_size = len(self._vocab)
        n_docs = len(self._docs)

        # Compute IDF: log(N / (1 + df)) + 1  (smooth IDF)
        df = np.zeros(vocab_size, dtype=np.float64)
        for tokens in doc_tokens:
            seen = set(tokens)
            for t in seen:
                if t in self._vocab:
                    df[self._vocab[t]] += 1
        self._idf = np.log(n_docs / (1.0 + df)) + 1.0

        # Build TF-IDF vectors (l2-normalised)
        self._doc_vectors = np.zeros((n_docs, vocab_size), dtype=np.float64)
        for i, tokens in enumerate(doc_tokens):
            tf = Counter(tokens)
            for term, count in tf.items():
                if term in self._vocab:
                    idx = self._vocab[term]
                    self._doc_vectors[i, idx] = count * self._idf[idx]
        # L2-normalise rows
        norms = np.linalg.norm(self._doc_vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0  # avoid division by zero
        self._doc_vectors = self._doc_vectors / norms
        self._doc_norms = np.ones(n_docs, dtype=np.float64)  # already normalised

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(self, text: str, top_k: int = 5) -> list[dict]:
        """Return up to ``top_k`` documents ranked by cosine similarity to *text*.

        Returns a list of dicts with ``score`` and the original document fields.
        """
        if not self._docs or self._doc_vectors is None:
            return []

        tokens = _tokenize(text)
        if not tokens:
            return []

        # Build query vector
        qvec = np.zeros(len(self._vocab), dtype=np.float64)
        tf = Counter(tokens)
        for term, count in tf.items():
            if term in self._vocab:
                idx = self._vocab[term]
                qvec[idx] = count * self._idf[idx]
        qnorm = np.linalg.norm(qvec)
        if qnorm == 0:
            return []
        qvec = qvec / qnorm

        # Cosine similarity (both already L2-normalised)
        scores = self._doc_vectors @ qvec

        # Top-k indices
        k = min(top_k, len(self._docs))
        top_indices = np.argsort(scores)[::-1][:k]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score <= 0:
                break
            results.append({**self._docs[idx], "_score": round(score, 4)})
        return results
