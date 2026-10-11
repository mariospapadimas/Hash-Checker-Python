"""Responsive file verification; workers never access Tk widgets."""

import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, ttk

from src.hashing import calculate_file_hash
from src.utils import AppUtils


class _HashingCancelled(Exception):
    """Interrupt an abandoned mode at the next chunk boundary."""


class VerifyFilesMode:
    # Widgets and worker lifecycle belong to this mode instance.
    # pylint: disable=too-many-instance-attributes
    """Select a file and compare its streamed digest with an expected hash."""

    def __init__(self, parent, design):
        self.parent = parent
        self.design = design
        self.file_path = None
        self.busy = False
        self._disposed = False
        self._after_id = None
        self._cancel = threading.Event()
        self._events = queue.Queue(maxsize=8)
        self.algorithm_var = tk.StringVar(self.parent, value="SHA-256")
        self.expected_hash_var = tk.StringVar(self.parent)

        self.select_button = tk.Button(
            parent, text="Select File", command=self.select_file
        )
        self.filename_label = tk.Label(parent, text="No file selected", wraplength=700)
        self.selected_file_path = tk.Label(parent, text="", wraplength=700)
        self.algorithm_select = ttk.Combobox(
            parent, values=list(AppUtils.ALGORITHMS), state="readonly",
            textvariable=self.algorithm_var, width=16
        )
        self.expected_prompt = tk.Label(parent, text="Expected hash", font=design.main_text_font)
        self.expected_hash = tk.Entry(parent, textvariable=self.expected_hash_var, width=65)
        self.verify_button = tk.Button(
            parent, text="Verify File", command=self.verify, state="disabled"
        )
        self.clear_button = tk.Button(parent, text="Clear", command=self.clear)
        self.progress_bar = ttk.Progressbar(parent, mode="determinate", maximum=100, value=0)
        self.progress_label = tk.Label(parent, text="")
        self.result_label = tk.Label(parent, text="", wraplength=700)
        self.algorithm_var.trace_add("write", self._inputs_changed)
        self.expected_hash_var.trace_add("write", self._inputs_changed)

    def draw_ui(self):
        """Use compact controls with wrapping for long paths and results."""
        self.select_button.pack(pady=8)
        self.filename_label.pack(fill="x")
        self.selected_file_path.pack(fill="x", pady=(0, 8))
        self.algorithm_select.pack(pady=5)
        self.expected_prompt.pack(pady=5)
        self.expected_hash.pack(fill="x", padx=20, ipady=5)
        self.verify_button.pack(pady=8)
        self.clear_button.pack()
        self.progress_bar.pack(fill="x", padx=20, pady=(12, 0))
        self.progress_label.pack()
        self.result_label.pack(fill="x", pady=8)

    def select_file(self):
        """Keep the previous selection when the user cancels the dialog."""
        if self.busy or self._disposed:
            return
        path = filedialog.askopenfilename(parent=self.parent)
        if path:
            self.file_path = path
            self.filename_label.config(text=os.path.basename(path))
            self.selected_file_path.config(text=path)
            self._inputs_changed()

    def _inputs_changed(self, *_args):
        if self.busy or self._disposed:
            return
        self.result_label.config(text="")
        self.progress_bar["value"] = 0
        self.progress_label.config(text="")
        self._update_controls()

    def _update_controls(self):
        state = "disabled" if self.busy else "normal"
        for widget in (self.select_button, self.expected_hash, self.clear_button):
            widget.config(state=state)
        self.algorithm_select.config(state="disabled" if self.busy else "readonly")
        eligible = bool(self.file_path) and AppUtils.is_valid_hash(
            self.expected_hash_var.get(), self.algorithm_var.get()
        )
        self.verify_button.config(state="normal" if eligible and not self.busy else "disabled")

    def verify(self):
        """Validate first, snapshot inputs, then hash on a daemon worker."""
        if self.busy or self._disposed:
            return
        if not self.file_path:
            self.result_label.config(text="Please select a file first.")
            return
        expected = self.expected_hash_var.get()
        algorithm = self.algorithm_var.get()
        if not expected.strip():
            self.result_label.config(text="Please enter the expected hash.")
            return
        if not AppUtils.is_valid_hash(expected, algorithm):
            self.result_label.config(text=f"Invalid expected hash for {algorithm}.")
            return
        self.busy = True
        self.progress_bar["value"] = 0
        self.progress_label.config(text="")
        self.result_label.config(text="Verifying file...")
        self._update_controls()
        threading.Thread(
            target=self._hash_file, args=(self.file_path, algorithm, expected), daemon=True
        ).start()
        self._after_id = self.parent.after(50, self._poll_events)

    def _queue_event(self, kind, payload):
        """Bound pending progress; retain recent events and the final result."""
        while not self._cancel.is_set():
            try:
                self._events.put_nowait((kind, payload))
                return
            except queue.Full:
                try:
                    self._events.get_nowait()
                except queue.Empty:
                    pass

    def _hash_file(self, path, algorithm, expected):
        """Worker entry point: only pure hashing, cancellation and queue writes."""
        def progress(processed, total):
            if self._cancel.is_set():
                raise _HashingCancelled
            self._queue_event("progress", (processed, total))

        try:
            digest = calculate_file_hash(path, algorithm, progress_callback=progress)
        except _HashingCancelled:
            return
        except FileNotFoundError:
            self._queue_event("error", "File not found. Please select it again.")
        except PermissionError:
            self._queue_event("error", "Cannot read file: permission denied.")
        except (OSError, ValueError) as error:
            self._queue_event("error", f"Cannot read or hash file: {error}")
        else:
            self._queue_event("done", (digest, expected))

    def _poll_events(self):
        """Consume worker events exclusively on Tk's main thread."""
        self._after_id = None
        if self._disposed:
            return
        while True:
            try:
                kind, payload = self._events.get_nowait()
            except queue.Empty:
                break
            if kind == "progress":
                processed, total = payload
                self.progress_bar["value"] = min(100, processed * 100 / total) if total else 0
                self.progress_label.config(text=f"{processed:,} / {total:,} bytes")
            else:
                self.busy = False
                if kind == "done":
                    self.progress_bar["value"] = 100
                    digest, expected = payload
                    message = "File verified! Hashes match."
                    if not AppUtils.hashes_match(digest, expected):
                        message = AppUtils.concat_str(
                            "Verification failed! Hashes mismatch.",
                            "File may be corrupted or malicious."
                        )
                    self.result_label.config(text=message)
                else:
                    self.result_label.config(text=payload)
                self._update_controls()
                break
        if self.busy:
            self._after_id = self.parent.after(50, self._poll_events)

    def clear(self):
        """Reset selection, input, progress and status when idle."""
        if self.busy or self._disposed:
            return
        self.file_path = None
        self.filename_label.config(text="No file selected")
        self.selected_file_path.config(text="")
        self.expected_hash_var.set("")
        self._inputs_changed()

    def dispose(self):
        """Stop polling and cancel abandoned hashing without blocking Tk."""
        self._disposed = True
        self._cancel.set()
        if self._after_id is not None:
            self.parent.after_cancel(self._after_id)
            self._after_id = None
