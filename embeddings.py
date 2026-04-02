"""Embedding generation using Ollama."""
import httpx
from config import OLLAMA_BASE_URL, EMBEDDING_MODEL


def get_embedding(text: str) -> list[float]:
    """Get embedding for a single text via Ollama."""
    resp = httpx.post(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        json={"model": EMBEDDING_MODEL, "prompt": text},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Get embeddings for multiple texts sequentially via Ollama."""
    return [get_embedding(text) for text in texts]
