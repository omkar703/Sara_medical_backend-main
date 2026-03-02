import asyncio
import uuid
from app.services.storage_service import StorageService
from app.config import settings

async def test_storage_service():
    print(f"MINIO_ENDPOINT: {settings.MINIO_ENDPOINT}")
    print(f"MINIO_EXTERNAL_ENDPOINT: {settings.MINIO_EXTERNAL_ENDPOINT}")
    print(f"MINIO_BUCKET_DOCUMENTS: {settings.MINIO_BUCKET_DOCUMENTS}")
    
    storage = StorageService()
    org_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    filename = "test_document.pdf"
    
    # 1. Test Storage Path Generation
    generated_path = storage.generate_storage_path(org_id, patient_id, doc_id, filename)
    print(f"\nGenerated Storage Path: {generated_path}")
    expected_start = f"{org_id}/{patient_id}/{doc_id}"
    assert generated_path.startswith(expected_start)
    assert not generated_path.startswith("/")
    
    # 2. Test Download URL Generation
    download_url = await storage.generate_download_url(generated_path)
    print(f"Generated Download URL: {download_url}")
    
    # Check for double slashes in the path part
    # URL format: http://host:port/bucket/path...
    url_path = download_url.split("?")[0]
    # Remove protocol
    path_no_proto = url_path.split("://")[1]
    # Split by /
    parts = path_no_proto.split("/")
    print(f"URL path parts: {parts}")
    
    # parts[0] is netloc
    # parts[1] is bucket
    # parts[2:] is object key
    
    if any(p == "" for p in parts[1:]):
        print("  --> ERROR: Double slash detected in URL path!")
    else:
        print("  --> SUCCESS: No double slashes in URL path.")

if __name__ == "__main__":
    asyncio.run(test_storage_service())
