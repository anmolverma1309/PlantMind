# Step 4 — Knowledge Graph Construction

## Objective
Load all extracted entities and relationships from Step 3 into a NetworkX graph, embed text chunks into ChromaDB, and expose graph query endpoints. This is the **differentiator** versus a plain RAG chatbot.

---

## 4.1 Graph Schema Definition

**File:** `plantmind/graph/schema.py`

```python
"""Knowledge graph schema definition — node types, relationship types, and validation."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    EQUIPMENT = "Equipment"
    DOCUMENT = "Document"
    PROCEDURE = "Procedure"
    INCIDENT = "Incident"
    REGULATION = "Regulation"
    PERSON = "Person"
    WORK_ORDER = "WorkOrder"
    LOCATION = "Location"
    FAILURE_MODE = "FailureMode"


class RelType(str, Enum):
    MENTIONED_IN = "MENTIONED_IN"
    MAINTAINED_BY = "MAINTAINED_BY"
    GOVERNED_BY = "GOVERNED_BY"
    CAUSED_BY = "CAUSED_BY"
    PART_OF = "PART_OF"
    PERFORMED_BY = "PERFORMED_BY"
    REFERENCES = "REFERENCES"
    LOCATED_AT = "LOCATED_AT"
    HAS_FAILURE = "HAS_FAILURE"
    LINKED_TO = "LINKED_TO"


class GraphNode(BaseModel):
    """Schema for a node in the knowledge graph."""
    node_id: str
    node_type: NodeType
    name: str
    properties: dict = Field(default_factory=dict)
    source_docs: list[str] = Field(default_factory=list)


class GraphEdge(BaseModel):
    """Schema for an edge (relationship) in the knowledge graph."""
    source_id: str
    target_id: str
    rel_type: RelType
    properties: dict = Field(default_factory=dict)
    confidence: float = 1.0


# Valid relationship constraints: (source_type, rel_type, target_type)
VALID_RELATIONSHIPS = [
    (NodeType.EQUIPMENT, RelType.MENTIONED_IN, NodeType.DOCUMENT),
    (NodeType.EQUIPMENT, RelType.MAINTAINED_BY, NodeType.PERSON),
    (NodeType.EQUIPMENT, RelType.GOVERNED_BY, NodeType.REGULATION),
    (NodeType.EQUIPMENT, RelType.PART_OF, NodeType.LOCATION),
    (NodeType.EQUIPMENT, RelType.HAS_FAILURE, NodeType.FAILURE_MODE),
    (NodeType.WORK_ORDER, RelType.MENTIONED_IN, NodeType.EQUIPMENT),
    (NodeType.WORK_ORDER, RelType.PERFORMED_BY, NodeType.PERSON),
    (NodeType.INCIDENT, RelType.CAUSED_BY, NodeType.FAILURE_MODE),
    (NodeType.INCIDENT, RelType.MENTIONED_IN, NodeType.DOCUMENT),
    (NodeType.PROCEDURE, RelType.REFERENCES, NodeType.REGULATION),
    (NodeType.PROCEDURE, RelType.REFERENCES, NodeType.EQUIPMENT),
    (NodeType.DOCUMENT, RelType.REFERENCES, NodeType.REGULATION),
    (NodeType.PERSON, RelType.PERFORMED_BY, NodeType.WORK_ORDER),
    # Allow flexible relationships for prototype
    (None, RelType.LINKED_TO, None),  # Catch-all
]
```

---

## 4.2 Enhanced Graph Store

Update `plantmind/graph/graph_store.py` — replace the boilerplate from Step 1 with the full implementation:

**File:** `plantmind/graph/graph_store.py`

