"""
Synchronous Document Processor for Celery Tasks
================================================
This module mirrors `document_processor.py` but uses a *synchronous* SQLAlchemy
session (psycopg2) instead of asyncpg, which avoids the event loop conflict that
occurs when Celery gevent greenlets try to reuse an asyncpg connection pool.

AWS Bedrock calls (which are async) are executed in isolated `asyncio.run()` calls
inside a fresh thread — one call at a time — so they never conflict with any existing
event loop.
"""

import io
import os
import uuid as uuid_mod
import tempfile
import asyncio
import concurrent.futures
from datetime import datetime
from typing import List
from uuid import UUID

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.chunk import Chunk
from app.services.minio_service import minio_service


def _run_async_isolated(coro):
    """Run a single async coroutine in a fresh background thread with its own event loop."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def _generate_embeddings(text: str) -> list:
    from app.services.aws_service import aws_service
    return _run_async_isolated(aws_service.generate_embeddings(text))


def _analyze_image(image_bytes: bytes) -> str:
    from app.services.aws_service import aws_service
    return _run_async_isolated(
        aws_service.analyze_image_with_bedrock(
            image_bytes,
            "Analyze this medical image. Describe findings, type of scan, clinical observations."
        )
    )


class SyncDocumentProcessor:
    """Fully synchronous document processor designed for use inside Celery tasks."""

    def __init__(self, db: Session):
        self.db = db

    def process_document(self, document_id: UUID):
        """
        Main entry point. Downloads file from MinIO, extracts text + images,
        generates embeddings via Bedrock, and bulk-inserts Chunk rows.
        """
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            print(f"[SyncDocumentProcessor] Document {document_id} not found.")
            return

        if not document.processing_details:
            document.processing_details = {
                "tier_1_text": {"status": "pending"},
                "tier_2_images": {"status": "pending"},
                "tier_3_vision": {"status": "pending"},
            }

        temp_path = None
        try:
            # ── Download from MinIO ────────────────────────────────────────────
            print(f"[SyncDocumentProcessor] Downloading {document.storage_path} from MinIO...")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".file") as tmp:
                temp_path = tmp.name

            from app.config import settings
            minio_service.client.fget_object(
                settings.MINIO_BUCKET_DOCUMENTS,
                document.storage_path,
                temp_path,
            )
            print(f"[SyncDocumentProcessor] Downloaded to {temp_path}")

            # ── Tier 1: Text Extraction ────────────────────────────────────────
            text_chunks = self._process_tier_1_text(document, temp_path)
            document.processing_details["tier_1_text"] = {
                "status": "completed",
                "chunks": len(text_chunks),
            }

            # ── Tier 2 & 3: Image Vision ───────────────────────────────────────
            image_chunks = self._process_tier_2_and_3_vision(document, temp_path)
            document.processing_details["tier_2_images"] = {"status": "completed"}
            document.processing_details["tier_3_vision"] = {
                "status": "completed",
                "chunks": len(image_chunks),
            }

            # ── Bulk Insert Chunks ─────────────────────────────────────────────
            all_chunks = text_chunks + image_chunks
            if all_chunks:
                rows = [
                    {
                        "id": uuid_mod.uuid4(),
                        "document_id": c.document_id,
                        "patient_id": c.patient_id,
                        "content": c.content,
                        "source": c.source,
                        "chunk_type": c.chunk_type,
                        "page_number": c.page_number,
                        "medical_keywords": c.medical_keywords,
                        "embedding": c.embedding,
                        "created_at": datetime.utcnow(),
                    }
                    for c in all_chunks
                ]
                from sqlalchemy import insert
                self.db.execute(insert(Chunk).values(rows))
                print(f"[SyncDocumentProcessor] Inserted {len(rows)} chunks.")

            document.total_chunks = len(all_chunks)
            self.db.commit()
            print(f"[SyncDocumentProcessor] ✅ Committed {len(all_chunks)} chunks for doc {document_id}.")

        except Exception as exc:
            self.db.rollback()
            import traceback
            print(f"[SyncDocumentProcessor] ❌ Failed for {document_id}: {exc}")
            traceback.print_exc()
            if document:
                try:
                    document.processing_details["error"] = str(exc)
                    self.db.commit()
                except Exception:
                    pass
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass

    # ── Private helpers ────────────────────────────────────────────────────────

    def _process_tier_1_text(self, document: Document, file_path: str) -> List[Chunk]:
        """Extract text from PDF pages and generate embeddings (Tier 1)."""
        chunks = []
        if document.file_type != "application/pdf":
            print(f"[Tier1] Skipping non-PDF ({document.file_type})")
            return chunks

        try:
            reader = PdfReader(file_path)
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if not text:
                    continue
                try:
                    embedding = _generate_embeddings(text)
                    chunks.append(Chunk(
                        document_id=document.id,
                        patient_id=document.patient_id,
                        content=text,
                        source="TIER_1_TEXT",
                        chunk_type="text",
                        page_number=i + 1,
                        medical_keywords=[],
                        embedding=embedding,
                    ))
                except Exception as exc:
                    print(f"[Tier1] Page {i+1} embedding failed: {exc}")
        except Exception as exc:
            import traceback
            traceback.print_exc()
            print(f"[Tier1] Failed: {exc}")

        print(f"[Tier1] Extracted {len(chunks)} text chunks.")
        return chunks

    def _process_tier_2_and_3_vision(self, document: Document, file_path: str) -> List[Chunk]:
        """Send images to AWS Bedrock Vision (Tier 2/3)."""
        chunks = []
        try:
            if document.file_type in ("image/png", "image/jpeg"):
                with open(file_path, "rb") as f:
                    image_bytes = f.read()
                try:
                    analysis = _analyze_image(image_bytes)
                    embedding = _generate_embeddings(analysis)
                    chunks.append(Chunk(
                        document_id=document.id,
                        patient_id=document.patient_id,
                        content=analysis,
                        source="TIER_3_IMAGE_ANALYSIS",
                        chunk_type="image_analysis",
                        page_number=1,
                        medical_keywords=[],
                        embedding=embedding,
                    ))
                except Exception as exc:
                    print(f"[Tier2/3] Raw image Bedrock call failed: {exc}")

            elif document.file_type == "application/pdf":
                reader = PdfReader(file_path)
                for i, page in enumerate(reader.pages):
                    for img_obj in page.images:
                        try:
                            analysis = _analyze_image(img_obj.data)
                            embedding = _generate_embeddings(analysis)
                            chunks.append(Chunk(
                                document_id=document.id,
                                patient_id=document.patient_id,
                                content=analysis,
                                source="TIER_3_IMAGE_ANALYSIS",
                                chunk_type="image_analysis",
                                page_number=i + 1,
                                medical_keywords=[],
                                embedding=embedding,
                            ))
                        except Exception as exc:
                            print(f"[Tier2/3] PDF image on page {i+1} failed: {exc}")
        except Exception as exc:
            import traceback
            traceback.print_exc()
            print(f"[Tier2/3] Failed: {exc}")

        print(f"[Tier2/3] Extracted {len(chunks)} image-analysis chunks.")
        return chunks
