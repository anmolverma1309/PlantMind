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
