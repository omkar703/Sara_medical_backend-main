import asyncio
import os
import sys

# Add the app directory to the Python path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.aws_service import AWSService
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def verify_image_extraction():
    print("Initializing AWS Service...")
    try:
        aws = AWSService()
    except Exception as e:
        print(f"Failed to initialize AWSService: {e}")
        return

    # Assuming there's a sample image file here. We will just use the same folder.
    image_dir = r"c:\Users\vikky\Desktop\medico\medical-records"
    
    # Try finding an image file (.png, .jpg, .jpeg)
    image_path = None
    for file in os.listdir(image_dir):
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(image_dir, file)
            break
            
    if not image_path:
        print(f"No image files found in: {image_dir}")
        print("Please place a .png or .jpg in the folder to test.")
        return

    print(f"\n--- Testing Raw Image: {os.path.basename(image_path)} ---")

    print(f"Reading {image_path}...")
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    print(f"Extracting image ({len(image_bytes)} bytes) using AWS Bedrock Vision...")
    
    try:
        vision_result = await aws.analyze_image_with_bedrock(
            image_bytes, 
            "Analyze this medical document image. Extract all the text you can see."
        )
        print(f"\n✅ SUCCESS! Bedrock Extraction for Raw Image:")
        print("-" * 40)
        print(vision_result)
        print("-" * 40)
    except Exception as e:
        print(f"Bedrock analysis failed for raw image file: {e}")

if __name__ == "__main__":
    print("=== Raw Image Extraction Verification Script ===")
    asyncio.run(verify_image_extraction())