```python
"""Graph store — NetworkX-based knowledge graph with query capabilities."""

import json
import logging
import networkx as nx
from pathlib import Path
from typing import Optional
from graph.schema import NodeType, RelType, GraphNode, GraphEdge

logger = logging.getLogger(__name__)

_graph_store: Optional["GraphStore"] = None


class GraphStore:
    """
    NetworkX-based knowledge graph for PlantMind.
    
    Supports:
    - Adding nodes with types and properties
    - Adding typed relationships
    - Multi-hop traversal queries
    - Subgraph extraction for context building
    - Export for visualization
    - Persistence to/from JSON
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self._node_index: dict[str, set[str]] = {}  # type -> set of node_ids

    # ── Node Operations ──────────────────────────────────────────

    def add_node(self, node_id: str, node_type: str, name: str = "", **properties) -> str:
        """Add or update a node. Returns the node_id."""
        # Normalize node_id
        node_id = self._normalize_id(node_id)
        
        if node_id in self.graph.nodes:
            # Merge properties
            existing = self.graph.nodes[node_id]
            existing.update(properties)
            # Merge source_docs
            if 'source_docs' in properties:
                existing_docs = set(existing.get('source_docs', []))
                existing_docs.update(properties.get('source_docs', []))
                existing['source_docs'] = list(existing_docs)
        else:
            self.graph.add_node(
                node_id,
                node_type=node_type,
                name=name or node_id,
                **properties,
            )
        
        # Update type index
        if node_type not in self._node_index:
            self._node_index[node_type] = set()
        self._node_index[node_type].add(node_id)
        
        return node_id

    def get_node(self, node_id: str) -> Optional[dict]:
        """Get a node by ID."""
        node_id = self._normalize_id(node_id)
        if node_id in self.graph.nodes:
            return {"id": node_id, **self.graph.nodes[node_id]}
        return None

    def find_node(self, name: str) -> Optional[dict]:
        """Find a node by name (case-insensitive fuzzy match)."""
        name_lower = name.lower().strip()
        for nid, data in self.graph.nodes(data=True):
            if (nid.lower() == name_lower or 
                data.get('name', '').lower() == name_lower):
                return {"id": nid, **data}
        # Partial match fallback
        for nid, data in self.graph.nodes(data=True):
            if (name_lower in nid.lower() or 
                name_lower in data.get('name', '').lower()):
                return {"id": nid, **data}
        return None

    # ── Relationship Operations ──────────────────────────────────

    def add_relationship(self, source_id: str, target_id: str, rel_type: str, **properties) -> None:
        """Add a directed relationship between two nodes."""
        source_id = self._normalize_id(source_id)
        target_id = self._normalize_id(target_id)
        
        # Auto-create nodes if they don't exist
        if source_id not in self.graph.nodes:
            logger.warning(f"Source node '{source_id}' not in graph — auto-creating")
            self.add_node(source_id, "Unknown", name=source_id)
        if target_id not in self.graph.nodes:
            logger.warning(f"Target node '{target_id}' not in graph — auto-creating")
            self.add_node(target_id, "Unknown", name=target_id)
        
        self.graph.add_edge(source_id, target_id, rel_type=rel_type, **properties)

    # ── Query Operations ─────────────────────────────────────────

    def get_neighbors(self, node_id: str, rel_type: str = None, direction: str = "both") -> list[dict]:
        """
        Get all neighbors of a node, optionally filtered by relationship type.
        
        Args:
            node_id: Node to query
            rel_type: Filter by relationship type (None = all)
            direction: "out", "in", or "both"
        """
        node_id = self._normalize_id(node_id)
        if node_id not in self.graph.nodes:
            return []
        
        neighbors = []
        
        if direction in ("out", "both"):
            for _, target, data in self.graph.out_edges(node_id, data=True):
                if rel_type is None or data.get("rel_type") == rel_type:
                    neighbors.append({
                        "id": target,
                        "direction": "outgoing",
                        "rel_type": data.get("rel_type"),
                        **self.graph.nodes[target],
                    })
        
        if direction in ("in", "both"):
            for source, _, data in self.graph.in_edges(node_id, data=True):
                if rel_type is None or data.get("rel_type") == rel_type:
                    neighbors.append({
                        "id": source,
                        "direction": "incoming",
                        "rel_type": data.get("rel_type"),
                        **self.graph.nodes[source],
                    })
        
        return neighbors

    def get_by_type(self, node_type: str) -> list[dict]:
        """Get all nodes of a given type."""
        node_ids = self._node_index.get(node_type, set())
        return [{"id": nid, **self.graph.nodes[nid]} for nid in node_ids if nid in self.graph.nodes]

    def traverse(self, start_id: str, max_depth: int = 2) -> dict:
        """
        BFS traversal from a start node up to max_depth hops.
        Returns subgraph as nodes + edges for context building.
        """
        start_id = self._normalize_id(start_id)
        if start_id not in self.graph.nodes:
            return {"nodes": [], "edges": []}
        
        visited = set()
        queue = [(start_id, 0)]
        nodes = []
        edges = []
        
        while queue:
            current, depth = queue.pop(0)
            if current in visited or depth > max_depth:
                continue
            visited.add(current)
            
            nodes.append({"id": current, **self.graph.nodes[current]})
            
            # Outgoing edges
            for _, target, data in self.graph.out_edges(current, data=True):
                edges.append({
                    "source": current,
                    "target": target,
                    "rel_type": data.get("rel_type", "UNKNOWN"),
                })
                if target not in visited:
                    queue.append((target, depth + 1))
            
            # Incoming edges
            for source, _, data in self.graph.in_edges(current, data=True):
                edges.append({
                    "source": source,
                    "target": current,
                    "rel_type": data.get("rel_type", "UNKNOWN"),
                })
                if source not in visited:
                    queue.append((source, depth + 1))
        
        return {"nodes": nodes, "edges": edges}

    def find_path(self, source_id: str, target_id: str) -> list[dict]:
        """Find shortest path between two nodes."""
        source_id = self._normalize_id(source_id)
        target_id = self._normalize_id(target_id)
        
        try:
            # Try undirected path
            undirected = self.graph.to_undirected()
            path = nx.shortest_path(undirected, source_id, target_id)
            return [{"id": nid, **self.graph.nodes[nid]} for nid in path]
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def find_common_neighbors(self, node_ids: list[str]) -> list[dict]:
        """Find nodes that are connected to ALL of the given nodes."""
        if not node_ids:
            return []
        
        neighbor_sets = []
        for nid in node_ids:
            nid = self._normalize_id(nid)
            neighbors = set()
            for n in self.get_neighbors(nid):
                neighbors.add(n["id"])
            neighbor_sets.append(neighbors)
        
        common = neighbor_sets[0]
        for ns in neighbor_sets[1:]:
            common = common.intersection(ns)
        
        return [{"id": nid, **self.graph.nodes[nid]} for nid in common if nid in self.graph.nodes]

    # ── Export / Visualization ───────────────────────────────────

    def export_for_visualization(self) -> dict:
        """Export graph in format suitable for force-directed graph visualization."""
        nodes = []
        for nid, data in self.graph.nodes(data=True):
            nodes.append({
                "id": nid,
                "label": data.get("name", nid),
                "type": data.get("node_type", "Unknown"),
                "properties": {k: v for k, v in data.items() 
                              if k not in ("node_type", "name", "source_docs")},
            })
        
        edges = []
        for source, target, data in self.graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "label": data.get("rel_type", "LINKED_TO"),
                "properties": {k: v for k, v in data.items() if k != "rel_type"},
            })
        
        return {"nodes": nodes, "edges": edges}

    def get_stats(self) -> dict:
        """Get graph statistics."""
        type_counts = {}
        for _, data in self.graph.nodes(data=True):
            t = data.get("node_type", "Unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        
        rel_counts = {}
        for _, _, data in self.graph.edges(data=True):
            r = data.get("rel_type", "Unknown")
            rel_counts[r] = rel_counts.get(r, 0) + 1
        
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "node_types": type_counts,
            "relationship_types": rel_counts,
            "connected_components": nx.number_weakly_connected_components(self.graph),
        }

    # ── Persistence ──────────────────────────────────────────────

    def save_to_json(self, filepath: str) -> None:
        """Save graph to JSON file for persistence."""
        data = {
            "nodes": [
                {"id": nid, **{k: v for k, v in d.items()}}
                for nid, d in self.graph.nodes(data=True)
            ],
            "edges": [
                {"source": s, "target": t, **{k: v for k, v in d.items()}}
                for s, t, d in self.graph.edges(data=True)
            ],
        }
        Path(filepath).write_text(json.dumps(data, indent=2, default=str), encoding='utf-8')
        logger.info(f"Graph saved to {filepath}")

    def load_from_json(self, filepath: str) -> None:
        """Load graph from JSON file."""
        data = json.loads(Path(filepath).read_text(encoding='utf-8'))
        
        for node in data.get("nodes", []):
            nid = node.pop("id")
            self.add_node(nid, **node)
        
        for edge in data.get("edges", []):
            source = edge.pop("source")
            target = edge.pop("target")
            rel_type = edge.pop("rel_type", "LINKED_TO")
            self.add_relationship(source, target, rel_type, **edge)
        
        logger.info(f"Graph loaded from {filepath}: {self.get_stats()}")

    # ── Internal ─────────────────────────────────────────────────

    @staticmethod
    def _normalize_id(node_id: str) -> str:
        """Normalize node IDs for consistent matching."""
        return node_id.strip()


def get_graph_store() -> GraphStore:
    """Singleton accessor for the global graph store."""
    global _graph_store
    if _graph_store is None:
        _graph_store = GraphStore()
    return _graph_store


def reset_graph_store() -> GraphStore:
    """Reset the global graph store (for testing)."""
    global _graph_store
    _graph_store = GraphStore()
    return _graph_store
```

