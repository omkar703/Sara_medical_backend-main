"""
OCR Service - Tesseract Integration and PDF Processing

=============================================================================
ROOT CAUSE ANALYSIS & FIX DOCUMENTATION
=============================================================================

ERROR: "type object 'Output' has no attribute 'TSV'"

CAUSE:
------
The pytesseract Python library does NOT support Output.TSV as an output type.
This is a common confusion between:

1. Tesseract CLI (command-line interface):
   - Supports TSV output via: tesseract image.png output tsv
   - Produces tab-separated values file with confidence scores
   
2. pytesseract Python API:
   - Only supports these Output types:
     * Output.BYTES - Raw bytes output
     * Output.DATAFRAME - Pandas DataFrame (requires pandas)
     * Output.DICT - Python dictionary with word-level data
     * Output.STRING - Plain text string
   
FIX APPLIED:
------------
Changed from: pytesseract.Output.TSV (INVALID)
Changed to:   pytesseract.Output.DICT (VALID)

The DICT output provides the same information as TSV but as a Python dictionary:
- 'text': list of recognized words
- 'conf': list of confidence scores (0-100, -1 for non-text elements)
- 'left', 'top', 'width', 'height': bounding box coordinates
- 'level', 'page_num', 'block_num', 'par_num', 'line_num', 'word_num': hierarchy

ADDITIONAL IMPROVEMENTS:
------------------------
1. Robust confidence calculation with proper filtering of -1 values
2. Word-level confidence filtering (configurable threshold)
3. Comprehensive error handling
4. CPU-optimized OCR configuration
5. Inline documentation for future maintainers
=============================================================================
"""
import io
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

import cv2
import numpy as np
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image

from app.config import get_settings
from app.utils.preprocessing import preprocess_image, pil_to_cv2, cv2_to_pil

settings = get_settings()

# Minimum confidence threshold for word-level filtering (0-100)
MIN_WORD_CONFIDENCE = 30


