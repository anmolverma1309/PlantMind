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
