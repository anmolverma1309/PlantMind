"""P&ID tag detection — OCR-based approach for prototype.

For the prototype, we use OCR to extract text from P&ID drawings (or read the text file mock directly), then 
regex-match equipment tags. A production system would use a trained 
CV model for symbol detection.
"""

import re
from pathlib import Path
try:
    from PIL import Image
except ImportError:
    Image = None
try:
    import pytesseract
except ImportError:
    pytesseract = None
import logging
from ingestion.schemas import (
    DocumentOutput, DocType, ExtractedEntity, EntityType,
    ExtractedRelationship, RelationshipType,
)
from ingestion.chunker import chunk_text

logger = logging.getLogger(__name__)

# Equipment tag patterns commonly found in P&IDs
TAG_PATTERNS = [
    (r'\b([A-Z]{1,3}-\d{2,4}[A-Z]?)\b', "generic"),          # P-104, HX-201, V-045
    (r'\b(TK-\d{2,4})\b', "tank"),                              # TK-001
    (r'\b(DC-\d{2,4})\b', "distillation_column"),               # DC-01
    (r'\b(CP-\d{2,4})\b', "control_panel"),                     # CP-03
    (r'\b(GDS-\d{2,4})\b', "gas_detection"),                    # GDS-07
    (r'\b(CL-\d{2,4})\b', "process_line"),                      # CL-015
]

# Equipment type inference from tag prefix
TAG_TYPE_MAP = {
    'P': 'Pump',
    'HX': 'Heat Exchanger',
    'C': 'Compressor',
    'V': 'Valve',
    'TK': 'Tank',
    'DC': 'Distillation Column',
    'CP': 'Control Panel',
    'GDS': 'Gas Detection System',
    'CL': 'Process Line',
    'AP': 'Assembly Point',
}


def infer_equipment_type(tag: str) -> str:
    """Infer equipment type from tag prefix."""
    prefix = re.match(r'^([A-Z]+)', tag)
    if prefix:
        return TAG_TYPE_MAP.get(prefix.group(1), "Unknown Equipment")
    return "Unknown Equipment"


def extract_pid_tags(file_path: str) -> DocumentOutput:
    """
    Extract equipment tags from a P&ID image (or text file mock) using OCR/text + regex matching.
    
    Args:
        file_path: Path to P&ID image or txt mock
    
    Returns:
        DocumentOutput with detected equipment entities and connections
    """
    path = Path(file_path)
    
    # Support text file mockups for robust deployment
    if path.suffix.lower() == '.txt':
        full_text = path.read_text(encoding='utf-8')
        image_metadata = {"extractor": "pid_detector_mock"}
    else:
        image = Image.open(str(path))
        image_metadata = {
            "extractor": "pid_detector",
            "image_size": f"{image.width}x{image.height}",
        }
        # OCR the P&ID
        try:
            full_text = pytesseract.image_to_string(image, config='--oem 3 --psm 11')
        except Exception as e:
            logger.error(f"P&ID OCR failed: {e}")
            full_text = ""
    
    # Find all equipment tags
    found_tags = set()
    for pattern, _ in TAG_PATTERNS:
        matches = re.findall(pattern, full_text)
        found_tags.update(matches)
    
    # Create entities for each detected tag
    entities = []
    for tag in sorted(found_tags):
        eq_type = infer_equipment_type(tag)
        entities.append(ExtractedEntity(
            name=tag,
            entity_type=EntityType.EQUIPMENT,
            properties={
                "equipment_type": eq_type,
                "detected_in": "P&ID",
                "detection_method": "OCR + regex",
            },
            source_text=tag,
            confidence=0.85,  # OCR-based detection has moderate confidence
        ))
    
    # Create PART_OF relationships (all equipment belongs to the P&ID/unit)
    relationships = []
    for entity in entities:
        relationships.append(ExtractedRelationship(
            source_entity=entity.name,
            target_entity="Unit-3",
            relationship_type=RelationshipType.PART_OF,
            confidence=0.9,
        ))
    
    chunks = chunk_text(full_text, doc_id=path.stem)
    
    output = DocumentOutput(
        doc_type=DocType.PID_DRAWING,
        filename=path.name,
        source_path=str(path),
        full_text=full_text,
        raw_text_chunks=chunks,
        entities=entities,
        relationships=relationships,
        source_metadata={
            **image_metadata,
            "tags_detected": len(found_tags),
            "detection_method": "OCR + regex (prototype)",
        },
        processing_notes=[
            "P&ID tag detection uses OCR + regex matching (prototype approach)",
            "Production system should use trained CV model for symbol detection",
            f"Detected {len(found_tags)} equipment tags",
        ],
    )
    
    logger.info(f"Detected {len(found_tags)} tags in P&ID: {sorted(found_tags)}")
    return output
