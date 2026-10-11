"""The compare hashes mode."""

import tkinter as tk
from tkinter import ttk

from src.utils import AppUtils


class CompareHashesMode:
    """The class for the compare hashes mode."""

    def __init__(self, parent, design):
        """Initialize the HashChecker compare mode."""
        self.design = design
        self.parent = parent
        self.algorithm_var = tk.StringVar(self.parent, value="SHA-256")
        self.algorithm_select = ttk.Combobox(
            self.parent,
            values=list(AppUtils.ALGORITHMS),
            state="readonly",
            textvariable=self.algorithm_var,
            width=16
        )

        self.entry_prompt_first = tk.Label(
            self.parent,
            text="Enter first hash",
            font=self.design.main_text_font
        )

        self.entry_prompt_second = tk.Label(
            self.parent,
            text="Enter second hash",
            font=self.design.main_text_font
        )

        self.result_label = tk.Label(
            self.parent,
            text="",
            font=self.design.main_text_font,
            wraplength=700
        )

        self.first_hash = tk.Entry(
            self.parent,
            width=60
        )

        self.second_hash = tk.Entry(
            self.parent,
            width=60
        )

        self.check_button = tk.Button(
            self.parent,
            text="Check Hashes",
            font=self.design.main_text_font,
            command=self.check,
            fg="white",
            bg="black"
        )

    def draw_ui(self):
        """Draw the UI."""
        self.algorithm_select.pack(pady=10)
        self.entry_prompt_first.pack()
        self.first_hash.pack(fill="x", padx=20, ipady=5)

        self.entry_prompt_second.pack()
        self.second_hash.pack(fill="x", padx=20, ipady=5)

        self.check_button.pack(pady=50)

        self.result_label.pack(fill="x")

    def check(self):
        """Check if the two hashes match."""
        hash1 = self.first_hash.get().strip()
        hash2 = self.second_hash.get().strip()
        algorithm = self.algorithm_var.get()

        if not hash1 or not hash2:
            self.result_label.config(
                text="Please enter both hashes"
            )
        elif not all(AppUtils.is_valid_hash(value, algorithm) for value in (hash1, hash2)):
            length = AppUtils.ALGORITHMS[algorithm][1]
            self.result_label.config(
                text=f"Enter valid {algorithm} hashes ({length} hexadecimal characters)."
            )
        elif AppUtils.hashes_match(hash1, hash2):
            self.result_label.config(
                text="Check complete! Hashes match!"
            )
        else:
            self.result_label.config(
                text=AppUtils.concat_str(
                    "Check complete! Hashes mismatch.",
                    "Files may be corrupted or malicious"
                )
            )
