# Step 3 — Ingestion Pipeline

## Objective
Build modular document processors (PDF, OCR, P&ID, CSV) that all converge on a standardized JSON schema, followed by an LLM-based NER pass to extract entities and relationships.

---

## 3.1 Standardized Output Schema

Every document processor must output this schema. Create this as a Pydantic model.

**File:** `plantmind/ingestion/schemas.py`

```python
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
```

---

## 3.2 Text Chunking Utility

**File:** `plantmind/ingestion/chunker.py`

```python
"""Text chunking utility — splits extracted text into overlapping chunks for embedding."""

from ingestion.schemas import TextChunk


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    doc_id: str = "",
) -> list[TextChunk]:
    """
    Split text into overlapping chunks for vector embedding.
    
    Args:
        text: Full document text
        chunk_size: Target characters per chunk
        chunk_overlap: Overlap between consecutive chunks
        doc_id: Parent document ID for metadata
    
    Returns:
        List of TextChunk objects
    """
    if not text.strip():
        return []
    
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at a sentence boundary
        if end < len(text):
            # Look for sentence-ending punctuation near the boundary
            for boundary_char in ['. ', '.\n', '\n\n', '\n']:
                boundary_pos = text.rfind(boundary_char, start + chunk_size // 2, end + 50)
                if boundary_pos != -1:
                    end = boundary_pos + len(boundary_char)
                    break
        
        chunk_text_content = text[start:end].strip()
        
        if chunk_text_content:
            chunks.append(TextChunk(
                text=chunk_text_content,
                chunk_index=chunk_index,
                start_char=start,
                end_char=end,
                metadata={"doc_id": doc_id},
            ))
            chunk_index += 1
        
        start = end - chunk_overlap
        if start >= len(text):
            break
    
    return chunks
```

---

## 3.3 PDF Text Extractor

**File:** `plantmind/ingestion/pdf_extractor.py`

```python
"""Extract text from text-based PDFs using PyMuPDF."""

import fitz  # PyMuPDF
from pathlib import Path
from ingestion.schemas import DocumentOutput, DocType
from ingestion.chunker import chunk_text
import logging

logger = logging.getLogger(__name__)


def extract_pdf(file_path: str, doc_type: DocType = DocType.UNKNOWN) -> DocumentOutput:
    """
    Extract text content from a PDF file.
    
    Also handles .txt files as plain text for prototype flexibility.
    
    Args:
        file_path: Path to PDF or TXT file
        doc_type: Document classification
    
    Returns:
        DocumentOutput with full_text and raw_text_chunks populated
    """
    path = Path(file_path)
    
    if path.suffix.lower() == '.txt':
        # Handle plain text files
        full_text = path.read_text(encoding='utf-8')
        page_count = 1
    elif path.suffix.lower() == '.pdf':
        # Extract from PDF
        doc = fitz.open(str(path))
        pages = []
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            if page_text.strip():
                pages.append(page_text)
        full_text = "\n\n".join(pages)
        page_count = len(doc)
        doc.close()
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")
    
    if not full_text.strip():
        logger.warning(f"No text extracted from {file_path}")
    
    # Chunk the text
    chunks = chunk_text(full_text, doc_id=path.stem)
    
    output = DocumentOutput(
        doc_type=doc_type,
        filename=path.name,
        source_path=str(path),
        full_text=full_text,
        raw_text_chunks=chunks,
        source_metadata={
            "extractor": "pdf_extractor",
            "page_count": page_count,
            "char_count": len(full_text),
            "chunk_count": len(chunks),
        },
    )
    
    logger.info(f"Extracted {len(full_text)} chars, {len(chunks)} chunks from {path.name}")
    return output
```

---

## 3.4 OCR Processor

**File:** `plantmind/ingestion/ocr_processor.py`