---

## 4.3 Graph Loader — Ingestion Output → Graph

**File:** `plantmind/graph/loader.py`

```python
"""Load ingestion pipeline output into the knowledge graph and vector store."""

import logging
from pathlib import Path
from typing import Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from graph.graph_store import get_graph_store, GraphStore
from graph.schema import NodeType
from ingestion.schemas import DocumentOutput, EntityType
from api.config import CHROMA_PERSIST_DIR

logger = logging.getLogger(__name__)

# Global ChromaDB client
_chroma_client: Optional[chromadb.Client] = None
_collection = None


def get_chroma_collection():
    """Get or create the ChromaDB collection for document chunks."""
    global _chroma_client, _collection
    
    if _collection is None:
        persist_dir = str(CHROMA_PERSIST_DIR)
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        
        _chroma_client = chromadb.PersistentClient(path=persist_dir)
        _collection = _chroma_client.get_or_create_collection(
            name="plantmind_chunks",
            metadata={"description": "PlantMind document chunks for RAG retrieval"},
        )
    
    return _collection


def load_document_to_graph(doc_output: DocumentOutput, graph: GraphStore = None) -> dict:
    """
    Load a single DocumentOutput into the knowledge graph and vector store.
    
    Steps:
    1. Create a Document node for this document
    2. Add all extracted entities as nodes
    3. Add all extracted relationships as edges
    4. Link entities to the document via MENTIONED_IN
    5. Embed text chunks into ChromaDB
    
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
        # Use entity name as node_id (for cross-document dedup)
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
    
    # 4. Embed text chunks into ChromaDB
    collection = get_chroma_collection()
    
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
                "entities": ", ".join(entity_names[:20]),  # ChromaDB metadata size limits
            })
        
        # Upsert chunks (ChromaDB handles embedding via its default model)
        collection.upsert(
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
    graph.save_to_json(str(CHROMA_PERSIST_DIR.parent / "knowledge_graph.json"))
    
    logger.info(f"All documents loaded: {total_stats}")
    return total_stats
```

