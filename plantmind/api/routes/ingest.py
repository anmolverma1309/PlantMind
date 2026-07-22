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
