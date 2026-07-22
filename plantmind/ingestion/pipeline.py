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
    '.txt': 'pdf',      # Text files use the same extractor by default
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
    parent_dir = file_path.parent.name.lower()
    
    # Special: if it is a txt mockup of P&ID or Inspection scan, route it correctly
    if ext == '.txt' and parent_dir == 'pid_drawings':
        return 'pid'
    if ext == '.txt' and parent_dir == 'inspection_forms':
        return 'image' # Runs through extract_ocr with text mockup loading
        
    strategy = EXTENSION_MAP.get(ext, 'unknown')
    
    # P&ID images get special handling
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
