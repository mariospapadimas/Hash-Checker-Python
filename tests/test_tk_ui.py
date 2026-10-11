"""Opt-in rendered Tk regression; ordinary CI stays fully headless.

Run with HASH_CHECKER_UI_TESTS=1 on a machine with a desktop display.
"""

import os
import tkinter as tk
from tkinter import filedialog

import pytest

from src.app import HashChecker


@pytest.mark.skipif(os.environ.get("HASH_CHECKER_UI_TESTS") != "1",
                    reason="opt-in desktop Tk layout regression")
def test_long_path_keeps_verification_controls_visible(monkeypatch):
    """A 3,000-character selection must not push controls out of 800x600."""
    root = tk.Tk()
    root.withdraw()
    root.overrideredirect(True)
    root.attributes("-alpha", 0)
    controller = HashChecker(root)
    try:
        controller.draw_ui()
        controller.mode_select.set("Verify Files Mode")
        controller.on_selection_change()
        mode = controller.active_mode
        path = "C:/" + "long-directory/" * 200 + "selected.bin"
        # Open-file dialogs can return paths exceeding the legacy 260 limit.
        monkeypatch.setattr(filedialog, "askopenfilename", lambda **_kwargs: path)
        mode.select_file()
        mode.algorithm_var.set("SHA-512")
        mode.expected_hash_var.set("a" * 128)
        root.deiconify()
        root.update()
        for widget in (mode.verify_button, mode.clear_button, mode.progress_bar,
                       mode.progress_label, mode.result_label):
            assert widget.winfo_ismapped(), "long path hides verification controls"
            assert widget.winfo_height() >= widget.winfo_reqheight()
        assert mode.verify_button["state"] == "normal"
        assert mode.selected_file_path.get("1.0", "end-1c") == path
        mode.selected_file_path.yview_moveto(1)
        assert mode.selected_file_path.yview()[1] == 1
    finally:
        controller.close()
