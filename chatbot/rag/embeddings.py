"""Embedding functions for AgriNova Agriculture RAG."""

import logging
import os
from pathlib import Path
from typing import List, Optional

import numpy as np
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from django.conf import settings
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 384


class LocalAgriculturalEmbeddingFunction(EmbeddingFunction[Documents]):
    """
    Local, deterministic embedding function using TF-IDF with character and word n-grams,
    projected into fixed-dimension L2-normalized vector space.
    Completely offline and requires no internet connection or external API keys.
    """

    def __init__(self, n_dimensions: int = EMBEDDING_DIM, model_path: Optional[str] = None):
        self.n_dimensions = n_dimensions
        self.model_path = model_path
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._load_or_init()

    def _load_or_init(self):
        if self.model_path and os.path.exists(self.model_path):
            try:
                import joblib
                self._vectorizer = joblib.load(self.model_path)
                return
            except Exception as exc:
                logger.warning("Could not load persisted vectorizer from %s: %s", self.model_path, exc)

        self._vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words='english',
            max_features=self.n_dimensions,
            sublinear_tf=True,
        )

    def fit(self, corpus: List[str]):
        """Fit the vectorizer on the agriculture corpus and save to disk if path is provided."""
        if not corpus:
            return
        self._vectorizer.fit(corpus)
        if self.model_path:
            try:
                import joblib
                os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
                joblib.dump(self._vectorizer, self.model_path)
            except Exception as exc:
                logger.warning("Could not persist vectorizer to %s: %s", self.model_path, exc)

    def __call__(self, input: Documents) -> Embeddings:
        """Transform documents into normalized embeddings list."""
        if not input:
            return []

        # Check if vectorizer has been fitted with vocabulary
        if not hasattr(self._vectorizer, 'vocabulary_'):
            # Fit on the incoming batch as fallback
            self._vectorizer.fit(input)

        sparse_matrix = self._vectorizer.transform(input)
        dense = sparse_matrix.toarray().astype(np.float32)

        # Pad with zeros if features < n_dimensions
        if dense.shape[1] < self.n_dimensions:
            padding = np.zeros((dense.shape[0], self.n_dimensions - dense.shape[1]), dtype=np.float32)
            dense = np.hstack([dense, padding])
        elif dense.shape[1] > self.n_dimensions:
            dense = dense[:, :self.n_dimensions]

        # L2-normalize each vector
        norms = np.linalg.norm(dense, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized = dense / norms

        return normalized.tolist()


class GeminiEmbeddingFunction(EmbeddingFunction[Documents]):
    """Gemini API embedding function using google-genai SDK."""

    def __init__(self, api_key: Optional[str] = None, model: str = 'gemini-embedding-001'):
        self.api_key = api_key or getattr(settings, 'GEMINI_API_KEY', '')
        self.model = model

    def __call__(self, input: Documents) -> Embeddings:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured for Gemini embeddings.")

        from google import genai
        client = genai.Client(api_key=self.api_key)

        results = []
        for text in input:
            resp = client.models.embed_content(
                model=self.model,
                contents=text,
            )
            if resp and resp.embeddings and len(resp.embeddings) > 0:
                results.append(list(resp.embeddings[0].values))
            else:
                results.append([0.0] * 768)
        return results


def get_embedding_function(provider: Optional[str] = None) -> EmbeddingFunction[Documents]:
    """Factory to get the configured embedding function."""
    provider_name = (provider or getattr(settings, 'RAG_EMBEDDING_PROVIDER', 'local')).lower()

    persist_dir = getattr(settings, 'CHROMA_PERSIST_DIR', str(Path(settings.BASE_DIR) / 'data' / 'chroma_db'))
    model_path = os.path.join(persist_dir, 'tfidf_vectorizer.joblib')

    if provider_name == 'gemini':
        try:
            return GeminiEmbeddingFunction()
        except Exception as exc:
            logger.warning("Failed to initialize Gemini embedding, falling back to local: %s", exc)

    return LocalAgriculturalEmbeddingFunction(model_path=model_path)
