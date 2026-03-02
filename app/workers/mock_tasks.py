class MockTask:
    def delay(self, *args, **kwargs):
        print(f"MOCK CELERY: Task delayed with args={args} kwargs={kwargs}")
        return None

process_document_task = MockTask()
