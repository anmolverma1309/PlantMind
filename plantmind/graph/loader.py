"""Load ingestion pipeline output into the knowledge graph and vector store."""

import logging
from pathlib import Path
from typing import Optional

from graph.graph_store import get_graph_store, GraphStore
from graph.vector_store import get_local_vector_store
from graph.schema import NodeType
from ingestion.schemas import DocumentOutput, EntityType

logger = logging.getLogger(__name__)


def load_document_to_graph(doc_output: DocumentOutput, graph: GraphStore = None) -> dict:
    """
    Load a single DocumentOutput into the knowledge graph and vector store.
    
    Steps:
    1. Create a Document node for this document
    2. Add all extracted entities as nodes
    3. Add all extracted relationships as edges
    4. Link entities to the document via MENTIONED_IN
    5. Embed text chunks into LocalVectorStore
    
    Returns:
        Stats dict with counts of nodes/edges/chunks added
    """
    if graph is None:
        graph = get_graph_store()
    
    stats = {"nodes_added": 0, "edges_added": 0, "chunks_embedded": 0}
    
    # 1. Create Document node
    doc_node_id = f"DOC:{doc_output.doc_id}"
    graph.add_node(
        doc_node_id,
        node_type=NodeType.DOCUMENT.value,
        name=doc_output.filename,
        doc_type=doc_output.doc_type.value,
        source_path=doc_output.source_path,
    )
    stats["nodes_added"] += 1
    
    # 2. Add entity nodes
    entity_id_map = {}  # maps entity name → graph node_id
    
    for entity in doc_output.entities:
        node_id = entity.name
        
        graph.add_node(
            node_id,
            node_type=entity.entity_type.value,
            name=entity.name,
            source_docs=[doc_output.filename],
            **entity.properties,
        )
        entity_id_map[entity.name] = node_id
        stats["nodes_added"] += 1
        
        # Link entity to document
        graph.add_relationship(
            node_id, doc_node_id,
            rel_type="MENTIONED_IN",
            confidence=entity.confidence,
        )
        stats["edges_added"] += 1
    
    # 3. Add relationships
    for rel in doc_output.relationships:
        source_id = entity_id_map.get(rel.source_entity, rel.source_entity)
        target_id = entity_id_map.get(rel.target_entity, rel.target_entity)
        
        graph.add_relationship(
            source_id, target_id,
            rel_type=rel.relationship_type.value,
            confidence=rel.confidence,
            **rel.properties,
        )
        stats["edges_added"] += 1
    
    # 4. Embed text chunks into LocalVectorStore
    vector_store = get_local_vector_store()
    
    if doc_output.raw_text_chunks:
        chunk_ids = []
        chunk_texts = []
        chunk_metadatas = []
        
        for chunk in doc_output.raw_text_chunks:
            chunk_id = f"{doc_output.doc_id}:{chunk.chunk_id}"
            chunk_ids.append(chunk_id)
            chunk_texts.append(chunk.text)
            
            # Build metadata with entity tags for filtered search
            entity_names = [e.name for e in doc_output.entities]
            chunk_metadatas.append({
                "doc_id": doc_output.doc_id,
                "doc_type": doc_output.doc_type.value,
                "filename": doc_output.filename,
                "chunk_index": chunk.chunk_index,
                "entities": ", ".join(entity_names[:20]),
            })
        
        # Upsert chunks
        vector_store.upsert(
            ids=chunk_ids,
            documents=chunk_texts,
            metadatas=chunk_metadatas,
        )
        stats["chunks_embedded"] = len(chunk_ids)
    
    logger.info(
        f"Loaded {doc_output.filename} → "
        f"{stats['nodes_added']} nodes, {stats['edges_added']} edges, "
        f"{stats['chunks_embedded']} chunks"
    )
    
    return stats


def load_all_documents(doc_outputs: list[DocumentOutput]) -> dict:
    """
    Load all processed documents into the graph and vector store.
    
    Args:
        doc_outputs: List of DocumentOutput from ingestion pipeline
    
    Returns:
        Aggregate stats
    """
    graph = get_graph_store()
    total_stats = {"nodes_added": 0, "edges_added": 0, "chunks_embedded": 0, "docs_loaded": 0}
    
    for doc_output in doc_outputs:
        try:
            stats = load_document_to_graph(doc_output, graph)
            total_stats["nodes_added"] += stats["nodes_added"]
            total_stats["edges_added"] += stats["edges_added"]
            total_stats["chunks_embedded"] += stats["chunks_embedded"]
            total_stats["docs_loaded"] += 1
        except Exception as e:
            logger.error(f"Failed to load {doc_output.filename}: {e}")
    
    # Save graph to JSON for persistence
    from api.config import DATA_DIR
    graph.save_to_json(str(DATA_DIR / "knowledge_graph.json"))
    
    logger.info(f"All documents loaded: {total_stats}")
    return total_stats
