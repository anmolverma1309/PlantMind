"""Standardized document ingestion output schema."""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class DocType(str, Enum):
    MAINTENANCE_RECORD = "maintenance_record"
    WORK_ORDER = "work_order"
    SAFETY_PROCEDURE = "safety_procedure"
    INSPECTION_FORM = "inspection_form"
    PID_DRAWING = "pid_drawing"
    REGULATORY = "regulatory"
    INCIDENT_REPORT = "incident_report"
    UNKNOWN = "unknown"


class EntityType(str, Enum):
    EQUIPMENT = "Equipment"
    DOCUMENT = "Document"
    PROCEDURE = "Procedure"
    INCIDENT = "Incident"
    REGULATION = "Regulation"
    PERSON = "Person"
    WORK_ORDER = "WorkOrder"
    LOCATION = "Location"
    FAILURE_MODE = "FailureMode"


class RelationshipType(str, Enum):
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


class ExtractedEntity(BaseModel):
    entity_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    entity_type: EntityType
    properties: dict = Field(default_factory=dict)
    source_text: str = ""  # The text span where this entity was found
    confidence: float = 1.0


class ExtractedRelationship(BaseModel):
    source_entity: str  # entity name or ID
    target_entity: str  # entity name or ID
    relationship_type: RelationshipType
    properties: dict = Field(default_factory=dict)
    confidence: float = 1.0


class TextChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    text: str
    chunk_index: int
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    metadata: dict = Field(default_factory=dict)


class DocumentOutput(BaseModel):
    """Standardized output from any ingestion processor."""
    doc_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    doc_type: DocType
    filename: str
    source_path: str
    entities: list[ExtractedEntity] = Field(default_factory=list)
    relationships: list[ExtractedRelationship] = Field(default_factory=list)
    raw_text_chunks: list[TextChunk] = Field(default_factory=list)
    full_text: str = ""
    source_metadata: dict = Field(default_factory=dict)
    processed_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    processing_notes: list[str] = Field(default_factory=list)
