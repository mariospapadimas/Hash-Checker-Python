"""The main hash checker application."""

import tkinter as tk
from tkinter.ttk import Combobox

from src.design_system import DesignSystem
from src.modes.compare_hashes import CompareHashesMode
from src.modes.verify_files import VerifyFilesMode


class HashChecker:
    """The class for the HashChecker application."""

    def __init__(self, root):
        """Initialize the HashChecker application."""
        self.root = root
        self.active_mode = None

        self.root.title("Hash Checker")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.design = DesignSystem()

        self.label_title = tk.Label(
            text="Hash Checker",
            font=self.design.main_title_font
        )

        self.mode_select = Combobox(
            self.root,
            values=["Compare Hashes Mode", "Verify Files Mode"],
            state="readonly",
            width=25
        )

        self.mode_select.bind(
            "<<ComboboxSelected>>",
            self.on_selection_change
        )

        self.content_frame = tk.Frame(self.root)

    def on_selection_change(self, _event=None):
        """Change the hash checker mode."""
        self._dispose_active_mode()
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        selection = self.mode_select.get()

        if selection == "Compare Hashes Mode":
            self.active_mode = CompareHashesMode(
                self.content_frame,
                self.design
            )

        elif selection == "Verify Files Mode":
            self.active_mode = VerifyFilesMode(
                self.content_frame,
                self.design
            )
        if self.active_mode is not None:
            self.active_mode.draw_ui()

    def _dispose_active_mode(self):
        if self.active_mode is not None:
            dispose = getattr(self.active_mode, "dispose", None)
            if dispose is not None:
                dispose()
            self.active_mode = None

    def close(self):
        """Dispose the current mode before closing the window."""
        self._dispose_active_mode()
        self.root.destroy()

    def draw_ui(self):
        """Draw the UI."""
        self.label_title.pack()

        self.mode_select.current(0)
        self.mode_select.pack(pady=10)

        self.content_frame.pack(fill="both", expand=True, padx=20)

        self.on_selection_change()