---

## 4.4 Graph Query Utilities

**File:** `plantmind/graph/queries.py`

```python
"""Pre-built graph queries for common PlantMind use cases."""

import logging
from graph.graph_store import get_graph_store
from graph.schema import NodeType, RelType

logger = logging.getLogger(__name__)


def get_equipment_history(equipment_tag: str) -> dict:
    """
    Get full history of an equipment item: work orders, incidents, 
    related procedures, and regulatory requirements.
    
    This is the core query for the RCA agent.
    """
    graph = get_graph_store()
    node = graph.find_node(equipment_tag)
    
    if not node:
        return {"equipment": None, "error": f"Equipment '{equipment_tag}' not found"}
    
    # 2-hop traversal to get full context
    subgraph = graph.traverse(node["id"], max_depth=2)
    
    # Categorize neighbors
    work_orders = []
    incidents = []
    procedures = []
    regulations = []
    people = []
    failure_modes = []
    documents = []
    
    for n in subgraph["nodes"]:
        nt = n.get("node_type", "")
        if nt == NodeType.WORK_ORDER.value:
            work_orders.append(n)
        elif nt == NodeType.INCIDENT.value:
            incidents.append(n)
        elif nt == NodeType.PROCEDURE.value:
            procedures.append(n)
        elif nt == NodeType.REGULATION.value:
            regulations.append(n)
        elif nt == NodeType.PERSON.value:
            people.append(n)
        elif nt == NodeType.FAILURE_MODE.value:
            failure_modes.append(n)
        elif nt == NodeType.DOCUMENT.value:
            documents.append(n)
    
    return {
        "equipment": node,
        "work_orders": work_orders,
        "incidents": incidents,
        "procedures": procedures,
        "regulations": regulations,
        "people": people,
        "failure_modes": failure_modes,
        "documents": documents,
        "subgraph": subgraph,
    }


def find_compliance_gaps() -> list[dict]:
    """
    Find equipment or procedures that reference a regulation 
    but may not have a linked compliant procedure.
    
    This is the core query for the Compliance agent.
    """
    graph = get_graph_store()
    gaps = []
    
    # Get all regulation nodes
    regulations = graph.get_by_type(NodeType.REGULATION.value)
    
    for reg in regulations:
        reg_id = reg["id"]
        
        # Find all equipment governed by this regulation
        governed_equipment = []
        for neighbor in graph.get_neighbors(reg_id, direction="in"):
            if neighbor.get("node_type") == NodeType.EQUIPMENT.value:
                governed_equipment.append(neighbor)
        
        # For each governed equipment, check if there's a linked procedure
        for equip in governed_equipment:
            equip_neighbors = graph.get_neighbors(equip["id"])
            has_procedure = any(
                n.get("node_type") == NodeType.PROCEDURE.value 
                for n in equip_neighbors
            )
            
            if not has_procedure:
                gaps.append({
                    "equipment": equip,
                    "regulation": reg,
                    "gap": "No linked compliance procedure found",
                    "severity": "high",
                })
    
    return gaps


def find_repeated_failures() -> list[dict]:
    """
    Find equipment with repeated failure patterns 
    (same failure mode appearing in multiple work orders/incidents).
    
    This is the core query for the Lessons-Learned agent.
    """
    graph = get_graph_store()
    patterns = []
    
    # Get all failure mode nodes
    failure_modes = graph.get_by_type(NodeType.FAILURE_MODE.value)
    
    for fm in failure_modes:
        fm_id = fm["id"]
        
        # Find all equipment linked to this failure mode
        affected_equipment = []
        for neighbor in graph.get_neighbors(fm_id, direction="in"):
            if neighbor.get("node_type") == NodeType.EQUIPMENT.value:
                affected_equipment.append(neighbor)
        
        if len(affected_equipment) >= 2:
            # Same failure mode across multiple equipment = pattern
            patterns.append({
                "failure_mode": fm,
                "affected_equipment": affected_equipment,
                "occurrence_count": len(affected_equipment),
                "pattern_type": "cross_equipment",
                "severity": "high" if len(affected_equipment) >= 3 else "medium",
            })
        elif len(affected_equipment) == 1:
            # Check if same equipment has multiple work orders for this failure
            equip = affected_equipment[0]
            work_orders = [
                n for n in graph.get_neighbors(equip["id"])
                if n.get("node_type") == NodeType.WORK_ORDER.value
            ]
            
            if len(work_orders) >= 2:
                patterns.append({
                    "failure_mode": fm,
                    "affected_equipment": affected_equipment,
                    "work_orders": work_orders,
                    "occurrence_count": len(work_orders),
                    "pattern_type": "repeated_on_same_equipment",
                    "severity": "high",
                })
    
    return patterns
```

