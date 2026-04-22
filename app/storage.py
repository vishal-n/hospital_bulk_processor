from threading import Lock
from typing import Dict, Optional

from app.models import BatchStatus


class InMemoryBatchStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._batches: Dict[str, BatchStatus] = {}

    def set_batch(self, batch: BatchStatus) -> None:
        with self._lock:
            self._batches[batch.batch_id] = batch

    def get_batch(self, batch_id: str) -> Optional[BatchStatus]:
        with self._lock:
            return self._batches.get(batch_id)

    def update_batch(self, batch_id: str, **fields) -> Optional[BatchStatus]:
        with self._lock:
            batch = self._batches.get(batch_id)
            if not batch:
                return None
            updated = batch.model_copy(update=fields)
            self._batches[batch_id] = updated
            return updated


batch_store = InMemoryBatchStore()
