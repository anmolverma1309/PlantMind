"""Lightweight, pure-Python vector store utilizing Google Gemini embeddings and numpy.

This serves as a zero-compile replacement for ChromaDB on Windows environments
without requiring C++ build tools.
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import numpy as np
import google.generativeai as genai
from api.config import GOOGLE_API_KEY, CHROMA_PERSIST_DIR

logger = logging.getLogger(__name__)

# Configure Gemini
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


class LocalVectorStore:
    """
    Local JSON-based vector store with numpy cosine similarity.
    Persists data in data/vector_db_mock.json.
    """

    def __init__(self):
        self.db_path = CHROMA_PERSIST_DIR.parent / "vector_db_mock.json"
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: List[List[float]] = []
        self.load()

    def load(self):
        """Load persisted chunks and embeddings from JSON."""
        if self.db_path.exists():
            try:
                data = json.loads(self.db_path.read_text(encoding='utf-8'))
                self.chunks = data.get("chunks", [])
                self.embeddings = data.get("embeddings", [])
                logger.info(f"Loaded {len(self.chunks)} vector chunks from {self.db_path}")
            except Exception as e:
                logger.error(f"Failed to load vector store: {e}")
                self.chunks = []
                self.embeddings = []

    def save(self):
        """Save chunks and embeddings to JSON."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "chunks": self.chunks,
            "embeddings": self.embeddings,
        }
        self.db_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
        logger.info(f"Saved {len(self.chunks)} vector chunks to {self.db_path}")

    def upsert(self, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]]):
        """Compute embeddings and add chunks to the local store."""
        if not GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY not set — mock embedding generation used (zero vectors)")
            new_embeddings = [[0.0] * 768 for _ in documents]
        else:
            try:
                # Compute embeddings in batch
                response = genai.embed_content(
                    model="models/embedding-001",
                    content=documents,
                    task_type="retrieval_document"
                )
                new_embeddings = response.get('embedding', [])
            except Exception as e:
                logger.error(f"Gemini embedding failed: {e}. Falling back to random embeddings for debugging.")
                # Fallback to random normalized embeddings if API fails
                new_embeddings = []
                for _ in documents:
                    vec = np.random.randn(768)
                    vec = vec / np.linalg.norm(vec)
                    new_embeddings.append(vec.tolist())

        # Merge / Update
        existing_ids = {c["id"]: idx for idx, c in enumerate(self.chunks)}
        
        for i, chunk_id in enumerate(ids):
            chunk_data = {
                "id": chunk_id,
                "text": documents[i],
                "metadata": metadatas[i],
            }
            emb = new_embeddings[i]
            
            if chunk_id in existing_ids:
                idx = existing_ids[chunk_id]
                self.chunks[idx] = chunk_data
                self.embeddings[idx] = emb
            else:
                self.chunks.append(chunk_data)
                self.embeddings.append(emb)
                
        self.save()

    def query(self, query_texts: List[str], n_results: int = 5) -> Dict[str, Any]:
        """Query vector store using cosine similarity."""
        query_text = query_texts[0]
        
        if not self.embeddings:
            return {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
                "ids": [[]],
            }
            
        # Get query embedding
        if not GOOGLE_API_KEY:
            query_emb = [0.0] * 768
        else:
            try:
                response = genai.embed_content(
                    model="models/embedding-001",
                    content=query_text,
                    task_type="retrieval_query"
                )
                query_emb = response.get('embedding', [0.0] * 768)
            except Exception as e:
                logger.error(f"Query embedding calculation failed: {e}")
                query_emb = [0.0] * 768

        # Compute cosine similarity using numpy
        q_vec = np.array(query_emb)
        db_vecs = np.array(self.embeddings)
        
        # Avoid division by zero
        q_norm = np.linalg.norm(q_vec)
        db_norms = np.linalg.norm(db_vecs, axis=1)
        
        if q_norm == 0 or np.any(db_norms == 0):
            scores = np.zeros(len(self.chunks))
        else:
            dot_products = np.dot(db_vecs, q_vec)
            scores = dot_products / (db_norms * q_norm)

        # Cosine distance = 1.0 - Cosine Similarity
        distances = 1.0 - scores
        
        # Sort indices
        top_indices = np.argsort(distances)[:n_results]
        
        ret_docs = []
        ret_metadatas = []
        ret_distances = []
        ret_ids = []
        
        for idx in top_indices:
            ret_docs.append(self.chunks[idx]["text"])
            ret_metadatas.append(self.chunks[idx]["metadata"])
            ret_distances.append(float(distances[idx]))
            ret_ids.append(self.chunks[idx]["id"])
            
        return {
            "documents": [ret_docs],
            "metadatas": [ret_metadatas],
            "distances": [ret_distances],
            "ids": [ret_ids],
        }

    def count(self) -> int:
        return len(self.chunks)


_local_vector_store: Optional[LocalVectorStore] = None


def get_local_vector_store() -> LocalVectorStore:
    global _local_vector_store
    if _local_vector_store is None:
        _local_vector_store = LocalVectorStore()
    return _local_vector_store
