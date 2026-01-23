"""Document Service - Business logic for document management"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.services.storage_service import StorageService


class DocumentService:
    """Service for document CRUD operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage = StorageService()
    
    async def create_document_metadata(
        self,
        patient_id: UUID,
        organization_id: UUID,
        file_name: str,
        file_type: str,
        file_size: int,
        uploaded_by: UUID,
    ) -> Dict:
        """
        Create document metadata record (before file upload)
        
        Returns:
            Document data including ID and storage path
        """
        # Create document with unique ID
        document = Document(
            patient_id=patient_id,
            organization_id=organization_id,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            storage_path="",  # Will be set after ID generation
            uploaded_by=uploaded_by,
        )
        
        self.db.add(document)
        await self.db.flush()  # Get the ID without committing
        
        # Generate storage path using document ID
        storage_path = self.storage.generate_storage_path(
            organization_id=organization_id,
            patient_id=patient_id,
            document_id=document.id,
            filename=file_name
        )
        
        document.storage_path = storage_path
        await self.db.flush()
        
        return {
            "id": str(document.id),
            "storage_path": storage_path,
            "file_name": file_name,
            "file_type": file_type,
            "file_size": file_size,
        }
    
    async def confirm_upload(
        self,
        document_id: UUID,
        organization_id: UUID,
        metadata: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Confirm upload and update document metadata
        
        Args:
            document_id: Document UUID
            organization_id: Organization UUID for multi-tenant filtering
            metadata: Optional dict with title, category, notes
        
        Returns:
            Document data or None if not found
        """
        result = await self.db.execute(
            select(Document)
            .where(
                Document.id == document_id,
                Document.organization_id == organization_id,
                Document.deleted_at.is_(None)
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            return None
        
        # Update metadata if provided
        if metadata:
            if "title" in metadata:
                document.title = metadata["title"]
            if "category" in metadata:
                document.category = metadata["category"]
            if "notes" in metadata:
                document.notes = metadata["notes"]
        
        await self.db.flush()
        
        return await self._document_to_dict(document)
    
    async def list_documents(
        self,
        organization_id: UUID,
        patient_id: Optional[UUID] = None,
        category: Optional[str] = None
    ) -> List[Dict]:
        """
        List documents for an organization/patient
        
        Args:
            organization_id: Organization UUID (required for multi-tenancy)
            patient_id: Optional patient ID filter
            category: Optional category filter
        
        Returns:
            List of document data dicts with download URLs
        """
        query = select(Document).where(
            Document.organization_id == organization_id,
            Document.deleted_at.is_(None)
        )
        
        if patient_id:
            query = query.where(Document.patient_id == patient_id)
        
        if category:
            query = query.where(Document.category == category)
        
        query = query.order_by(Document.uploaded_at.desc())
        
        result = await self.db.execute(query)
        documents = result.scalars().all()
        
        # Convert to dicts with download URLs
        return [await self._document_to_dict(doc, include_download_url=True) for doc in documents]
    
    async def get_document(
        self,
        document_id: UUID,
        organization_id: UUID
    ) -> Optional[Dict]:
        """
        Get a single document by ID
        
        Args:
            document_id: Document UUID
            organization_id: Organization UUID for multi-tenant filtering
        
        Returns:
            Document data with download URL or None
        """
        result = await self.db.execute(
            select(Document)
            .where(
                Document.id == document_id,
                Document.organization_id == organization_id,
                Document.deleted_at.is_(None)
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            return None
        
        return await self._document_to_dict(document, include_download_url=True)
    
    async def delete_document(
        self,
        document_id: UUID,
        organization_id: UUID
    ) -> bool:
        """
        Soft delete document from DB and delete file from storage
        
        Args:
            document_id: Document UUID
            organization_id: Organization UUID for multi-tenant filtering
        
        Returns:
            True if deleted, False if not found
        """
        result = await self.db.execute(
            select(Document)
            .where(
                Document.id == document_id,
                Document.organization_id == organization_id,
                Document.deleted_at.is_(None)
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            return False
        
        # Soft delete in DB
        document.deleted_at = datetime.utcnow()
        await self.db.flush()
        
        # Delete from storage
        await self.storage.delete_file(document.storage_path)
        
        return True
    
    async def _document_to_dict(
        self,
        document: Document,
        include_download_url: bool = False
    ) -> Dict:
        """Convert Document model to dict"""
        data = {
            "id": str(document.id),
            "patientId": str(document.patient_id),
            "fileName": document.file_name,
            "fileType": document.file_type,
            "fileSize": document.file_size,
            "category": document.category,
            "title": document.title,
            "notes": document.notes,
            "uploadedAt": document.uploaded_at.isoformat() if document.uploaded_at else None,
            "uploadedBy": str(document.uploaded_by) if document.uploaded_by else None,
            "virusScanned": document.virus_scanned,
            "virusScanResult": document.virus_scan_result,
        }
        
        if include_download_url:
            download_url = await self.storage.generate_download_url(document.storage_path)
            data["downloadUrl"] = download_url
        
        return data
