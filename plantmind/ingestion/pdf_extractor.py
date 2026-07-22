"""Extract text from text-based PDFs using PyMuPDF."""

try:
    import fitz  # PyMuPDF — optional, only needed for real PDF parsing
except ImportError:
    fitz = None
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
        if fitz is None:
            raise ImportError("PyMuPDF (fitz) is not installed. Install with: pip install PyMuPDF")
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
