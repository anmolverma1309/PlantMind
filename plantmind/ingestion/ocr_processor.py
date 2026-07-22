"""OCR processing for scanned documents and images using Tesseract."""

from pathlib import Path
try:
    from PIL import Image, ImageFilter, ImageEnhance
except ImportError:
    Image = None
try:
    import pytesseract
except ImportError:
    pytesseract = None
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
    Extract text from a scanned document image via OCR, or load directly if it is a text mockup.
    
    Args:
        file_path: Path to image file or txt mockup
        doc_type: Document classification
    
    Returns:
        DocumentOutput with OCR-extracted text and chunks
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    # Support text files directly to mock scans for hackathon robustness
    if path.suffix.lower() == '.txt':
        full_text = path.read_text(encoding='utf-8')
        chunks = chunk_text(full_text, doc_id=path.stem)
        output = DocumentOutput(
            doc_type=doc_type,
            filename=path.name,
            source_path=str(path),
            full_text=full_text,
            raw_text_chunks=chunks,
            source_metadata={
                "extractor": "ocr_processor_mock",
                "char_count": len(full_text),
                "chunk_count": len(chunks),
            },
            processing_notes=["Text mock loaded directly in place of OCR scan"],
        )
        logger.info(f"Mock OCR loaded {len(full_text)} chars from {path.name}")
        return output
    
    # Open and preprocess image
    image = Image.open(str(path))
    processed = preprocess_image(image)
    
    # Run OCR
    try:
        full_text = pytesseract.image_to_string(processed, config='--oem 3 --psm 6')
    except Exception as e:
        logger.error(f"OCR failed for {path.name}: {e}")
        # Fallback: try without preprocessing
        try:
            full_text = pytesseract.image_to_string(image)
        except Exception as e_inner:
            logger.error(f"Fallback OCR failed: {e_inner}")
            full_text = ""
    
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