---

## 4.5 Update Graph API Endpoints

Replace stub in `plantmind/api/routes/graph.py`:

```python
"""Knowledge graph query and visualization endpoints."""

from fastapi import APIRouter, HTTPException
from graph.graph_store import get_graph_store
from graph.queries import get_equipment_history, find_compliance_gaps, find_repeated_failures

router = APIRouter()


@router.get("/graph/stats")
async def get_graph_stats():
    """Get knowledge graph statistics."""
    graph = get_graph_store()
    return graph.get_stats()


@router.get("/graph/nodes")
async def get_graph_nodes(node_type: str = None, limit: int = 100):
    """Get nodes from the knowledge graph, optionally filtered by type."""
    graph = get_graph_store()
    
    if node_type:
        nodes = graph.get_by_type(node_type)
    else:
        nodes = [
            {"id": nid, **data}
            for nid, data in list(graph.graph.nodes(data=True))[:limit]
        ]
    
    return {"nodes": nodes[:limit], "total": len(nodes)}


@router.get("/graph/node/{node_id}")
async def get_node_detail(node_id: str):
    """Get a specific node and its neighbors."""
    graph = get_graph_store()
    node = graph.find_node(node_id)
    
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    
    neighbors = graph.get_neighbors(node["id"])
    return {"node": node, "neighbors": neighbors}


@router.get("/graph/traverse/{node_id}")
async def traverse_graph(node_id: str, depth: int = 2):
    """BFS traversal from a node."""
    graph = get_graph_store()
    node = graph.find_node(node_id)
    
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    
    return graph.traverse(node["id"], max_depth=depth)


@router.get("/graph/equipment/{tag}")
async def get_equipment_info(tag: str):
    """Get full equipment history — work orders, incidents, procedures, regulations."""
    return get_equipment_history(tag)


@router.get("/graph/export")
async def export_graph_for_viz():
    """Export the full graph for force-directed visualization."""
    graph = get_graph_store()
    return graph.export_for_visualization()
```

