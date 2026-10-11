"""Known digests, bounded reads, progress and filesystem failures."""

import builtins

import pytest

from src import hashing
from src.hashing import calculate_file_hash as calculate


@pytest.mark.parametrize("algorithm,digest", [
    ("SHA-256", "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),
    ("SHA-512", "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a"
     "2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f"),
    ("SHA-1", "a9993e364706816aba3e25717850c26c9cd0d89d"),
    ("MD5", "900150983cd24fb0d6963f7d28e17f72"),
])
def test_known_abc_digest(tmp_path, algorithm, digest):
    """Use standard published vectors, including three separate chunks."""
    path = tmp_path / "abc.bin"
    path.write_bytes(b"abc")
    assert calculate(str(path), algorithm, chunk_size=1) == digest


def test_empty_file(tmp_path):
    """The empty digest and final progress are defined without division."""
    path = tmp_path / "empty"
    path.write_bytes(b"")
    progress = []
    assert calculate(str(path), "SHA-256", progress_callback=lambda *p: progress.append(p)) == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    assert progress == [(0, 0)]


def test_binary_file_and_progress(tmp_path):
    """All byte values survive streaming; progress counts actual bytes."""
    path = tmp_path / "binary"
    path.write_bytes(bytes(range(256)))
    progress = []
    assert calculate(str(path), "SHA-256", 100, lambda *p: progress.append(p)) == (
        "40aff2e9d2d8922e47afd4648e6967497158785fbd1da870e7110266bf944880"
    )
    assert progress == [(0, 256), (100, 256), (200, 256), (256, 256)]


def test_large_file_uses_bounded_reads(tmp_path, monkeypatch):
    """A 2.4 MB file is opened once and never read into memory at once."""
    path = tmp_path / "large"
    path.write_bytes(b"abc" * 800000)
    sizes = []
    opened = []
    real_open = builtins.open

    class RecordingFile:
        """Record actual reads while keeping the filesystem real."""

        def __enter__(self):
            self.stream = real_open(path, "rb")
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def fileno(self):
            """Allow the real file's size to be queried."""
            return self.stream.fileno()

        def read(self, size=-1):
            """Record each bounded request to the real file."""
            sizes.append(size)
            return self.stream.read(size)

    def record_open(file_path, mode):
        opened.append((file_path, mode))
        return RecordingFile()

    monkeypatch.setattr(hashing, "open", record_open, raising=False)
    assert calculate(str(path), "SHA-256") == (
        "e1381e6d3ad0640c2af9014bf5645c446b7681506808656462a0ddef3de5f605"
    )
    assert opened == [(str(path), "rb")]
    assert sizes == [1024 * 1024] * 4


def test_missing_file(tmp_path):
    """A missing path reaches the caller as FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        calculate(str(tmp_path / "missing"), "SHA-256")


@pytest.mark.parametrize("error", [PermissionError("denied"), OSError("read failed")])
def test_open_error_propagates(monkeypatch, error):
    """Read permissions are mocked reliably across Windows and Linux."""
    def fail_open(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(builtins, "open", fail_open)
    with pytest.raises(type(error), match=str(error)):
        calculate("unreadable", "SHA-256")


@pytest.mark.parametrize("chunk_size", [0, -1])
def test_invalid_chunk_size(chunk_size):
    """Reject invalid chunks before opening an arbitrary path."""
    with pytest.raises(ValueError, match="chunk"):
        calculate("missing", "SHA-256", chunk_size)


def test_unknown_algorithm():
    """An unsupported algorithm must fail before the file is read."""
    with pytest.raises(ValueError, match="algorithm"):
        calculate("missing", "unknown")
