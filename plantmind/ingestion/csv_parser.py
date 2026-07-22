"""Parse structured CSV data (e.g., work orders) into entities and relationships."""

import csv
from pathlib import Path
from io import StringIO
import logging
from ingestion.schemas import (
    DocumentOutput, DocType, ExtractedEntity, EntityType,
    ExtractedRelationship, RelationshipType, TextChunk,
)

logger = logging.getLogger(__name__)


def parse_csv(file_path: str, doc_type: DocType = DocType.WORK_ORDER) -> DocumentOutput:
    """
    Parse a CSV file into structured entities and relationships.
    
    Handles work order CSVs with known column schema.
    Each row becomes a WorkOrder entity with relationships to
    Equipment, Person, and FailureMode entities.
    
    Args:
        file_path: Path to CSV file
        doc_type: Document classification
    
    Returns:
        DocumentOutput with entities, relationships, and text chunks
    """
    path = Path(file_path)
    content = path.read_text(encoding='utf-8')
    
    reader = csv.DictReader(StringIO(content))
    rows = list(reader)
    
    entities = []
    relationships = []
    chunks = []
    seen_entities = set()  # Avoid duplicate entity creation
    
    for i, row in enumerate(rows):
        wo_id = row.get('wo_id', f'WO-{i}')
        equipment_tag = row.get('equipment_tag', '')
        equipment_name = row.get('equipment_name', '')
        assigned_to = row.get('assigned_to', '')
        failure_mode = row.get('failure_mode', '')
        description = row.get('description', '')
        root_cause = row.get('root_cause', '')
        
        # Create WorkOrder entity
        wo_entity = ExtractedEntity(
            name=wo_id,
            entity_type=EntityType.WORK_ORDER,
            properties={
                "date": row.get('date', ''),
                "status": row.get('status', ''),
                "priority": row.get('priority', ''),
                "hours_spent": row.get('hours_spent', ''),
                "description": description,
                "root_cause": root_cause,
            },
            source_text=description,
        )
        entities.append(wo_entity)
        
        # Create Equipment entity (if not already created)
        if equipment_tag and equipment_tag not in seen_entities:
            entities.append(ExtractedEntity(
                name=equipment_tag,
                entity_type=EntityType.EQUIPMENT,
                properties={"full_name": equipment_name},
                source_text=equipment_name,
            ))
            seen_entities.add(equipment_tag)
        
        # Create Person entity (if not already created)
        if assigned_to and assigned_to not in seen_entities:
            entities.append(ExtractedEntity(
                name=assigned_to,
                entity_type=EntityType.PERSON,
                properties={"role": "Maintenance Technician"},
                source_text=assigned_to,
            ))
            seen_entities.add(assigned_to)
        
        # Create FailureMode entity (if applicable and not already created)
        if failure_mode and failure_mode != "None" and failure_mode not in seen_entities:
            entities.append(ExtractedEntity(
                name=failure_mode,
                entity_type=EntityType.FAILURE_MODE,
                properties={},
                source_text=failure_mode,
            ))
            seen_entities.add(failure_mode)
        
        # Relationships
        if equipment_tag:
            relationships.append(ExtractedRelationship(
                source_entity=wo_id,
                target_entity=equipment_tag,
                relationship_type=RelationshipType.MENTIONED_IN,
                properties={"context": "work order for equipment"},
            ))
        
        if assigned_to:
            relationships.append(ExtractedRelationship(
                source_entity=wo_id,
                target_entity=assigned_to,
                relationship_type=RelationshipType.PERFORMED_BY,
            ))
        
        if failure_mode and failure_mode != "None":
            relationships.append(ExtractedRelationship(
                source_entity=equipment_tag,
                target_entity=failure_mode,
                relationship_type=RelationshipType.HAS_FAILURE,
                properties={"work_order": wo_id, "date": row.get('date', '')},
            ))
        
        # Create a text chunk for this row (for vector search)
        row_text = (
            f"Work Order {wo_id} ({row.get('date', '')}): "
            f"{equipment_name} ({equipment_tag}). "
            f"{description} "
            f"Assigned to: {assigned_to}. "
            f"Status: {row.get('status', '')}. Priority: {row.get('priority', '')}. "
            f"Failure Mode: {failure_mode}. Root Cause: {root_cause}."
        )
        chunks.append(TextChunk(
            text=row_text,
            chunk_index=i,
            metadata={"wo_id": wo_id, "equipment_tag": equipment_tag},
        ))
    
    output = DocumentOutput(
        doc_type=doc_type,
        filename=path.name,
        source_path=str(path),
        full_text=content,
        raw_text_chunks=chunks,
        entities=entities,
        relationships=relationships,
        source_metadata={
            "extractor": "csv_parser",
            "row_count": len(rows),
            "columns": list(rows[0].keys()) if rows else [],
            "entity_count": len(entities),
            "relationship_count": len(relationships),
        },
    )
    
    logger.info(f"Parsed {len(rows)} rows → {len(entities)} entities, {len(relationships)} relationships")
    return output
