#!/usr/bin/env python3
"""
OCR Pipeline Automated Test Script

This script iterates through all images in the data/ folder and performs:
1. Image quality analysis (resolution, contrast, noise estimation)
2. OCR extraction using the fixed pipeline
3. Confidence scoring and reporting
4. Summary statistics for the entire batch

Usage:
    # Inside Docker container:
    docker exec healthcare_api python /app/scripts/test_ocr_pipeline.py
    
    # Or copy to container and run:
    docker cp scripts/test_ocr_pipeline.py healthcare_api:/app/
    docker exec healthcare_api python /app/test_ocr_pipeline.py
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict

import cv2
import numpy as np
from PIL import Image

# Add app to path for imports
sys.path.insert(0, '/app')

from app.services.ocr_service import get_ocr_service, OCRService
from app.utils.preprocessing import preprocess_image


@dataclass
class ImageAnalysis:
    """Analysis results for a single image."""
    filename: str
    resolution: Tuple[int, int]
    dpi_estimate: int
    contrast_score: float
    noise_level: float
    orientation: str
    text_density: str
    file_size_kb: float


@dataclass
class OCRResult:
    """OCR result for a single image."""
    filename: str
    success: bool
    text_length: int
    word_count: int
    confidence: float
    processing_time_ms: float
    error: str = ""
    sample_text: str = ""


def analyze_image(image_path: str) -> ImageAnalysis:
    """
    Analyze image quality characteristics.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        ImageAnalysis with quality metrics
    """
    filename = os.path.basename(image_path)
    file_size_kb = os.path.getsize(image_path) / 1024
    
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        return ImageAnalysis(
            filename=filename,
            resolution=(0, 0),
            dpi_estimate=0,
            contrast_score=0.0,
            noise_level=0.0,
            orientation="unknown",
            text_density="unknown",
            file_size_kb=file_size_kb
        )
    
    height, width = img.shape[:2]
    
    # Convert to grayscale for analysis
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Estimate DPI (assuming letter size paper 8.5x11 inches)
    dpi_estimate = int(max(width / 8.5, height / 11))
    
    # Calculate contrast score (standard deviation of pixel values)
    contrast_score = float(np.std(gray) / 128.0)  # Normalized 0-2
    
    # Estimate noise level using Laplacian variance
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    noise_level = min(1.0, laplacian_var / 10000.0)
    
    # Determine orientation
    orientation = "landscape" if width > height else "portrait"
    
    # Estimate text density based on edge detection
    edges = cv2.Canny(gray, 50, 150)
    edge_ratio = np.sum(edges > 0) / (width * height)
    if edge_ratio > 0.1:
        text_density = "high"
    elif edge_ratio > 0.05:
        text_density = "medium"
    else:
        text_density = "low"
    
    return ImageAnalysis(
        filename=filename,
        resolution=(width, height),
        dpi_estimate=dpi_estimate,
        contrast_score=round(contrast_score, 3),
        noise_level=round(noise_level, 3),
        orientation=orientation,
        text_density=text_density,
        file_size_kb=round(file_size_kb, 2)
    )


def process_single_image(ocr_service: OCRService, image_path: str) -> OCRResult:
    """
    Process a single image with OCR.
    
    Args:
        ocr_service: Initialized OCR service
        image_path: Path to the image file
        
    Returns:
        OCRResult with extraction details
    """
    filename = os.path.basename(image_path)
    
    try:
        # Read image bytes
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Time the OCR process
        start_time = time.time()
        text, confidence = ocr_service.process_image(image_data, apply_preprocessing=True)
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Calculate metrics
        word_count = len(text.split()) if text else 0
        sample_text = text[:200] + "..." if len(text) > 200 else text
        
        return OCRResult(
            filename=filename,
            success=True,
            text_length=len(text),
            word_count=word_count,
            confidence=round(confidence, 4),
            processing_time_ms=round(processing_time_ms, 2),
            sample_text=sample_text.replace('\n', ' ')
        )
        
    except Exception as e:
        return OCRResult(
            filename=filename,
            success=False,
            text_length=0,
            word_count=0,
            confidence=0.0,
            processing_time_ms=0.0,
            error=str(e)
        )


def run_ocr_tests(data_dir: str, limit: int = None) -> Dict[str, Any]:
    """
    Run OCR tests on all images in the data directory.
    
    Args:
        data_dir: Path to directory containing images
        limit: Optional limit on number of images to process
        
    Returns:
        Dictionary with test results and statistics
    """
    print("=" * 70)
    print("OCR PIPELINE AUTOMATED TEST")
    print("=" * 70)
    
    # Initialize OCR service
    print("\n[1] Initializing OCR service...")
    ocr_service = get_ocr_service()
    print("    ✓ OCR service initialized")
    
    # Find all images
    print(f"\n[2] Scanning {data_dir} for images...")
    image_extensions = {'.png', '.jpg', '.jpeg'}
    image_files = []
    
    for filename in os.listdir(data_dir):
        ext = Path(filename).suffix.lower()
        if ext in image_extensions:
            image_files.append(os.path.join(data_dir, filename))
    
    total_images = len(image_files)
    if limit:
        image_files = image_files[:limit]
    
    print(f"    Found {total_images} images, processing {len(image_files)}")
    
    # Analyze and process images
    print("\n[3] Processing images...")
    print("-" * 70)
    
    analyses = []
    results = []
    
    for i, image_path in enumerate(image_files, 1):
        filename = os.path.basename(image_path)
        print(f"    [{i:3d}/{len(image_files)}] {filename[:50]}...", end=" ")
        
        # Analyze image quality
        analysis = analyze_image(image_path)
        analyses.append(analysis)
        
        # Run OCR
        result = process_single_image(ocr_service, image_path)
        results.append(result)
        
        # Print status
        if result.success:
            print(f"✓ conf={result.confidence:.2f}, words={result.word_count}")
        else:
            print(f"✗ ERROR: {result.error[:30]}")
    
    print("-" * 70)
    
    # Calculate statistics
    print("\n[4] Calculating statistics...")
    
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    if successful:
        avg_confidence = sum(r.confidence for r in successful) / len(successful)
        avg_processing_time = sum(r.processing_time_ms for r in successful) / len(successful)
        avg_word_count = sum(r.word_count for r in successful) / len(successful)
        total_words = sum(r.word_count for r in successful)
        
        # Confidence distribution
        high_conf = len([r for r in successful if r.confidence >= 0.8])
        med_conf = len([r for r in successful if 0.5 <= r.confidence < 0.8])
        low_conf = len([r for r in successful if r.confidence < 0.5])
    else:
        avg_confidence = 0
        avg_processing_time = 0
        avg_word_count = 0
        total_words = 0
        high_conf = med_conf = low_conf = 0
    
    stats = {
        "total_images": len(image_files),
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": round(len(successful) / len(image_files) * 100, 2) if image_files else 0,
        "avg_confidence": round(avg_confidence, 4),
        "avg_processing_time_ms": round(avg_processing_time, 2),
        "avg_word_count": round(avg_word_count, 1),
        "total_words_extracted": total_words,
        "confidence_distribution": {
            "high_80_100": high_conf,
            "medium_50_80": med_conf,
            "low_0_50": low_conf
        }
    }
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST RESULTS SUMMARY")
    print("=" * 70)
    print(f"  Total images processed: {stats['total_images']}")
    print(f"  Successful:             {stats['successful']} ({stats['success_rate']:.1f}%)")
    print(f"  Failed:                 {stats['failed']}")
    print(f"  Average confidence:     {stats['avg_confidence']:.2%}")
    print(f"  Average processing:     {stats['avg_processing_time_ms']:.1f}ms")
    print(f"  Average words/image:    {stats['avg_word_count']:.1f}")
    print(f"  Total words extracted:  {stats['total_words_extracted']}")
    print()
    print("  Confidence Distribution:")
    print(f"    High (80-100%):       {high_conf} images")
    print(f"    Medium (50-80%):      {med_conf} images")
    print(f"    Low (0-50%):          {low_conf} images")
    print("=" * 70)
    
    # Show sample of low-confidence results
    if low_conf > 0:
        print("\n⚠️  LOW CONFIDENCE SAMPLES (may need manual review):")
        low_conf_results = sorted(
            [r for r in successful if r.confidence < 0.5],
            key=lambda x: x.confidence
        )[:5]
        for r in low_conf_results:
            print(f"  - {r.filename[:40]}: {r.confidence:.2%}")
    
    # Show failed results
    if failed:
        print("\n❌ FAILED EXTRACTIONS:")
        for r in failed[:5]:
            print(f"  - {r.filename[:40]}: {r.error[:40]}")
    
    return {
        "statistics": stats,
        "analyses": [asdict(a) for a in analyses[:10]],  # Sample
        "results": [asdict(r) for r in results[:10]],  # Sample
        "low_confidence_files": [r.filename for r in successful if r.confidence < 0.5],
        "failed_files": [r.filename for r in failed]
    }


def main():
    """Main entry point."""
    # Determine data directory
    data_dirs = [
        "/app/data",
        "/media/op/DATA/Omkar/CODE-111/Liomonk/Healthcare+/data",
        "./data"
    ]
    
    data_dir = None
    for d in data_dirs:
        if os.path.isdir(d):
            data_dir = d
            break
    
    if not data_dir:
        print("ERROR: Could not find data directory!")
        print(f"Tried: {data_dirs}")
        sys.exit(1)
    
    print(f"Using data directory: {data_dir}")
    
    # Run tests (limit to 50 for faster testing, remove limit for full test)
    limit = int(os.environ.get('TEST_LIMIT', '50'))
    results = run_ocr_tests(data_dir, limit=limit)
    
    # Save results to JSON
    output_file = "/app/ocr_test_results.json"
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Results saved to: {output_file}")
    except Exception as e:
        print(f"\n⚠️  Could not save results: {e}")
    
    # Return success/failure based on success rate
    success_rate = results['statistics']['success_rate']
    if success_rate >= 90:
        print("\n✅ OCR PIPELINE TEST PASSED!")
        return 0
    elif success_rate >= 70:
        print("\n⚠️  OCR PIPELINE TEST PASSED WITH WARNINGS")
        return 0
    else:
        print("\n❌ OCR PIPELINE TEST FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
