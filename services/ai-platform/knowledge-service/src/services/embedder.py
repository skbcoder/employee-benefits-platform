"""Embedding generation via Ollama."""

import logging

import ollama

from config.settings import settings

logger = logging.getLogger(__name__)


class Embedder:
    """Generates vector embeddings using Ollama's embedding models."""

    def __init__(self) -> None:
        self._client = ollama.AsyncClient(host=settings.ollama_base_url)
        self._model = settings.ollama_embed_model

    async def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text string."""
        response = await self._client.embed(model=self._model, input=text)
        embeddings = response.embeddings if hasattr(response, "embeddings") else response.get("embeddings", [])
        if not embeddings:
            raise ValueError("No embeddings returned from Ollama")
        return embeddings[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        results = []
        for text in texts:
            embedding = await self.embed(text)
            results.append(embedding)
        return results

    async def is_healthy(self) -> bool:
        """Check if the embedding model is available."""
        try:
            response = await self._client.list()
            model_names = [m.model for m in response.models]
            return any(self._model in name for name in model_names)
        except Exception as e:
            logger.warning(f"Embedder health check failed: {e}")
            return False


embedder = Embedder()
