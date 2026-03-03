class MockTask:
    """
    Mock Celery task that runs document processing SYNCHRONOUSLY.
    This ensures chunks are saved to the DB even without a real Celery worker.
    Replace `.delay()` with a real Celery task in production.
    """
    def delay(self, document_id_str: str, *args, **kwargs):
        print(f"[MockTask] Triggering SYNC document processing for: {document_id_str}")
        try:
            from uuid import UUID
            from app.database import SyncSessionLocal
            from app.services.sync_document_processor import SyncDocumentProcessor

            document_id = UUID(document_id_str)
            db = SyncSessionLocal()
            try:
                processor = SyncDocumentProcessor(db)
                processor.process_document(document_id)
                print(f"[MockTask] ✅ Sync processing complete for doc {document_id_str}")
            finally:
                db.close()
        except Exception as e:
            import traceback
            print(f"[MockTask] ❌ Sync processing failed for {document_id_str}: {e}")
            traceback.print_exc()

process_document_task = MockTask()
