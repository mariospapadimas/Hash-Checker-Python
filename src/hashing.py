"""Pure file hashing, independent of Tkinter."""

import hashlib
import os
from typing import Callable, Optional

from src.utils import AppUtils


def calculate_file_hash(
    file_path: str,
    algorithm: str,
    chunk_size: int = 1024 * 1024,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> str:
    """Hash bounded chunks, reporting bytes and propagating read failures.

    Total size is captured from the opened file. Callbacks run in the caller's
    thread and may raise to interrupt hashing; no UI code belongs here.
    """
    if chunk_size <= 0:
        raise ValueError("Hash chunk size must be positive")
    # File checksums may use legacy algorithms on restricted builds.
    digest = hashlib.new(AppUtils.get_hashlib_algorithm(algorithm), usedforsecurity=False)
    with open(file_path, "rb") as source:
        total = os.fstat(source.fileno()).st_size
        processed = 0
        if progress_callback is not None:
            progress_callback(processed, total)
        while True:
            chunk = source.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
            processed += len(chunk)
            if progress_callback is not None:
                progress_callback(processed, total)
    return digest.hexdigest()
