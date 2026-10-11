"""Verification flows exercise real handlers, queues and file hashing."""

import threading
import time
from types import SimpleNamespace

import pytest

from src.modes import verify_files
from tests.helpers import FakeParent, patch_verify_widgets

ABC_SHA256 = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


@pytest.fixture
def mode(monkeypatch):
    """Construct real mode logic with only the Tk boundary replaced."""
    patch_verify_widgets(monkeypatch, verify_files)
    instance = verify_files.VerifyFilesMode(
        FakeParent(), SimpleNamespace(main_text_font="font")
    )
    yield instance
    instance.dispose()


def wait_for_result(mode):
    """Pump main-thread events until the real worker completes."""
    deadline = time.monotonic() + 3
    while mode.busy and time.monotonic() < deadline:
        mode.parent.pump()
        time.sleep(0.001)
    assert not mode.busy, "worker did not complete"


def prepare_file(mode, tmp_path, expected=ABC_SHA256):
    """Choose a real file containing a known vector."""
    path = tmp_path / "selected.bin"
    path.write_bytes(b"abc")
    mode.file_path = str(path)
    mode.expected_hash_var.set(expected)
    return path


def test_no_file_selected(mode):
    """Guard direct invocation even when the button is disabled."""
    mode.expected_hash_var.set(ABC_SHA256)
    mode.verify()
    assert "select" in mode.result_label["text"].lower()
    assert not mode.busy


@pytest.mark.parametrize("expected", ["", " ", "a" * 16, "g" * 64])
def test_invalid_expected_hash(mode, tmp_path, expected):
    """Empty and malformed expected values never start a worker."""
    prepare_file(mode, tmp_path, expected)
    assert mode.verify_button["state"] == "disabled"
    mode.verify()
    assert "hash" in mode.result_label["text"].lower()
    assert not mode.busy


@pytest.mark.parametrize("expected,success", [(ABC_SHA256.upper(), True), ("0" * 64, False)])
def test_verify_selected_file(mode, tmp_path, expected, success):
    """Verify the actual selected bytes against the provided digest."""
    prepare_file(mode, tmp_path, expected)
    mode.verify()
    wait_for_result(mode)
    message = mode.result_label["text"].lower()
    assert ("verified" in message) == success
    if not success:
        assert "mismatch" in message and "malicious" in message
    assert mode.progress_bar["value"] == 100
    assert "3 / 3 bytes" in mode.progress_label["text"]
    assert mode.verify_button["state"] == "normal"
    assert mode.algorithm_select["state"] == "readonly"


def test_different_selected_file_is_hashed(mode, tmp_path):
    """Changing the file must change the verification outcome."""
    prepare_file(mode, tmp_path)
    other = tmp_path / "other"
    other.write_bytes(b"different data")
    mode.file_path = str(other)
    mode.verify()
    wait_for_result(mode)
    assert "mismatch" in mode.result_label["text"].lower()


def test_missing_file_error(mode, tmp_path):
    """A selected file removed before hashing gives an explicit error."""
    path = prepare_file(mode, tmp_path)
    path.unlink()
    mode.verify()
    wait_for_result(mode)
    assert "not found" in mode.result_label["text"].lower()
    assert mode.select_button["state"] == "normal"


@pytest.mark.parametrize("error,fragment", [
    (PermissionError("denied"), "permission"), (OSError("broken disk"), "read"),
])
def test_read_errors_restore_controls(mode, tmp_path, monkeypatch, error, fragment):
    """Filesystem failures leave the mode usable for another attempt."""
    prepare_file(mode, tmp_path)

    def fail_hash(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(verify_files, "calculate_file_hash", fail_hash, raising=False)
    mode.verify()
    wait_for_result(mode)
    assert fragment in mode.result_label["text"].lower()
    assert mode.expected_hash["state"] == "normal"
    assert mode.clear_button["state"] == "normal"


def test_selection_and_cancel(mode, tmp_path, monkeypatch):
    """A cancelled picker preserves the last selected path and filename."""
    path = str(tmp_path / "filename.bin")
    selections = iter([path, ""])
    monkeypatch.setattr(verify_files.filedialog, "askopenfilename", lambda **_kw: next(selections))
    mode.select_file()
    assert mode.file_path == path
    assert mode.selected_file_path["text"] == path
    assert mode.filename_label["text"] == "filename.bin"
    mode.select_file()
    assert mode.file_path == path


def test_clear_resets_result_and_selection(mode, tmp_path):
    """Reset removes all state, then requires valid input again."""
    prepare_file(mode, tmp_path)
    mode.verify()
    wait_for_result(mode)
    mode.clear()
    assert not mode.file_path
    assert mode.expected_hash_var.get() == ""
    assert mode.result_label["text"] == ""
    assert mode.progress_bar["value"] == 0
    assert mode.verify_button["state"] == "disabled"


def test_edit_clears_stale_result(mode, tmp_path):
    """A successful status cannot describe subsequently edited inputs."""
    prepare_file(mode, tmp_path)
    mode.verify()
    wait_for_result(mode)
    mode.expected_hash_var.set("a" * 16)
    assert mode.result_label["text"] == ""
    assert mode.progress_bar["value"] == 0
    assert mode.verify_button["state"] == "disabled"
    mode.algorithm_var.set("MD5")
    mode.expected_hash_var.set("900150983cd24fb0d6963f7d28e17f72")
    assert mode.verify_button["state"] == "normal"


def test_busy_lock_progress_and_dispose(mode, tmp_path, monkeypatch):
    """Hashing stays off the UI thread; disposed workers cannot touch widgets."""
    prepare_file(mode, tmp_path)
    entered = threading.Event()
    release = threading.Event()
    stopped = threading.Event()
    main_thread = threading.get_ident()

    def blocked_hash(_path, _algorithm, progress_callback):
        assert threading.get_ident() != main_thread
        try:
            progress_callback(1, 3)
            entered.set()
            assert release.wait(3)
            progress_callback(2, 3)
            return ABC_SHA256
        finally:
            stopped.set()

    monkeypatch.setattr(verify_files, "calculate_file_hash", blocked_hash, raising=False)
    mode.verify()
    try:
        assert entered.wait(3)
        for widget in (mode.select_button, mode.algorithm_select, mode.expected_hash,
                       mode.verify_button, mode.clear_button):
            assert widget["state"] == "disabled"
        mode.parent.pump()
        assert "1 / 3 bytes" in mode.progress_label["text"]
        mode.clear()
        assert mode.file_path
        mode.dispose()
        for widget in mode.parent.children:
            widget.destroy()
        assert not mode.parent.pending
        release.set()
        assert stopped.wait(3)
        mode.parent.pump()
    finally:
        release.set()


def test_empty_file_completes_progress(mode, tmp_path):
    """Zero bytes still report a completed successful verification."""
    prepare_file(mode, tmp_path,
                 "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
    with open(mode.file_path, "wb"):
        pass
    mode.verify()
    wait_for_result(mode)
    assert "verified" in mode.result_label["text"].lower()
    assert mode.progress_bar["value"] == 100
    assert "0 / 0 bytes" in mode.progress_label["text"]
