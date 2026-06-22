"""
indexer.py -- Auto-Incremental PDF Indexer for TheSuperRAG.

Uses the `watchdog` library to monitor the DATA/ folder for new PDF files.
When a new file is detected, it is automatically parsed, chunked, and
upserted into the Qdrant vector store -- no restart needed.

The `on_indexed` callback is called with an event dict on success, allowing
the FastAPI server to push real-time SSE notifications to the frontend.
"""
import os
import time
import threading
from typing import Callable, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class PDFEventHandler(FileSystemEventHandler):
    """
    Watchdog event handler that triggers incremental indexing
    when new PDF files appear in the watched directory.
    """

    def __init__(self, doc_store, on_indexed: Optional[Callable] = None):
        """
        Args:
            doc_store:    An instance of DocumentStore (from ingest.py).
            on_indexed:   Optional callback called with event dict on success.
                          Signature: (event: dict) -> None
                          Event shape: {"type": "document_indexed", "file": str, "chunks": int}
        """
        super().__init__()
        self.doc_store = doc_store
        self.on_indexed = on_indexed
        self._in_flight: set = set()  # Prevents double-processing the same file

    def on_created(self, event):
        """Fires when a new file/directory appears in the watched path."""
        if event.is_directory:
            return
        if not event.src_path.lower().endswith(".pdf"):
            return

        file_name = os.path.basename(event.src_path)
        if file_name in self._in_flight:
            return

        self._in_flight.add(file_name)

        # Offload to a daemon thread so the watchdog loop is never blocked
        worker = threading.Thread(
            target=self._index_after_delay,
            args=(event.src_path, file_name),
            daemon=True
        )
        worker.start()

    def _index_after_delay(self, file_path: str, file_name: str):
        """
        Waits briefly for the file to finish copying, then indexes it.
        """
        try:
            # Poll until file size stabilises (handles slow network copies)
            prev_size = -1
            for _ in range(10):
                try:
                    curr_size = os.path.getsize(file_path)
                except OSError:
                    curr_size = -1
                if curr_size == prev_size and curr_size > 0:
                    break
                prev_size = curr_size
                time.sleep(0.5)

            print(f"[AutoIndexer] Detected new PDF: {file_name}")
            chunk_count = self.doc_store.index_file(file_path, file_name)

            if chunk_count > 0 and self.on_indexed:
                self.on_indexed({
                    "type": "document_indexed",
                    "file": file_name,
                    "chunks": chunk_count
                })
                print(f"[AutoIndexer] [OK] Indexed {chunk_count} chunks from '{file_name}'")
        except Exception as e:
            print(f"[AutoIndexer] Error indexing '{file_name}': {e}")
        finally:
            self._in_flight.discard(file_name)


class AutoIndexer:
    """
    Manages a watchdog Observer that auto-indexes PDFs dropped into a folder.

    Usage:
        indexer = AutoIndexer("DATA/", doc_store, on_indexed=push_event_fn)
        indexer.start()
        ...
        indexer.stop()
    """

    def __init__(
        self,
        folder_path: str,
        doc_store,
        on_indexed: Optional[Callable] = None
    ):
        self.folder_path = os.path.abspath(folder_path)
        self.handler = PDFEventHandler(doc_store, on_indexed)
        self.observer = Observer()
        self._running = False

    def start(self):
        """Start watching the folder for new PDFs."""
        if self._running:
            return
        os.makedirs(self.folder_path, exist_ok=True)
        self.observer.schedule(self.handler, self.folder_path, recursive=False)
        self.observer.start()
        self._running = True
        print(f"[AutoIndexer] Watching: {self.folder_path}")

    def stop(self):
        """Gracefully stop the watchdog observer."""
        if not self._running:
            return
        self.observer.stop()
        self.observer.join(timeout=5)
        self._running = False
        print("[AutoIndexer] Stopped.")

    @property
    def is_running(self) -> bool:
        return self._running
