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
