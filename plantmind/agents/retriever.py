"""
Hybrid retriever — combines graph traversal + vector semantic search.

This is the core retrieval engine shared by all agents. It provides
richer context than pure vector search by also pulling graph-connected
entities and their relationships.
"""

import logging
from typing import Optional
from graph.graph_store import get_graph_store
from graph.vector_store import get_local_vector_store
from graph.schema import NodeType

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Retrieval engine that combines:
    1. Vector semantic search (LocalVectorStore) for relevant text chunks
    2. Graph traversal (NetworkX) for related entities and context
    
    The merged context is richer than either source alone.
    """

    def __init__(self):
        self.graph = get_graph_store()
        self._vector_store = None

    @property
    def vector_store(self):
        if self._vector_store is None:
            self._vector_store = get_local_vector_store()
        return self._vector_store

    def retrieve(
        self,
        query: str,
        n_vector_results: int = 5,
        graph_depth: int = 2,
        entity_hints: list[str] = None,
    ) -> dict:
        """
        Hybrid retrieval: vector search + graph traversal.
        
        Args:
            query: Natural language question
            n_vector_results: Number of vector search results
            graph_depth: BFS depth for graph traversal
            entity_hints: Optional list of entity names/tags detected in the query
        
        Returns:
            {
                "vector_results": [...],      # Semantically similar text chunks
                "graph_context": {...},        # Graph traversal results
                "merged_context": str,         # Combined context string for LLM
                "source_documents": [...],     # Unique source documents
                "confidence_signals": {...},   # Retrieval quality indicators
            }
        """
        # 1. Vector semantic search
        vector_results = self._vector_search(query, n_vector_results)
        
        # 2. Extract entity mentions from query (simple approach)
        if entity_hints is None:
            entity_hints = self._extract_entity_hints(query)
        
        # 3. Graph traversal for each mentioned entity
        graph_context = self._graph_search(entity_hints, graph_depth)
        
        # 4. Merge contexts
        merged_context = self._merge_contexts(vector_results, graph_context)
        
        # 5. Collect source documents
        source_docs = self._collect_sources(vector_results, graph_context)
        
        # 6. Calculate confidence signals
        confidence = self._calculate_confidence(vector_results, graph_context)
        
        return {
            "vector_results": vector_results,
            "graph_context": graph_context,
            "merged_context": merged_context,
            "source_documents": source_docs,
            "confidence_signals": confidence,
        }

    def _vector_search(self, query: str, n_results: int) -> list[dict]:
        """Search LocalVectorStore for semantically similar text chunks."""
        try:
            results = self.vector_store.query(
                query_texts=[query],
                n_results=n_results,
            )
            
            chunks = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    chunks.append({
                        "text": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0,
                        "id": results["ids"][0][i] if results["ids"] else "",
                    })
            
            return chunks
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    def _extract_entity_hints(self, query: str) -> list[str]:
        """
        Extract potential entity references from the query text.
        Uses simple pattern matching.
        """
        import re
        
        hints = []
        
        # Look for equipment tag patterns (P-104, HX-201, V-045, C-302, etc.)
        tag_matches = re.findall(r'\b([A-Z]{1,3}-\d{2,4}[A-Z]?)\b', query)
        hints.extend(tag_matches)
        
        # Look for work order patterns (WO-2024-001)
        wo_matches = re.findall(r'\b(WO-\d{4}-\d{3})\b', query)
        hints.extend(wo_matches)
        
        # Look for incident patterns (INC-2024-003)
        inc_matches = re.findall(r'\b(INC-\d{4}-\d{3})\b', query)
        hints.extend(inc_matches)
        
        # Look for regulation patterns (OISD-STD-154)
        reg_matches = re.findall(r'\b(OISD-STD-\d+)\b', query, re.IGNORECASE)
        hints.extend(reg_matches)
        
        # Look for SOP patterns (SOP-SAFE-007)
        sop_matches = re.findall(r'\b(SOP-[A-Z]+-\d+)\b', query, re.IGNORECASE)
        hints.extend(sop_matches)
        
        # Also try to find known node names in the graph
        for word in query.split():
            node = self.graph.find_node(word.strip('?,.:'))
            if node:
                hints.append(node["id"])
        
        return list(set(hints))

    def _graph_search(self, entity_hints: list[str], depth: int) -> dict:
        """Traverse the graph from each hinted entity to build relational context."""
        all_nodes = []
        all_edges = []
        entity_details = []
        
        for hint in entity_hints:
            node = self.graph.find_node(hint)
            if node:
                entity_details.append(node)
                
                # BFS traversal
                subgraph = self.graph.traverse(node["id"], max_depth=depth)
                all_nodes.extend(subgraph["nodes"])
                all_edges.extend(subgraph["edges"])
        
        # Deduplicate nodes
        seen_ids = set()
        unique_nodes = []
        for n in all_nodes:
            if n["id"] not in seen_ids:
                unique_nodes.append(n)
                seen_ids.add(n["id"])
        
        return {
            "matched_entities": entity_details,
            "nodes": unique_nodes,
            "edges": all_edges,
            "entity_count": len(unique_nodes),
            "relationship_count": len(all_edges),
        }

    def _merge_contexts(self, vector_results: list[dict], graph_context: dict) -> str:
        """
        Merge vector search results and graph context into a single 
        context string for the LLM.
        """
        sections = []
        
        # Graph context section
        if graph_context["matched_entities"]:
            sections.append("=== KNOWLEDGE GRAPH CONTEXT ===")
            
            for entity in graph_context["matched_entities"]:
                sections.append(f"\n--- Entity: {entity.get('name', entity['id'])} ({entity.get('node_type', 'Unknown')}) ---")
                
                # Add entity properties
                props = {k: v for k, v in entity.items() if k not in ('id', 'name', 'node_type', 'source_docs')}
                if props:
                    sections.append(f"Properties: {props}")
            
            # Add relationships
            if graph_context["edges"]:
                sections.append("\n--- Relationships ---")
                for edge in graph_context["edges"][:20]:  # Limit to avoid context overflow
                    sections.append(f"  {edge['source']} --[{edge['rel_type']}]--> {edge['target']}")
            
            # Add connected nodes with details
            sections.append("\n--- Connected Entities ---")
            for node in graph_context["nodes"][:15]:
                node_type = node.get("node_type", "Unknown")
                name = node.get("name", node["id"])
                props_str = ""
                relevant_props = {k: v for k, v in node.items() 
                                 if k not in ('id', 'name', 'node_type', 'source_docs', 'direction', 'rel_type')}
                if relevant_props:
                    props_str = f" | {relevant_props}"
                sections.append(f"  [{node_type}] {name}{props_str}")
        
        # Vector search results section
        if vector_results:
            sections.append("\n=== DOCUMENT TEXT MATCHES ===")
            for i, result in enumerate(vector_results):
                doc_info = result["metadata"].get("filename", "unknown")
                sections.append(f"\n--- Match {i+1} (from: {doc_info}) ---")
                sections.append(result["text"])
        
        return "\n".join(sections)

    def _collect_sources(self, vector_results: list[dict], graph_context: dict) -> list[dict]:
        """Collect unique source document references."""
        sources = {}
        
        # From vector results
        for result in vector_results:
            filename = result["metadata"].get("filename", "unknown")
            if filename not in sources:
                sources[filename] = {
                    "filename": filename,
                    "doc_type": result["metadata"].get("doc_type", "unknown"),
                    "relevance_score": 1.0 - result.get("distance", 0),
                    "match_type": "semantic",
                }
        
        # From graph context
        for node in graph_context.get("nodes", []):
            if node.get("node_type") == "Document":
                filename = node.get("name", "unknown")
                if filename not in sources:
                    sources[filename] = {
                        "filename": filename,
                        "doc_type": node.get("doc_type", "unknown"),
                        "relevance_score": 0.8,
                        "match_type": "graph",
                    }
        
        return list(sources.values())

    def _calculate_confidence(self, vector_results: list[dict], graph_context: dict) -> dict:
        """
        Calculate confidence signals for the retrieval quality.
        Higher confidence = more relevant context found.
        """
        signals = {
            "vector_match_count": len(vector_results),
            "graph_entity_count": len(graph_context.get("matched_entities", [])),
            "graph_relationship_count": len(graph_context.get("edges", [])),
            "has_graph_context": len(graph_context.get("matched_entities", [])) > 0,
            "has_vector_context": len(vector_results) > 0,
        }
        
        # Calculate overall confidence score (0-1)
        score = 0.0
        
        if vector_results:
            # Best vector match distance (lower = better match)
            best_distance = min(r.get("distance", 1.0) for r in vector_results)
            vector_score = max(0, 1.0 - best_distance)
            score += vector_score * 0.5
        
        if graph_context.get("matched_entities"):
            graph_score = min(1.0, len(graph_context["matched_entities"]) * 0.3 + 
                            len(graph_context.get("edges", [])) * 0.05)
            score += graph_score * 0.5
        
        signals["overall_confidence"] = round(min(1.0, score), 3)
        
        return signals