```python
"""OCR processing for scanned documents and images using Tesseract."""

from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance
import pytesseract
import logging
from ingestion.schemas import DocumentOutput, DocType
from ingestion.chunker import chunk_text

logger = logging.getLogger(__name__)


def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Pre-process image for better OCR accuracy.
    
    Steps: grayscale → contrast enhance → sharpen → threshold
    """
    # Convert to grayscale
    img = image.convert('L')
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    
    # Sharpen
    img = img.filter(ImageFilter.SHARPEN)
    
    # Simple threshold to clean up
    img = img.point(lambda x: 0 if x < 128 else 255, '1')
    
    return img


def extract_ocr(file_path: str, doc_type: DocType = DocType.INSPECTION_FORM) -> DocumentOutput:
    """
    Extract text from a scanned document image via OCR.
    
    Args:
        file_path: Path to image file (PNG, JPG, TIFF)
        doc_type: Document classification
    
    Returns:
        DocumentOutput with OCR-extracted text and chunks
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {file_path}")
    
    # Open and preprocess
    image = Image.open(str(path))
    processed = preprocess_image(image)
    
    # Run OCR
    try:
        full_text = pytesseract.image_to_string(processed, config='--oem 3 --psm 6')
    except Exception as e:
        logger.error(f"OCR failed for {path.name}: {e}")
        # Fallback: try without preprocessing
        full_text = pytesseract.image_to_string(image)
    
    if not full_text.strip():
        logger.warning(f"No text extracted via OCR from {file_path}")
    
    # Chunk the text
    chunks = chunk_text(full_text, doc_id=path.stem)
    
    output = DocumentOutput(
        doc_type=doc_type,
        filename=path.name,
        source_path=str(path),
        full_text=full_text,
        raw_text_chunks=chunks,
        source_metadata={
            "extractor": "ocr_processor",
            "image_size": f"{image.width}x{image.height}",
            "char_count": len(full_text),
            "chunk_count": len(chunks),
            "ocr_engine": "tesseract",
        },
        processing_notes=["Text extracted via OCR — may contain recognition errors"],
    )
    
    logger.info(f"OCR extracted {len(full_text)} chars from {path.name}")
    return output
```

---

## 3.5 P&ID Tag Detector

**File:** `plantmind/ingestion/pid_detector.py`

```python
"""P&ID tag detection — OCR-based approach for prototype.

For the prototype, we use OCR to extract text from P&ID images, then 
regex-match equipment tags. A production system would use a trained 
CV model for symbol detection.
"""

import re
from pathlib import Path
from PIL import Image
import pytesseract
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
    Extract equipment tags from a P&ID image using OCR + regex matching.
    
    Args:
        file_path: Path to P&ID image
    
    Returns:
        DocumentOutput with detected equipment entities and connections
    """
    path = Path(file_path)
    image = Image.open(str(path))
    
    # OCR the P&ID
    full_text = pytesseract.image_to_string(image, config='--oem 3 --psm 11')
    
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
            "extractor": "pid_detector",
            "image_size": f"{image.width}x{image.height}",
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
```

---

## 3.6 CSV Parser

**File:** `plantmind/ingestion/csv_parser.py`

```python
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
```

---

## 3.7 LLM-Based NER Extractor

**File:** `plantmind/ingestion/ner_extractor.py`

