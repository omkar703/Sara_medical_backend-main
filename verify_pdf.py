import asyncio
import os
import sys

# Add the app directory to the Python path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.aws_service import AWSService
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def verify_pdf_extraction():
    print("Initializing AWS Service...")
    try:
        aws = AWSService()
    except Exception as e:
        print(f"Failed to initialize AWSService: {e}")
        return

    # Path to the user's PDF
    pdf_path = r"c:\Users\vikky\Desktop\medico\medical-records\png2pdf.pdf"

    print(f"\n--- Testing PDF: {os.path.basename(pdf_path)} ---")
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return

    print(f"Reading {pdf_path}...")
    try:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    print("Extracting embedded text using PyPDF (Tier 1)...")
    
    try:
        # TIER 1 Testing
        result = await aws.extract_text_from_document(pdf_bytes)
        print("\nSUCCESS! Tier 1 Response:")
        print("="*60)
         
        text_snapshot = result.get("RawText", "")
        if not text_snapshot.strip():
             print("WARNING: No native text was found in this PDF. Proceeding to Tier 2 (Vision Extraction)...")
        else:
             print(text_snapshot[:500] + "...")
             
        print("="*60)
        
        # TIER 2 Testing (Extract images and send to Bedrock Vision)
        print("\nExtracting embedded images from PDF (Tier 2/3)...")
        import io
        from pypdf import PdfReader
        
        reader = PdfReader(io.BytesIO(pdf_bytes))
        images_found = 0
        
        for i, page in enumerate(reader.pages):
            for img_file_obj in page.images:
                images_found += 1
                image_bytes = img_file_obj.data
                print(f"Found image on page {i+1} ({len(image_bytes)} bytes)")
                print("Sending image to AWS Bedrock Vision (Claude 3 Haiku)...")
                
                try:
                    vision_result = await aws.analyze_image_with_bedrock(
                        image_bytes, 
                        "Analyze this medical document image. Extract all the text you can see."
                    )
                    print(f"\n✅ SUCCESS! Bedrock Extraction for Image {images_found}:")
                    print("-" * 40)
                    print(vision_result)
                    print("-" * 40)
                except Exception as e:
                    print(f"Bedrock analysis failed for image {images_found}: {e}")
                    
        if images_found == 0:
            print("No embedded images found in this PDF.")
            
    except Exception as e:
        print(f"\nExtraction Error: {e}")

if __name__ == "__main__":
    print("=== PDF Text Extraction Verification Script ===")
    asyncio.run(verify_pdf_extraction())
