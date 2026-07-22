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