```python
"""LLM-based Named Entity Recognition and Relationship Extraction.

Uses Google Gemini to extract structured entities and relationships
from document text. This runs AFTER the document-type-specific extractor
to enrich the output with NER-detected entities.
"""

import json
import logging
import google.generativeai as genai
from api.config import GOOGLE_API_KEY
from ingestion.schemas import (
    DocumentOutput, ExtractedEntity, EntityType,
    ExtractedRelationship, RelationshipType,
)

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

NER_PROMPT_TEMPLATE = """You are an industrial document NER (Named Entity Recognition) system.

Analyze the following document text and extract ALL entities and relationships.

ENTITY TYPES to look for:
- Equipment: pumps, valves, compressors, heat exchangers, tanks, columns (look for tags like P-104, HX-201, V-045)
- Person: names of technicians, engineers, managers
- Regulation: regulatory standards (OISD-STD-154, Factory Act sections, PESO, IS codes)
- Procedure: SOPs, work procedures (SOP-SAFE-007, SOP-MAINT-012)
- Incident: incident IDs, accident references (INC-2024-003)
- WorkOrder: work order IDs (WO-2024-001)
- Location: plant areas, units (Unit-3, Area A)
- FailureMode: types of failures (seal failure, vibration, fouling, corrosion)

RELATIONSHIP TYPES to look for:
- MENTIONED_IN: entity is mentioned in this document
- MAINTAINED_BY: equipment is maintained by a person
- GOVERNED_BY: equipment/procedure is governed by a regulation
- CAUSED_BY: incident/failure is caused by something
- PART_OF: equipment is part of a larger system
- PERFORMED_BY: work order is performed by a person
- REFERENCES: document references another document/regulation
- HAS_FAILURE: equipment has a failure mode

Return your response as a JSON object with this EXACT structure:
{{
  "entities": [
    {{
      "name": "entity name or tag",
      "entity_type": "Equipment|Person|Regulation|Procedure|Incident|WorkOrder|Location|FailureMode",
      "properties": {{"key": "value"}},
      "source_text": "the text span where found",
      "confidence": 0.95
    }}
  ],
  "relationships": [
    {{
      "source_entity": "entity name",
      "target_entity": "entity name",
      "relationship_type": "MENTIONED_IN|MAINTAINED_BY|GOVERNED_BY|CAUSED_BY|PART_OF|PERFORMED_BY|REFERENCES|HAS_FAILURE",
      "confidence": 0.9
    }}
  ]
}}

DOCUMENT TEXT:
---
{document_text}
---

Extract all entities and relationships. Be thorough — do not miss any equipment tags, people, or regulatory references. Return ONLY valid JSON."""


def run_ner_extraction(doc_output: DocumentOutput) -> DocumentOutput:
    """
    Run LLM-based NER on a DocumentOutput to extract/enrich entities and relationships.
    
    This merges LLM-extracted entities with any already present (e.g., from CSV parser
    or P&ID detector), deduplicating by entity name.
    
    Args:
        doc_output: Existing DocumentOutput from a document-type-specific extractor
    
    Returns:
        Enriched DocumentOutput with NER-extracted entities and relationships added
    """
    if not GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY not set — skipping NER extraction")
        doc_output.processing_notes.append("NER skipped: no API key")
        return doc_output
    
    # Use a truncated version if text is very long (Gemini context window)
    text_for_ner = doc_output.full_text[:8000]
    
    prompt = NER_PROMPT_TEMPLATE.format(document_text=text_for_ner)
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1,  # Low temperature for factual extraction
            ),
        )
        
        result = json.loads(response.text)
        
        # Merge extracted entities (dedup by name)
        existing_names = {e.name for e in doc_output.entities}
        
        for ent_data in result.get("entities", []):
            if ent_data["name"] not in existing_names:
                try:
                    entity = ExtractedEntity(
                        name=ent_data["name"],
                        entity_type=EntityType(ent_data["entity_type"]),
                        properties=ent_data.get("properties", {}),
                        source_text=ent_data.get("source_text", ""),
                        confidence=ent_data.get("confidence", 0.8),
                    )
                    doc_output.entities.append(entity)
                    existing_names.add(ent_data["name"])
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid entity: {ent_data} — {e}")
        
        # Merge relationships
        for rel_data in result.get("relationships", []):
            try:
                rel = ExtractedRelationship(
                    source_entity=rel_data["source_entity"],
                    target_entity=rel_data["target_entity"],
                    relationship_type=RelationshipType(rel_data["relationship_type"]),
                    confidence=rel_data.get("confidence", 0.8),
                )
                doc_output.relationships.append(rel)
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid relationship: {rel_data} — {e}")
        
        doc_output.processing_notes.append(
            f"NER extracted {len(result.get('entities', []))} entities, "
            f"{len(result.get('relationships', []))} relationships via Gemini"
        )
        
    except Exception as e:
        logger.error(f"NER extraction failed: {e}")
        doc_output.processing_notes.append(f"NER extraction failed: {str(e)}")
    
    return doc_output
```

---

## 3.8 Main Ingestion Pipeline

**File:** `plantmind/ingestion/pipeline.py`