---

## 4.6 Full Ingestion + Graph Loading Script

**File:** `plantmind/scripts/build_graph.py`

```python
"""
Build the full knowledge graph from sample documents.

Run this script to:
1. Process all sample documents through the ingestion pipeline
2. Load entities and relationships into NetworkX graph
3. Embed text chunks into ChromaDB
4. Save the graph to JSON for persistence

Usage:
    cd plantmind
    python -m scripts.build_graph
"""

import sys
import logging
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.pipeline import process_all_documents
from graph.loader import load_all_documents
from graph.graph_store import get_graph_store
from graph.queries import get_equipment_history, find_compliance_gaps, find_repeated_failures
from api.config import SAMPLE_DOCS_DIR, DATA_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


def main():
    print("=" * 60)
    print("PlantMind — Knowledge Graph Builder")
    print("=" * 60)
    
    # Step 1: Process all documents
    print("\n📄 Step 1: Processing documents...")
    doc_outputs = process_all_documents(
        str(SAMPLE_DOCS_DIR),
        output_dir=str(DATA_DIR / "processed"),
    )
    print(f"   Processed {len(doc_outputs)} documents")
    
    # Step 2: Load into graph and vector store
    print("\n🔗 Step 2: Building knowledge graph...")
    stats = load_all_documents(doc_outputs)
    print(f"   Loaded: {stats}")
    
    # Step 3: Print graph statistics
    graph = get_graph_store()
    graph_stats = graph.get_stats()
    print(f"\n📊 Graph Statistics:")
    print(f"   Total nodes: {graph_stats['total_nodes']}")
    print(f"   Total edges: {graph_stats['total_edges']}")
    print(f"   Node types: {graph_stats['node_types']}")
    print(f"   Relationship types: {graph_stats['relationship_types']}")
    print(f"   Connected components: {graph_stats['connected_components']}")
    
    # Step 4: Run verification queries
    print("\n🔍 Verification Queries:")
    
    # Query 1: Equipment history for P-104
    p104 = get_equipment_history("P-104")
    if p104["equipment"]:
        print(f"\n   P-104 History:")
        print(f"   - Work orders: {len(p104['work_orders'])}")
        print(f"   - Failure modes: {[fm.get('name') for fm in p104['failure_modes']]}")
        print(f"   - Documents: {len(p104['documents'])}")
    else:
        print("   ⚠ P-104 not found in graph!")
    
    # Query 2: Compliance gaps
    gaps = find_compliance_gaps()
    print(f"\n   Compliance Gaps: {len(gaps)} found")
    for gap in gaps[:3]:
        print(f"   - {gap['equipment'].get('name', 'N/A')} ↔ {gap['regulation'].get('name', 'N/A')}: {gap['gap']}")
    
    # Query 3: Repeated failures
    patterns = find_repeated_failures()
    print(f"\n   Repeated Failure Patterns: {len(patterns)} found")
    for p in patterns[:3]:
        equip_names = [e.get("name", "N/A") for e in p["affected_equipment"]]
        print(f"   - {p['failure_mode'].get('name', 'N/A')} → {equip_names} ({p['occurrence_count']}x)")
    
    print("\n" + "=" * 60)
    print("✅ Knowledge graph build complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
```

