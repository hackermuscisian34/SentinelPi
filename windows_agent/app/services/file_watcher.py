
import logging
import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Callable
import pathlib

logger = logging.getLogger("agent.watcher")

# How long (seconds) to wait before re-scanning the same file
SCAN_COOLDOWN_SECONDS = 60


class DownloadHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self._last_scanned: dict[str, float] = {}   # path -> last scan timestamp
        self._lock = threading.Lock()

    def on_created(self, event):
        if not event.is_directory:
            self._process(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._process(event.src_path)

    def _process(self, path: str):
        # Ignore temporary / in-progress download files
        lower = path.lower()
        if lower.endswith((".tmp", ".crdownload", ".part", ".~lock", ".swp")):
            return

        # Ignore Windows system metadata files
        basename = os.path.basename(path)
        if basename.startswith("~") or basename == "desktop.ini" or basename == "thumbs.db":
            return

        now = time.monotonic()
        with self._lock:
            last = self._last_scanned.get(path, 0)
            if now - last < SCAN_COOLDOWN_SECONDS:
                # Cooldown not expired — skip silently
                return
            self._last_scanned[path] = now

        logger.info(f"File detected: {path}")
        self.callback(path)


class DownloadWatcher:
    def __init__(self, scan_callback: Callable[[str], None]):
        self.observer = Observer()
        self.scan_callback = scan_callback
        self.downloads_path = str(pathlib.Path.home() / "Downloads")

    def start(self):
        if not os.path.exists(self.downloads_path):
            logger.warning(f"Downloads folder not found at {self.downloads_path}")
            return

        logger.info(f"Starting Download Watcher on {self.downloads_path}")
        event_handler = DownloadHandler(self.scan_callback)
        self.observer.schedule(event_handler, self.downloads_path, recursive=False)
        self.observer.start()

    def stop(self):
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
