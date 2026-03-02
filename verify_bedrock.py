import asyncio
import os
import sys

# Add the app directory to the Python path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.aws_service import AWSService
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def verify_bedrock_vision():
    print("Initializing AWS Service...")
    try:
        aws = AWSService()
    except Exception as e:
        print(f"Failed to initialize AWSService: {e}")
        return

    # Paths to the user's images
    image_paths = [
        r"c:\Users\vikky\Desktop\medico\medical-records\img1.png",
        r"c:\Users\vikky\Desktop\medico\medical-records\img2.png"
    ]

    for img_path in image_paths:
        print(f"\n--- Testing Image: {os.path.basename(img_path)} ---")
        if not os.path.exists(img_path):
            print(f"File not found: {img_path}")
            continue

        print(f"Reading {img_path}...")
        try:
            with open(img_path, "rb") as f:
                image_bytes = f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            continue

        print("Sending to AWS Bedrock Vision (Claude 3.5 Sonnet)...")
        prompt = "Analyze this medical image. Describe findings, type of scan, clinical observations."
        
        try:
            # We are directly testing the Bedrock vision function used in DocumentProcessor
            result = await aws.analyze_image_with_bedrock(image_bytes, prompt)
            print("\nSUCCESS! Bedrock Response:")
            print("="*60)
            print(result)
            print("="*60)
        except Exception as e:
            print(f"\nAWS Bedrock Error: {e}")
            print("Please ensure your AWS credentials are valid and you have requested access to the 'anthropic.claude-3-sonnet-20240229-v1:0' model in the AWS Bedrock console.")

if __name__ == "__main__":
    print("=== AWS Bedrock Vision (Claude 3.5 Sonnet) Verification Script ===")
    if not os.environ.get("AWS_ACCESS_KEY_ID") or not os.environ.get("AWS_SECRET_ACCESS_KEY"):
        print("⚠️ Warning: AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY not found in environment!")
        print("Make sure your .env file is loaded correctly.\n")
    
    asyncio.run(verify_bedrock_vision())
