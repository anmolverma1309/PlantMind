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
if GOOGLE_API_KEY:
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