Create the scripts directory `__init__.py`:

**File:** `plantmind/scripts/__init__.py`
```python
"""PlantMind scripts."""
```

---

## 4.7 Verification Gate

**All checks must pass before proceeding to Step 5:**

### Check 1: Build the full graph
```bash
cd "d:\hackathon projects\PlantMind ET\plantmind"
python -m scripts.build_graph
```
**Expected output:**
- Processed 5+ documents
- Graph has 20+ nodes and 30+ edges
- P-104 found with work orders and failure modes
- At least 1 compliance gap detected
- At least 1 repeated failure pattern detected

### Check 2: Query graph via API
```bash
# Start backend
python -m api.main &

# Test graph stats
curl http://localhost:8000/api/v1/graph/stats
# Expected: {"total_nodes": 20+, "total_edges": 30+, ...}

# Test equipment query
curl http://localhost:8000/api/v1/graph/equipment/P-104
# Expected: Equipment node with work_orders, failure_modes, documents

# Test graph export for viz
curl http://localhost:8000/api/v1/graph/export
# Expected: {"nodes": [...], "edges": [...]}
```

### Check 3: Verify cross-document connections
```bash
python -c "
from graph.graph_store import get_graph_store
graph = get_graph_store()
graph.load_from_json('data/knowledge_graph.json')

# P-104 should connect to multiple documents
p104_neighbors = graph.get_neighbors('P-104')
doc_neighbors = [n for n in p104_neighbors if n.get('node_type') == 'Document']
print(f'P-104 appears in {len(doc_neighbors)} documents')
assert len(doc_neighbors) >= 2, 'P-104 should appear in multiple documents'

# C-302 and P-104 should share Seal Failure / misalignment connection pattern
print('✓ Cross-document connections verified')
"
```

### Check 4: Vector store populated
```bash
python -c "
import chromadb
client = chromadb.PersistentClient(path='data/chroma_db')
collection = client.get_collection('plantmind_chunks')
print(f'Vector store: {collection.count()} chunks embedded')
assert collection.count() >= 10, 'Expected at least 10 chunks'

# Test semantic search
results = collection.query(query_texts=['pump vibration problem'], n_results=3)
print(f'Search results for \"pump vibration\": {len(results[\"documents\"][0])} matches')
print(f'Top match: {results[\"documents\"][0][0][:100]}...')
print('✓ Vector store working')
"
```

---

## Output of This Step

After completing Step 4, you should have:
- ✅ Full knowledge graph with 20+ nodes and 30+ edges
- ✅ All entity types populated: Equipment, WorkOrder, Person, Regulation, etc.
- ✅ Cross-document relationships established
- ✅ ChromaDB vector store with embedded text chunks
- ✅ Graph query utilities for equipment history, compliance gaps, repeated failures
- ✅ API endpoints for graph querying and visualization export
- ✅ Graph persistence to JSON
- ✅ `build_graph.py` script for rebuilding from scratch

**→ Proceed to [Step 5 — RAG Copilot Agent](step5_rag_copilot.md)**
