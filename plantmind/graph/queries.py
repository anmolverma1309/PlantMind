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
