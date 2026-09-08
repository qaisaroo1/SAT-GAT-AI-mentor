import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from langchain_text_splitters import MarkdownHeaderTextSplitter
from src.config import DATA_DIR, STORAGE_DIR, GEMINI_API_KEY, EMBEDDING_MODEL

# Try importing Google GenAI SDK
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None


class KnowledgeStore:
    """
    RAG Knowledge Store tailored for Markdown test prep books.
    Maintains Markdown hierarchy (Chapter, Topic, Subtopic) in metadata
    and performs semantic search via Gemini Embeddings with BM25/keyword fallback.
    """

    def __init__(self, storage_file: Optional[Path] = None):
        self.storage_file = storage_file or (STORAGE_DIR / "knowledge_store.json")
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.client = None

        if GEMINI_API_KEY and genai:
            try:
                self.client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                print(f"[KnowledgeStore] Warning: could not initialize Gemini client: {e}")

        self.load()

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        if not self.client:
            return None
        try:
            response = self.client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text,
            )
            if response.embeddings:
                return response.embeddings[0].values
        except Exception as e:
            print(f"[KnowledgeStore] Embedding error: {e}")
        return None

    def index_markdown_file(self, file_path: Path, exam_type: str):
        """Chunk a markdown file by headers and compute embeddings."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        text = file_path.read_text(encoding="utf-8")

        headers_to_split_on = [
            ("#", "chapter"),
            ("##", "topic"),
            ("###", "subtopic"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            strip_headers=False
        )
        md_chunks = markdown_splitter.split_text(text)

        new_chunks = []
        for i, doc in enumerate(md_chunks):
            content = doc.page_content.strip()
            if not content:
                continue

            metadata = doc.metadata.copy()
            metadata["exam_type"] = exam_type
            metadata["source_file"] = file_path.name
            metadata["chunk_id"] = f"{exam_type}_{file_path.stem}_{i}"

            # Calculate embedding if client is ready
            vector = self._get_embedding(content)

            new_chunks.append({
                "id": metadata["chunk_id"],
                "content": content,
                "metadata": metadata,
                "embedding": vector
            })

        # Avoid duplicates
        existing_ids = {c["id"] for c in self.chunks}
        for chunk in new_chunks:
            if chunk["id"] not in existing_ids:
                self.chunks.append(chunk)

        self.save()
        print(f"[KnowledgeStore] Successfully indexed {len(new_chunks)} chunks from {file_path.name}")

    def save(self):
        """Save chunk metadata and vectors to disk."""
        data = {
            "chunks": self.chunks
        }
        self.storage_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self):
        """Load stored chunks from disk."""
        if self.storage_file.exists():
            try:
                data = json.loads(self.storage_file.read_text(encoding="utf-8"))
                self.chunks = data.get("chunks", [])
                print(f"[KnowledgeStore] Loaded {len(self.chunks)} chunks from storage.")
            except Exception as e:
                print(f"[KnowledgeStore] Error loading storage: {e}")
                self.chunks = []

    def search(self, query: str, exam_type: Optional[str] = None, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Hybrid search: Semantic vector similarity if embeddings exist,
        falling back to keyword overlap.
        """
        if not self.chunks:
            return []

        filtered_chunks = [
            c for c in self.chunks
            if exam_type is None or c.get("metadata", {}).get("exam_type", "").upper() == exam_type.upper()
        ]

        if not filtered_chunks:
            filtered_chunks = self.chunks

        # Try semantic search if query embedding succeeds
        query_vector = self._get_embedding(query)
        if query_vector is not None and any(c.get("embedding") is not None for c in filtered_chunks):
            scores = []
            qv = np.array(query_vector)
            q_norm = np.linalg.norm(qv) or 1.0

            for c in filtered_chunks:
                emb = c.get("embedding")
                if emb is not None:
                    cv = np.array(emb)
                    c_norm = np.linalg.norm(cv) or 1.0
                    sim = float(np.dot(qv, cv) / (q_norm * c_norm))
                else:
                    sim = 0.0
                scores.append((sim, c))

            scores.sort(key=lambda x: x[0], reverse=True)
            return [chunk for score, chunk in scores[:top_k]]

        # Fallback: Token overlap search (BM25-style keyword matching)
        query_tokens = set(re.findall(r"\w+", query.lower()))
        scores = []
        for c in filtered_chunks:
            content_tokens = set(re.findall(r"\w+", c["content"].lower()))
            overlap = len(query_tokens.intersection(content_tokens))
            scores.append((overlap, c))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [chunk for score, chunk in scores[:top_k]]

    def get_topics_by_exam(self, exam_type: str) -> List[str]:
        """Extract unique topics available for a specific exam."""
        topics = []
        for c in self.chunks:
            meta = c.get("metadata", {})
            if meta.get("exam_type", "").upper() == exam_type.upper():
                t = meta.get("topic")
                if t and t not in topics:
                    topics.append(t)
        return topics

    def get_topic_content(self, topic: str, exam_type: str) -> str:
        """Fetch all content chunks associated with a specific topic."""
        relevant_chunks = [
            c["content"] for c in self.chunks
            if c.get("metadata", {}).get("exam_type", "").upper() == exam_type.upper()
            and c.get("metadata", {}).get("topic", "").lower() == topic.lower()
        ]
        if relevant_chunks:
            return "\n\n".join(relevant_chunks)
        # Fallback to semantic search
        results = self.search(topic, exam_type=exam_type, top_k=2)
        return "\n\n".join([r["content"] for r in results])


def initialize_default_knowledge_base() -> KnowledgeStore:
    """Convenience helper to index both default SAT and GAT prep files."""
    store = KnowledgeStore()
    sat_file = DATA_DIR / "sat_math_sample.md"
    gat_file = DATA_DIR / "gat_analytical_sample.md"

    if sat_file.exists():
        store.index_markdown_file(sat_file, "SAT")
    if gat_file.exists():
        store.index_markdown_file(gat_file, "GAT")

    return store


if __name__ == "__main__":
    print("Initializing knowledge store...")
    kb = initialize_default_knowledge_base()
    results = kb.search("perpendicular line slope", exam_type="SAT")
    print(f"\nSearch test found {len(results)} matches:")
    for r in results:
        print(f"\n--- {r['metadata'].get('topic')} / {r['metadata'].get('subtopic')} ---")
        print(r['content'][:200] + "...")