```python
"""Main ingestion pipeline — orchestrates document processing end-to-end."""

import os
import json
import logging
from pathlib import Path
from typing import Optional
from ingestion.schemas import DocumentOutput, DocType
from ingestion.pdf_extractor import extract_pdf
from ingestion.ocr_processor import extract_ocr
from ingestion.pid_detector import extract_pid_tags
from ingestion.csv_parser import parse_csv
from ingestion.ner_extractor import run_ner_extraction

logger = logging.getLogger(__name__)

# Map file extensions and directory names to processing strategies
EXTENSION_MAP = {
    '.pdf': 'pdf',
    '.txt': 'pdf',      # Text files use the same extractor
    '.csv': 'csv',
    '.png': 'image',
    '.jpg': 'image',
    '.jpeg': 'image',
    '.tiff': 'image',
}

# Map directory names to document types
DIR_TYPE_MAP = {
    'maintenance': DocType.MAINTENANCE_RECORD,
    'safety_procedures': DocType.SAFETY_PROCEDURE,
    'inspection_forms': DocType.INSPECTION_FORM,
    'pid_drawings': DocType.PID_DRAWING,
    'regulatory': DocType.REGULATORY,
}


def detect_doc_type(file_path: Path) -> DocType:
    """Infer document type from directory name and filename."""
    parent_dir = file_path.parent.name.lower()
    
    if parent_dir in DIR_TYPE_MAP:
        doc_type = DIR_TYPE_MAP[parent_dir]
        # Refine: check filename for more specific types
        name_lower = file_path.stem.lower()
        if 'incident' in name_lower:
            return DocType.INCIDENT_REPORT
        if 'work_order' in name_lower:
            return DocType.WORK_ORDER
        return doc_type
    
    return DocType.UNKNOWN


def detect_processing_strategy(file_path: Path) -> str:
    """Determine which extractor to use based on file extension and type."""
    ext = file_path.suffix.lower()
    strategy = EXTENSION_MAP.get(ext, 'unknown')
    
    # P&ID images get special handling
    parent_dir = file_path.parent.name.lower()
    if strategy == 'image' and parent_dir == 'pid_drawings':
        return 'pid'
    
    return strategy


def process_single_document(
    file_path: str,
    doc_type: Optional[DocType] = None,
    skip_ner: bool = False,
) -> DocumentOutput:
    """
    Process a single document through the full ingestion pipeline.
    
    Pipeline: detect type → extract content → NER enrichment
    
    Args:
        file_path: Path to the document file
        doc_type: Override document type (auto-detected if None)
        skip_ner: Skip LLM-based NER extraction
    
    Returns:
        Fully processed DocumentOutput
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")
    
    # Detect document type and processing strategy
    if doc_type is None:
        doc_type = detect_doc_type(path)
    
    strategy = detect_processing_strategy(path)
    
    logger.info(f"Processing {path.name} | type={doc_type.value} | strategy={strategy}")
    
    # Step 1: Extract content using appropriate extractor
    if strategy == 'pdf':
        doc_output = extract_pdf(str(path), doc_type)
    elif strategy == 'csv':
        doc_output = parse_csv(str(path), doc_type)
    elif strategy == 'pid':
        doc_output = extract_pid_tags(str(path))
    elif strategy == 'image':
        doc_output = extract_ocr(str(path), doc_type)
    else:
        raise ValueError(f"No extractor available for {path.suffix} files")
    
    # Step 2: Run NER enrichment (unless skipped or CSV which already has structured entities)
    if not skip_ner and strategy != 'csv':
        doc_output = run_ner_extraction(doc_output)
    
    logger.info(
        f"Completed {path.name}: "
        f"{len(doc_output.entities)} entities, "
        f"{len(doc_output.relationships)} relationships, "
        f"{len(doc_output.raw_text_chunks)} chunks"
    )
    
    return doc_output


def process_all_documents(
    docs_dir: str,
    output_dir: Optional[str] = None,
    skip_ner: bool = False,
) -> list[DocumentOutput]:
    """
    Process all documents in the sample_docs directory.
    
    Args:
        docs_dir: Path to the sample_docs directory
        output_dir: Optional directory to save JSON outputs
        skip_ner: Skip LLM-based NER extraction
    
    Returns:
        List of processed DocumentOutputs
    """
    docs_path = Path(docs_dir)
    results = []
    errors = []
    
    # Walk all subdirectories
    for root, dirs, files in os.walk(str(docs_path)):
        for filename in files:
            file_path = Path(root) / filename
            
            # Skip hidden files and non-document files
            if filename.startswith('.') or filename.startswith('__'):
                continue
            
            try:
                result = process_single_document(str(file_path), skip_ner=skip_ner)
                results.append(result)
                
                # Optionally save JSON output
                if output_dir:
                    out_path = Path(output_dir) / f"{file_path.stem}_output.json"
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    out_path.write_text(
                        result.model_dump_json(indent=2),
                        encoding='utf-8',
                    )
                    
            except Exception as e:
                logger.error(f"Failed to process {filename}: {e}")
                errors.append({"file": filename, "error": str(e)})
    
    logger.info(f"Batch processing complete: {len(results)} succeeded, {len(errors)} failed")
    if errors:
        logger.warning(f"Failed documents: {errors}")
    
    return results
```

---

## 3.9 Wire Up the Ingest API Endpoint

Update `plantmind/api/routes/ingest.py` to replace the stub with the real pipeline:

