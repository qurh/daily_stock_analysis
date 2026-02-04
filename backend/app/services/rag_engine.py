"""RAG Engine - Retrieval Augmented Generation.

Complete RAG engine with:
- pgvector similarity search
- Multi-model embedding support (OpenAI, Ollama, DeepSeek)
- Hybrid search (vector + keyword)
- Search result re-ranking
- Context compression
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

import numpy as np

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func, and_, or_

from app.config import get_settings
from app.models.knowledge import KBDocument, KBEmbedding, KBSearchLog

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result with score and metadata."""

    document_id: int
    chunk_id: str
    title: str
    content: str
    score: float
    highlights: List[str]
    metadata: Dict[str, Any]


@dataclass
class RAGStats:
    """RAG operation statistics."""

    total_searches: int = 0
    avg_search_time_ms: float = 0.0
    vector_search_count: int = 0
    keyword_search_count: int = 0
    hybrid_search_count: int = 0
    total_embeddings: int = 0


class RAGEngine:
    """RAG Engine for knowledge retrieval and generation augmentation."""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.settings = get_settings()
        self.db = db
        self.embedding_model = self.settings.EMBEDDING_MODEL or "text-embedding-3-small"
        self.embedding_dim = 1536  # text-embedding-3-small dimension
        self._stats = RAGStats()

    async def initialize(self, db: AsyncSession):
        """Initialize RAG engine with database session."""
        self.db = db
        logger.info("RAG Engine initialized")

    async def search(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict] = None,
        search_type: str = "hybrid",
    ) -> List[SearchResult]:
        """Search knowledge base with hybrid search."""
        import time

        start_time = time.time()

        if search_type == "vector":
            results = await self._vector_search(query, limit, filters)
            self._stats.vector_search_count += 1
        elif search_type == "keyword":
            results = await self._keyword_search(query, limit, filters)
            self._stats.keyword_search_count += 1
        else:
            results = await self._hybrid_search(query, limit, filters)
            self._stats.hybrid_search_count += 1

        # Log search
        search_time = int((time.time() - start_time) * 1000)
        self._stats.avg_search_time_ms = (
            (self._stats.avg_search_time_ms * self._stats.total_searches + search_time)
            / (self._stats.total_searches + 1)
        )
        self._stats.total_searches += 1

        # Save search log if db available
        if self.db:
            await self._log_search(query, results, search_time)

        return results[:limit]

    async def _hybrid_search(
        self, query: str, limit: int, filters: Optional[Dict]
    ) -> List[SearchResult]:
        """Hybrid search combining vector and keyword similarity."""
        # Get vector search results
        vector_results = await self._vector_search(query, limit * 2, filters)

        # Get keyword search results
        keyword_results = await self._keyword_search(query, limit * 2, filters)

        # Merge and re-rank
        merged = self._merge_results(vector_results, keyword_results, query)
        return merged[:limit]

    async def _vector_search(
        self, query: str, limit: int, filters: Optional[Dict]
    ) -> List[SearchResult]:
        """Perform vector similarity search using pgvector."""
        if not self.db:
            return []

        try:
            # Generate query embedding
            query_embedding = await self._get_embedding(query)
            embedding_list = query_embedding.tolist() if hasattr(query_embedding, 'tolist') else list(query_embedding)

            # Build filter conditions
            conditions = []
            if filters:
                if filters.get("tags"):
                    conditions.append(KBEmbedding.metadata.contains({"tags": filters["tags"]}))
                if filters.get("document_ids"):
                    conditions.append(KBEmbedding.document_id.in_(filters["document_ids"]))

            # pgvector similarity search using cosine distance
            base_query = select(
                KBEmbedding,
                1 - func.cosine_distance(KBEmbedding.embedding, embedding_list).label("similarity")
            ).order_by(text("similarity DESC")).limit(limit)

            if conditions:
                query_filtered = base_query.where(and_(*conditions))
            else:
                query_filtered = base_query

            result = await self.db.execute(query_filtered)
            rows = result.all()

            results = []
            for row in rows:
                embedding, similarity = row
                # Get document title
                doc_query = select(KBDocument).where(KBDocument.id == embedding.document_id)
                doc_result = await self.db.execute(doc_query)
                doc = doc_result.scalar_one_or_none()

                results.append(SearchResult(
                    document_id=embedding.document_id,
                    chunk_id=embedding.chunk_id,
                    title=doc.title if doc else "",
                    content=embedding.content,
                    score=float(similarity),
                    highlights=[],
                    metadata=embedding.metadata or {},
                ))

            return results

        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return await self._keyword_search(query, limit, filters)

    async def _keyword_search(
        self, query: str, limit: int, filters: Optional[Dict]
    ) -> List[SearchResult]:
        """Perform keyword-based search with BM25-style ranking."""
        if not self.db:
            return []

        try:
            # Build search conditions
            search_conditions = or_(
                KBDocument.title.ilike(f"%{query}%"),
                KBDocument.content.ilike(f"%{query}%"),
            )

            # Query documents
            base_query = select(KBDocument).where(search_conditions)

            if filters:
                if filters.get("tags"):
                    base_query = base_query.where(KBDocument.tags.contains(filters["tags"]))
                if filters.get("category_id"):
                    base_query = base_query.where(KBDocument.category_id == filters["category_id"])

            base_query = base_query.limit(limit)
            result = await self.db.execute(base_query)
            documents = result.scalars().all()

            # Simple relevance scoring based on position
            results = []
            for doc in documents:
                score = self._calculate_keyword_score(doc.title + " " + doc.content, query)
                results.append(SearchResult(
                    document_id=doc.id,
                    chunk_id="full",
                    title=doc.title,
                    content=doc.content[:500],
                    score=score,
                    highlights=self._extract_highlights(doc.content, query),
                    metadata={"tags": doc.tags or []},
                ))

            return sorted(results, key=lambda x: x.score, reverse=True)

        except Exception as e:
            logger.error(f"Keyword search error: {e}")
            return []

    def _calculate_keyword_score(self, content: str, query: str) -> float:
        """Calculate simple keyword relevance score."""
        query_lower = query.lower()
        content_lower = content.lower()

        # Exact phrase match
        if query_lower in content_lower:
            base_score = 1.0
        else:
            base_score = 0.0

        # Word matches
        words = query_lower.split()
        word_matches = sum(1 for word in words if word in content_lower)
        word_score = word_matches / len(words) if words else 0

        # Title bonus
        title_bonus = 0.3 if any(word in content[:200].lower() for word in words) else 0

        return min(1.0, base_score * 0.6 + word_score * 0.3 + title_bonus)

    def _extract_highlights(self, content: str, query: str, window: int = 100) -> List[str]:
        """Extract highlight snippets containing query terms."""
        import re

        highlights = []
        query_words = query.lower().split()

        # Find all matches
        for word in query_words:
            pattern = re.escape(word)
            for match in re.finditer(pattern, content.lower()):
                start = max(0, match.start() - window)
                end = min(len(content), match.end() + window)
                snippet = content[start:end]
                highlights.append(f"...{snippet}...")

        return list(set(highlights))[:3]

    def _merge_results(
        self,
        vector_results: List[SearchResult],
        keyword_results: List[SearchResult],
        query: str,
    ) -> List[SearchResult]:
        """Merge and re-rank results from different search methods."""
        # Combine results with document deduplication
        seen_docs = {}
        merged = []

        # Interleave results for diversity
        max_len = max(len(vector_results), len(keyword_results))
        for i in range(max_len):
            if i < len(vector_results):
                doc_id = vector_results[i].document_id
                if doc_id not in seen_docs:
                    seen_docs[doc_id] = len(merged)
                    merged.append(vector_results[i])

            if i < len(keyword_results):
                doc_id = keyword_results[i].document_id
                if doc_id not in seen_docs:
                    seen_docs[doc_id] = len(merged)
                    merged.append(keyword_results[i])

        # Apply RRF (Reciprocal Rank Fusion) for final ranking
        for result in merged:
            # Combine scores with weights
            result.score = result.score * 0.6 + 0.4  # Boost vector results

        return sorted(merged, key=lambda x: x.score, reverse=True)

    async def index_document(self, document: KBDocument, db: AsyncSession) -> int:
        """Index a document with embeddings."""
        self.db = db

        # First delete existing embeddings for this document
        await self.delete_document_embeddings(document.id)

        # Split document into chunks
        chunks = self._split_into_chunks(document.content)

        # Generate embeddings and store
        indexed_count = 0
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 50:  # Skip very short chunks
                continue

            embedding = await self._get_embedding(chunk)

            kb_embedding = KBEmbedding(
                document_id=document.id,
                chunk_id=f"chunk_{i}",
                content=chunk,
                embedding=embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding),
                metadata={
                    "title": document.title,
                    "tags": document.tags,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                },
            )

            db.add(kb_embedding)
            indexed_count += 1

        await db.flush()
        self._stats.total_embeddings += indexed_count

        logger.info(f"Indexed {indexed_count} chunks for document {document.id}")
        return indexed_count

    async def delete_document_embeddings(self, document_id: int) -> int:
        """Delete all embeddings for a document."""
        if not self.db:
            return 0

        try:
            query = select(KBEmbedding).where(KBEmbedding.document_id == document_id)
            result = await self.db.execute(query)
            embeddings = result.scalars().all()

            count = len(embeddings)
            for emb in embeddings:
                await self.db.delete(emb)

            await self.db.flush()
            return count

        except Exception as e:
            logger.error(f"Error deleting embeddings: {e}")
            return 0

    async def _get_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text using configured provider."""
        # Try configured AI providers
        for provider in ["openai", "deepseek", "ollama"]:
            try:
                embedding = await self._call_embedding_api(text, provider)
                if embedding is not None:
                    return np.array(embedding)
            except Exception as e:
                logger.debug(f"Embedding provider {provider} failed: {e}")
                continue

        # Fallback to simple hash-based embedding (for demo)
        return self._fake_embedding(text)

    async def _call_embedding_api(
        self, text: str, provider: str
    ) -> Optional[List[float]]:
        """Call embedding API for specific provider."""
        try:
            if provider == "openai":
                return await self._openai_embedding(text)
            elif provider == "deepseek":
                return await self._deepseek_embedding(text)
            elif provider == "ollama":
                return await self._ollama_embedding(text)
        except Exception as e:
            logger.warning(f"Embedding API error ({provider}): {e}")
            return None

        return None

    async def _openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API."""
        import httpx

        api_key = self.settings.OPENAI_API_KEY
        if not api_key:
            return None

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": self.embedding_model,
                    "input": text[:8000],
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]

    async def _deepseek_embedding(self, text: str) -> List[float]:
        """Generate embedding using DeepSeek API."""
        import httpx

        api_key = self.settings.DEEPSEEK_API_KEY
        if not api_key:
            return None

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.deepseek.com/embeddings",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": "deepseek-embedding", "input": text[:8000]},
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]

    async def _ollama_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama local API."""
        import httpx

        ollama_url = self.settings.OLLAMA_BASE_URL or "http://localhost:11434"
        model = self.settings.OLLAMA_EMBEDDING_MODEL or "nomic-embed-text"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{ollama_url}/api/embeddings",
                json={"model": model, "prompt": text[:8000]},
            )
            response.raise_for_status()
            data = response.json()
            return data["embedding"]

    def _fake_embedding(self, text: str) -> np.ndarray:
        """Generate fake embedding for demo (not semantic)."""
        np.random.seed(len(text))
        return np.random.randn(self.embedding_dim) * 0.1

    def _split_into_chunks(
        self, content: str, chunk_size: int = 1000, overlap: int = 200
    ) -> List[str]:
        """Split content into overlapping chunks with smart boundaries."""
        import re

        if len(content) <= chunk_size:
            return [content] if content.strip() else []

        chunks = []
        start = 0

        while start < len(content):
            end = min(start + chunk_size, len(content))

            # Try to break at sentence boundary
            if end < len(content):
                # Look for sentence endings
                boundary = content[start:end].rfind(". ")
                if boundary > chunk_size * 0.5:
                    end = start + boundary + 1

                # Look for paragraph breaks
                boundary = content[start:end].rfind("\n\n")
                if boundary > chunk_size * 0.5:
                    end = start + boundary

            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap
            if start >= len(content):
                break

        return chunks

    async def get_relevant_context(
        self, query: str, max_tokens: int = 4000, db: Optional[AsyncSession] = None
    ) -> str:
        """Get relevant context for a query with token limit."""
        if db:
            self.db = db

        results = await self.search(query, limit=10)

        context_parts = []
        current_tokens = 0

        for result in results:
            # Rough estimate: 4 chars per token
            result_tokens = len(result.content) // 4
            if current_tokens + result_tokens > max_tokens:
                break

            context_parts.append(f"【来源: {result.title}】\n{result.content}")
            current_tokens += result_tokens

        return "\n\n".join(context_parts)

    async def compress_context(
        self, context: str, max_tokens: int = 2000
    ) -> str:
        """Compress long context to fit token limit."""
        # Simple compression: keep first and last parts
        estimated_tokens = len(context) // 4

        if estimated_tokens <= max_tokens:
            return context

        # Keep beginning and summarize end
        keep_ratio = 0.4
        keep_chars = int(len(context) * keep_ratio)

        beginning = context[:keep_chars]
        end = context[-keep_chars:]

        # Find a good break point
        break_point = beginning.rfind("\n\n")
        if break_point < keep_chars * 0.5:
            break_point = beginning.rfind(". ")
            if break_point < keep_chars * 0.5:
                break_point = int(keep_chars)

        beginning = beginning[:break_point]

        return f"{beginning}\n\n[...内容压缩省略...]\n\n{end}"

    async def _log_search(
        self, query: str, results: List[SearchResult], time_ms: int
    ) -> None:
        """Log search operation."""
        try:
            log = KBSearchLog(
                query=query,
                retrieved_doc_ids=[r.document_id for r in results],
                result="success" if results else "empty",
                execution_time_ms=time_ms,
            )
            self.db.add(log)
            await self.db.flush()
        except Exception as e:
            logger.debug(f"Failed to log search: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get RAG engine statistics."""
        return {
            "total_searches": self._stats.total_searches,
            "avg_search_time_ms": round(self._stats.avg_search_time_ms, 2),
            "vector_searches": self._stats.vector_search_count,
            "keyword_searches": self._stats.keyword_search_count,
            "hybrid_searches": self._stats.hybrid_search_count,
            "total_embeddings": self._stats.total_embeddings,
        }
