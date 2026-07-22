"""
Build the full knowledge graph from sample documents.

Run this script to:
1. Process all sample documents through the ingestion pipeline
2. Load entities and relationships into NetworkX graph
3. Embed text chunks into LocalVectorStore
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
    print("\n[Doc] Step 1: Processing documents...")
    doc_outputs = process_all_documents(
        str(SAMPLE_DOCS_DIR),
        output_dir=str(DATA_DIR / "processed"),
    )
    print(f"   Processed {len(doc_outputs)} documents")
    
    # Step 2: Load into graph and vector store
    print("\n[Link] Step 2: Building knowledge graph...")
    stats = load_all_documents(doc_outputs)
    print(f"   Loaded: {stats}")
    
    # Step 3: Print graph statistics
    graph = get_graph_store()
    graph_stats = graph.get_stats()
    print(f"\n[Stats] Graph Statistics:")
    print(f"   Total nodes: {graph_stats['total_nodes']}")
    print(f"   Total edges: {graph_stats['total_edges']}")
    print(f"   Node types: {graph_stats['node_types']}")
    print(f"   Relationship types: {graph_stats['relationship_types']}")
    print(f"   Connected components: {graph_stats['connected_components']}")
    
    # Step 4: Run verification queries
    print("\n[Query] Verification Queries:")
    
    # Query 1: Equipment history for P-104
    p104 = get_equipment_history("P-104")
    if p104["equipment"]:
        print(f"\n   P-104 History:")
        print(f"   - Work orders: {len(p104['work_orders'])}")
        print(f"   - Failure modes: {[fm.get('name') for fm in p104['failure_modes']]}")
        print(f"   - Documents: {len(p104['documents'])}")
    else:
        print("   [WARN] P-104 not found in graph!")
    
    # Query 2: Compliance gaps
    gaps = find_compliance_gaps()
    print(f"\n   Compliance Gaps: {len(gaps)} found")
    for gap in gaps[:3]:
        print(f"   - {gap['equipment'].get('name', 'N/A')} <-> {gap['regulation'].get('name', 'N/A')}: {gap['gap']}")
    
    # Query 3: Repeated failures
    patterns = find_repeated_failures()
    print(f"\n   Repeated Failure Patterns: {len(patterns)} found")
    for p in patterns[:3]:
        equip_names = [e.get("name", "N/A") for e in p["affected_equipment"]]
        print(f"   - {p['failure_mode'].get('name', 'N/A')} -> {equip_names} ({p['occurrence_count']}x)")
    
    print("\n" + "=" * 60)
    print("[OK] Knowledge graph build complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