```python
"""Document ingestion endpoints — connected to the real pipeline."""

import shutil
import tempfile
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
from api.config import SAMPLE_DOCS_DIR, DATA_DIR
from ingestion.pipeline import process_single_document, process_all_documents

router = APIRouter()


class IngestResponse(BaseModel):
    doc_id: str
    doc_type: str
    entities_extracted: int
    relationships_extracted: int
    chunks_created: int
    status: str
    processing_notes: list[str] = []


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    doc_type: Optional[str] = None,
):
    """Ingest a single uploaded document into the knowledge graph."""
    # Save uploaded file to temp location
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    
    try:
        result = process_single_document(tmp_path)
        return IngestResponse(
            doc_id=result.doc_id,
            doc_type=result.doc_type.value,
            entities_extracted=len(result.entities),
            relationships_extracted=len(result.relationships),
            chunks_created=len(result.raw_text_chunks),
            status="success",
            processing_notes=result.processing_notes,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.post("/ingest/batch")
async def ingest_batch(skip_ner: bool = False):
    """Ingest all documents in the sample_docs directory."""
    output_dir = str(DATA_DIR / "processed")
    
    try:
        results = process_all_documents(
            str(SAMPLE_DOCS_DIR),
            output_dir=output_dir,
            skip_ner=skip_ner,
        )
        return {
            "status": "success",
            "documents_processed": len(results),
            "total_entities": sum(len(r.entities) for r in results),
            "total_relationships": sum(len(r.relationships) for r in results),
            "total_chunks": sum(len(r.raw_text_chunks) for r in results),
            "documents": [
                {
                    "doc_id": r.doc_id,
                    "filename": r.filename,
                    "doc_type": r.doc_type.value,
                    "entities": len(r.entities),
                    "relationships": len(r.relationships),
                    "chunks": len(r.raw_text_chunks),
                }
                for r in results
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 3.10 Verification Gate

**All checks must pass before proceeding to Step 4:**

### Check 1: Unit test each extractor individually

```bash
cd "d:\hackathon projects\PlantMind ET\plantmind"
python -c "
from ingestion.csv_parser import parse_csv
result = parse_csv('data/sample_docs/maintenance/work_orders.csv')
print(f'CSV: {len(result.entities)} entities, {len(result.relationships)} rels')
assert len(result.entities) > 0, 'No entities extracted from CSV'
print('✓ CSV parser works')
"
```

### Check 2: PDF extractor
```bash
python -c "
from ingestion.pdf_extractor import extract_pdf
result = extract_pdf('data/sample_docs/maintenance/maintenance_report_P104.txt')
print(f'PDF: {len(result.raw_text_chunks)} chunks, {len(result.full_text)} chars')
assert len(result.full_text) > 100, 'Insufficient text extracted'
print('✓ PDF extractor works')
"
```

### Check 3: Full batch processing (without NER to test extractors only)
```bash
python -c "
from ingestion.pipeline import process_all_documents
results = process_all_documents('data/sample_docs', skip_ner=True)
print(f'Processed {len(results)} documents')
for r in results:
    print(f'  {r.filename}: {len(r.entities)} entities, {len(r.raw_text_chunks)} chunks')
assert len(results) >= 5, 'Expected at least 5 documents'
print('✓ Batch processing works')
"
```

### Check 4: Full batch with NER (requires GOOGLE_API_KEY)
```bash
python -c "
from ingestion.pipeline import process_all_documents
results = process_all_documents('data/sample_docs', output_dir='data/processed')
total_entities = sum(len(r.entities) for r in results)
print(f'Total entities extracted: {total_entities}')
assert total_entities > 20, 'Expected more entities with NER'
print('✓ NER enrichment works')
"
```

### Check 5: Verify against ground truth
Manually check that these key entities were extracted:
- [ ] `P-104` (Equipment) — from work_orders.csv, maintenance_report, SOP, P&ID
- [ ] `C-302` (Equipment) — from work_orders.csv, incident_report, SOP
- [ ] `V-045` (Equipment) — from work_orders.csv, inspection form, SOP
- [ ] `John Patel` (Person) — from work_orders.csv, inspection form
- [ ] `OISD-STD-154` (Regulation) — from maintenance_report, SOP, regulatory doc
- [ ] `Seal Failure` (FailureMode) — from work_orders.csv, incident_report
- [ ] `WO-2024-003` (WorkOrder) — from work_orders.csv

### Check 6: API endpoint test
```bash
curl -X POST http://localhost:8000/api/v1/ingest/batch
```
**Expected:** JSON response with `documents_processed >= 5`

---

## Output of This Step

After completing Step 3, you should have:
- ✅ 5 working extractors: PDF, OCR, P&ID, CSV, NER
- ✅ Standardized DocumentOutput schema used by all extractors
- ✅ Text chunking with overlap for vector embedding
- ✅ LLM-based NER enrichment via Gemini
- ✅ Batch processing pipeline for the full corpus
- ✅ JSON outputs saved to `data/processed/`
- ✅ Key entities verified against ground truth

**→ Proceed to [Step 4 — Knowledge Graph Construction](step4_knowledge_graph.md)**
