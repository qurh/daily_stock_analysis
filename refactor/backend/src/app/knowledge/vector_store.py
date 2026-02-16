from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any

import chromadb


class ChromaVectorStore:
    """Chroma-backed vector store with deterministic local embeddings."""

    def __init__(self, path: str, collection_name: str) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=path)
        self._collection = self._client.get_or_create_collection(name=collection_name)

    def upsert_chunks(self, records: list[dict[str, Any]]) -> None:
        if not records:
            return
        self._collection.upsert(
            ids=[item["chunk_id"] for item in records],
            documents=[item["content"] for item in records],
            embeddings=[_embed_text(item["content"]) for item in records],
            metadatas=[
                {
                    "doc_id": item["doc_id"],
                    "section_path": item["section_path"],
                    "summary": item["summary"],
                }
                for item in records
            ],
        )

    def delete_document(self, doc_id: str) -> None:
        self._collection.delete(where={"doc_id": doc_id})

    def search(self, query: str, top_k: int, doc_id: str | None = None) -> list[dict[str, Any]]:
        if top_k <= 0:
            return []

        params: dict[str, Any] = {
            "query_embeddings": [_embed_text(query)],
            "n_results": top_k,
        }
        if doc_id:
            params["where"] = {"doc_id": doc_id}
        result = self._collection.query(**params)
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        hits: list[dict[str, Any]] = []
        for idx, chunk_id in enumerate(ids):
            metadata = metadatas[idx] if idx < len(metadatas) else {}
            document = documents[idx] if idx < len(documents) else ""
            distance = float(distances[idx]) if idx < len(distances) else 0.0
            score = max(0.0, 1.0 - distance)
            hits.append(
                {
                    "chunk_id": chunk_id,
                    "doc_id": metadata.get("doc_id", ""),
                    "section_path": metadata.get("section_path", ""),
                    "summary": metadata.get("summary", ""),
                    "content": document,
                    "score": score,
                }
            )
        return hits


def _embed_text(text: str, dimensions: int = 64) -> list[float]:
    tokens = _tokenize(text)
    vector = [0.0] * dimensions
    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = digest[0] % dimensions
        sign = 1.0 if digest[1] % 2 == 0 else -1.0
        magnitude = (digest[2] / 255.0) + 0.01
        vector[index] += sign * magnitude

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def _tokenize(text: str) -> list[str]:
    compact = text.strip().lower()
    if not compact:
        return []
    word_tokens = [token for token in compact.replace("\n", " ").split(" ") if token]
    if word_tokens:
        return word_tokens
    return list(compact)
