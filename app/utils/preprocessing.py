"""
Image Preprocessing Utilities for OCR
"""
import cv2
import numpy as np
from PIL import Image


def grayscale_conversion(image: np.ndarray) -> np.ndarray:
    """
    Convert image to grayscale
    
    Args:
        image: Input image (BGR format)
        
    Returns:
        Grayscale image
    """
    if len(image.shape) == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


def adaptive_threshold(image: np.ndarray) -> np.ndarray:
    """
    Apply adaptive thresholding for better OCR
    
    Args:
        image: Grayscale image
        
    Returns:
        Thresholded binary image
    """
    # Apply Gaussian adaptive thresholding
    return cv2.adaptiveThreshold(
        image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,  # Block size
        2    # Constant subtracted from mean
    )


def deskew(image: np.ndarray) -> np.ndarray:
    """
    Auto-detect and correct page skew
    
    Args:
        image: Binary or grayscale image
        
    Returns:
        Deskewed image
    """
    # Calculate skew angle
    coords = np.column_stack(np.where(image > 0))
    if len(coords) == 0:
        return image
    
    angle = cv2.minAreaRect(coords)[-1]
    
    # Adjust angle
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    
    # Only deskew if angle is significant (> 0.5 degrees)
    if abs(angle) < 0.5:
        return image
    
    # Rotate image
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image,
        M,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    
    return rotated


def noise_removal(image: np.ndarray) -> np.ndarray:
    """
    Remove noise using morphological operations
    
    Args:
        image: Binary or grayscale image
        
    Returns:
        Denoised image
    """
    # Apply morphological opening (erosion followed by dilation)
    kernel = np.ones((1, 1), np.uint8)
    opening = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
    
    # Median filtering for additional noise reduction
    denoised = cv2.medianBlur(opening, 3)
    
    return denoised


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Enhance image contrast using CLAHE
    
    Args:
        image: Grayscale image
        
    Returns:
        Contrast-enhanced image
    """
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(image)


def resize_for_ocr(image: np.ndarray, target_dpi: int = 300) -> np.ndarray:
    """
    Resize image to optimal DPI for OCR (typically 300 DPI)
    
    Args:
        image: Input image
        target_dpi: Target DPI (default 300)
        
    Returns:
        Resized image
    """
    # Calculate scaling factor based on current size
    # Assuming original is 72 DPI if not specified
    scale_factor = target_dpi / 72
    
    # Only upscale if image is small
    height, width = image.shape[:2]
    if width < 1000 or height < 1000:
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
    
    return image


def preprocess_image(
    image_data: bytes,
    apply_deskew: bool = True,
    apply_denoising: bool = True,
    enhance: bool = True
) -> np.ndarray:
    """
    Main preprocessing pipeline for OCR
    
    Args:
        image_data: Raw image bytes
        apply_deskew: Whether to apply deskewing
        apply_denoising: Whether to apply noise removal
        enhance: Whether to enhance contrast
        
    Returns:
        Preprocessed image ready for OCR
    """
    # Convert bytes to numpy array
    nparr = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        raise ValueError("Failed to decode image")
    
    # Step 1: Convert to grayscale
    gray = grayscale_conversion(image)
    
    # Step 2: Enhance contrast
    if enhance:
        gray = enhance_contrast(gray)
    
    # Step 3: Resize for optimal OCR
    gray = resize_for_ocr(gray)
    
    # Step 4: Apply adaptive thresholding
    binary = adaptive_threshold(gray)
    
    # Step 5: Deskew if requested
    if apply_deskew:
        binary = deskew(binary)
    
    # Step 6: Remove noise if requested
    if apply_denoising:
        binary = noise_removal(binary)
    
    return binary


def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
    """
    Convert PIL Image to OpenCV format
    
    Args:
        pil_image: PIL Image object
        
    Returns:
        OpenCV image (numpy array)
    """
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)


def cv2_to_pil(cv2_image: np.ndarray) -> Image.Image:
    """
    Convert OpenCV image to PIL format
    
    Args:
        cv2_image: OpenCV image (numpy array)
        
    Returns:
        PIL Image object
    """
    if len(cv2_image.shape) == 2:  # Grayscale
        return Image.fromarray(cv2_image)
    else:  # Color
        return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))
