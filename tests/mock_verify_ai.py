"""Mock Verification Test for AI Features"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime

from app.services.document_processor import DocumentProcessor
from app.services.ai_chat_service import AIChatService
from app.models.document import Document
from app.models.user import User
from app.models.chunk import Chunk

@pytest.mark.asyncio
async def test_document_processor():
    # Mock DB Session
    mock_db = AsyncMock()
    
    # Mock Document
    doc_id = uuid4()
    mock_doc = Document(
        id=doc_id,
        patient_id=uuid4(),
        processing_details={},
        storage_path="test.pdf"
    )
    
    # Mock Select execution
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_doc
    mock_db.execute.return_value = mock_result
    
    # Mock file read
    with patch("builtins.open", new_callable=MagicMock) as mock_open:
        mock_file = MagicMock()
        mock_file.read.return_value = b"fake pdf content"
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Mock AWS Service
        with patch("app.services.document_processor.aws_service") as mock_aws:
            mock_aws.analyze_image_with_bedrock = AsyncMock(return_value="Image analysis result")
            
            # Init Processor
            processor = DocumentProcessor(mock_db)
            
            # Run Process
            with patch("app.services.document_processor.PdfReader") as mock_pdf:
                mock_page = MagicMock()
                mock_page.extract_text.return_value = "Page 1 content"
                mock_page.images = [] # No images for simplicity
                mock_pdf.return_value.pages = [mock_page]
                
                await processor.process_document(doc_id)
                
    # Verify DB commits
    assert mock_db.commit.called
    assert mock_doc.status == "indexed"
    assert mock_doc.total_chunks > 0
    assert mock_doc.processing_details["tier_1_text"]["status"] == "completed"

@pytest.mark.asyncio
async def test_chat_service():
    mock_db = AsyncMock()
    
    # Mock Chunks
    chunk1 = Chunk(id=uuid4(), content="Medical info A", source="text", page_number=1)
    
    # Mock Select
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [chunk1]
    mock_db.execute.return_value = mock_result
    
    # Mock AWS
    with patch("app.services.ai_chat_service.aws_service") as mock_aws:
        mock_aws.generate_text = AsyncMock(return_value="AI Response based on Medical info A")
        
        service = AIChatService(mock_db)
        user = User(id=uuid4(), role="patient")
        
        # Run Chat
        response_gen = service.chat_with_patient_data(
            patient_id=user.id,
            query="What is info A?",
            requesting_user=user
        )
        
        response = []
        async for part in response_gen:
            response.append(part)
            
        assert "AI Response" in "".join(response)
        assert mock_db.add.called # ChatHistory saved