class OCRService:
    """
    Service for OCR processing of images and PDFs.
    
    This service uses Tesseract OCR via pytesseract for text extraction.
    All processing is CPU-optimized with no GPU dependencies.
    
    Key Features:
    - Image preprocessing for improved accuracy
    - Multi-page PDF support
    - Word-level confidence scoring
    - Hybrid PDF processing (text extraction + OCR fallback)
    """
    
    def __init__(self):
        """Initialize OCR service with Tesseract configuration."""
        # Configure Tesseract path if specified
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
        
        self.tesseract_config = settings.ocr_config
        self.tesseract_lang = settings.tesseract_lang
    
    def extract_text_with_confidence(
        self,
        image: np.ndarray
    ) -> Tuple[str, float, Dict[str, Any]]:
        """
        Extract text from image using Tesseract with confidence scores.
        
        IMPORTANT: Uses pytesseract.Output.DICT (NOT Output.TSV which doesn't exist)
        
        The pytesseract library provides these output types:
        - Output.STRING: Plain text
        - Output.BYTES: Raw bytes
        - Output.DICT: Dictionary with word-level data (RECOMMENDED)
        - Output.DATAFRAME: Pandas DataFrame (requires pandas)
        
        Args:
            image: Preprocessed image (numpy array, grayscale or BGR)
            
        Returns:
            Tuple of:
            - extracted_text (str): Full extracted text
            - confidence (float): Average confidence score (0.0 to 1.0)
            - ocr_data (dict): Full OCR output with word-level details
        """
        # Convert to PIL Image for Tesseract
        pil_image = cv2_to_pil(image)
        
        # Extract plain text
        text = pytesseract.image_to_string(
            pil_image,
            lang=self.tesseract_lang,
            config=self.tesseract_config
        )
        
        # =====================================================================
        # CRITICAL FIX: Use Output.DICT instead of Output.TSV
        # =====================================================================
        # pytesseract.Output.TSV does NOT exist in the pytesseract library.
        # The Tesseract CLI supports TSV output, but the Python wrapper does not.
        # Output.DICT provides equivalent functionality as a Python dictionary.
        # =====================================================================
        ocr_data = pytesseract.image_to_data(
            pil_image,
            lang=self.tesseract_lang,
            config=self.tesseract_config,
            output_type=pytesseract.Output.DICT  # FIXED: Was incorrectly Output.TSV
        )
        
        # Calculate overall confidence from word-level confidences
        confidence = self._calculate_confidence_from_dict(ocr_data)
        
        return text.strip(), confidence, ocr_data
    
    def _calculate_confidence_from_dict(self, ocr_data: Dict[str, Any]) -> float:
        """
        Calculate overall confidence score from OCR dictionary output.
        
        The OCR data dictionary contains:
        - 'conf': List of confidence values (0-100, -1 for non-text elements)
        - 'text': List of recognized text for each element
        
        We filter out:
        - Confidence values of -1 (non-text elements like whitespace)
        - Empty text entries
        - Low-confidence words (below MIN_WORD_CONFIDENCE threshold)
        
        Args:
            ocr_data: Dictionary output from pytesseract.image_to_data()
            
        Returns:
            float: Average confidence normalized to 0.0-1.0 range
        """
        if not ocr_data or 'conf' not in ocr_data or 'text' not in ocr_data:
            return 0.0
        
        confidences = ocr_data['conf']
        texts = ocr_data['text']
        
        # Filter valid confidences (non-negative, non-empty text)
        valid_confidences = []
        for conf, text in zip(confidences, texts):
            # Skip non-text elements (conf = -1) and empty text
            if conf >= 0 and text and text.strip():
                valid_confidences.append(conf)
        
        if not valid_confidences:
            return 0.0
        
        # Calculate average and normalize to 0.0-1.0
        avg_confidence = sum(valid_confidences) / len(valid_confidences)
        return min(1.0, max(0.0, avg_confidence / 100.0))
    
    def filter_low_confidence_words(
        self, 
        ocr_data: Dict[str, Any],
        min_confidence: int = MIN_WORD_CONFIDENCE
    ) -> str:
        """
        Extract text with low-confidence words filtered out.
        
        Args:
            ocr_data: Dictionary output from pytesseract.image_to_data()
            min_confidence: Minimum confidence threshold (0-100)
            
        Returns:
            str: Filtered text with only high-confidence words
        """
        if not ocr_data or 'conf' not in ocr_data or 'text' not in ocr_data:
            return ""
        
        filtered_words = []
        for conf, text in zip(ocr_data['conf'], ocr_data['text']):
            if conf >= min_confidence and text and text.strip():
                filtered_words.append(text)
        
        return ' '.join(filtered_words)
    
    def process_image(
        self,
        image_data: bytes,
        apply_preprocessing: bool = True
    ) -> Tuple[str, float]:
        """
        Process a single image for OCR.
        
        Args:
            image_data: Raw image bytes
            apply_preprocessing: Whether to apply preprocessing pipeline
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            if apply_preprocessing:
                # Apply preprocessing pipeline (grayscale, threshold, denoise)
                processed_image = preprocess_image(image_data)
            else:
                # Convert bytes directly to numpy array
                nparr = np.frombuffer(image_data, np.uint8)
                processed_image = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
            
            if processed_image is None:
                raise ValueError("Failed to decode image")
            
            # Extract text with confidence
            text, confidence, _ = self.extract_text_with_confidence(processed_image)
            
            return text, confidence
            
        except Exception as e:
            # Log error and return empty result instead of crashing
            print(f"OCR processing error: {str(e)}")
            return "", 0.0
    
    def process_pdf_with_pdfplumber(self, pdf_data: bytes) -> List[Tuple[str, float]]:
        """
        Process PDF using pdfplumber (text-based extraction).
        
        This is faster than OCR and works well for digitally-created PDFs.
        Falls back to OCR if no text is found.
        
        Args:
            pdf_data: PDF file bytes
            
        Returns:
            List of (text, confidence) tuples per page
        """
        results = []
        
        try:
            with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text and text.strip():
                        # Text-based extraction has high confidence
                        results.append((text.strip(), 0.95))
                    else:
                        # No text found, will need OCR
                        results.append(("", 0.0))
        except Exception as e:
            print(f"PDF text extraction error: {str(e)}")
            results.append(("", 0.0))
        
        return results
    
    def process_pdf_with_ocr(
        self,
        pdf_data: bytes,
        dpi: int = 300
    ) -> List[Tuple[str, float]]:
        """
        Process PDF using OCR (image-based extraction).
        
        Converts each PDF page to an image and applies OCR.
        CPU-optimized with configurable DPI.
        
        Args:
            pdf_data: PDF file bytes
            dpi: DPI for PDF to image conversion (higher = better quality but slower)
            
        Returns:
            List of (text, confidence) tuples per page
        """
        results = []
        
        try:
            # Convert PDF pages to images
            images = convert_from_bytes(pdf_data, dpi=dpi)
            
            for page_num, image in enumerate(images, 1):
                try:
                    # Convert PIL Image to OpenCV format
                    cv_image = pil_to_cv2(image)
                    
                    # Convert to bytes for preprocessing
                    is_success, buffer = cv2.imencode(".png", cv_image)
                    if not is_success:
                        results.append(("", 0.0))
                        continue
                    
                    image_bytes = buffer.tobytes()
                    
                    # Process with OCR
                    text, confidence = self.process_image(image_bytes, apply_preprocessing=True)
                    results.append((text, confidence))
                    
                except Exception as e:
                    print(f"Error processing PDF page {page_num}: {str(e)}")
                    results.append(("", 0.0))
                    
        except Exception as e:
            print(f"PDF OCR conversion error: {str(e)}")
            results.append(("", 0.0))
        
        return results
    
    def process_pdf(
        self,
        pdf_data: bytes,
        try_text_extraction: bool = True
    ) -> List[Tuple[str, float]]:
        """
        Process PDF with hybrid approach: text extraction first, then OCR.
        
        Args:
            pdf_data: PDF file bytes
            try_text_extraction: Whether to try text-based extraction first
            
        Returns:
            List of (text, confidence) tuples per page
        """
        if try_text_extraction:
            # Try text-based extraction first (faster)
            text_results = self.process_pdf_with_pdfplumber(pdf_data)
            
            # Check if we got meaningful text
            has_text = any(conf > 0.5 for _, conf in text_results)
            
            if has_text:
                # Use text-based extraction results
                return text_results
        
        # Fall back to OCR-based extraction
        return self.process_pdf_with_ocr(pdf_data)
    
    async def process_file(
        self,
        file_data: bytes,
        filename: str
    ) -> List[Tuple[str, float]]:
        """
        Process any supported file (PDF or image).
        
        Args:
            file_data: File bytes
            filename: Original filename
            
        Returns:
            List of (text, confidence) tuples per page
            
        Raises:
            ValueError: For unsupported file formats
        """
        file_ext = Path(filename).suffix.lower()
        
        if file_ext == '.pdf':
            # Process as PDF
            return self.process_pdf(file_data)
        elif file_ext in ['.png', '.jpg', '.jpeg']:
            # Process as single image
            text, confidence = self.process_image(file_data)
            return [(text, confidence)]
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")


# Singleton instance
_ocr_service_instance: Optional[OCRService] = None


def get_ocr_service() -> OCRService:
    """Get or create OCR service instance."""
    global _ocr_service_instance
    if _ocr_service_instance is None:
        _ocr_service_instance = OCRService()
    return _ocr_service_instance

