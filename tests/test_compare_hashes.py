"""Compare-mode behavior uses shared, strict algorithm validation."""

from types import SimpleNamespace

import pytest

from src.modes import compare_hashes
from tests.helpers import FakeParent, FakeVariable, FakeWidget


@pytest.fixture(name="mode")
def compare_mode(monkeypatch):
    """Only Tk construction is fake; the real check handler runs."""
    monkeypatch.setattr(compare_hashes.tk, "StringVar", FakeVariable)
    for name in ("Entry", "Label", "Button"):
        monkeypatch.setattr(compare_hashes.tk, name, FakeWidget)
    if hasattr(compare_hashes, "ttk"):
        monkeypatch.setattr(compare_hashes.ttk, "Combobox", FakeWidget)
    return compare_hashes.CompareHashesMode(
        FakeParent(), SimpleNamespace(main_text_font="font")
    )


def enter_hashes(mode, first, second, algorithm="SHA-256"):
    """Supply inputs at the Entry boundary without a display."""
    mode.first_hash.options["text"] = first
    mode.second_hash.options["text"] = second
    mode.algorithm_var.set(algorithm)


def test_defaults_to_sha256(mode):
    """New comparisons start with the sensible default algorithm."""
    assert mode.algorithm_var.get() == "SHA-256"


@pytest.mark.parametrize("first,second", [("", "a" * 64), ("a" * 64, ""), ("", ""),
                                        (" \t", "a" * 64)])
def test_empty_hashes(mode, first, second):
    """Any missing input asks for both hashes."""
    enter_hashes(mode, first, second)
    mode.check()
    assert "enter both" in mode.result_label["text"].lower()


@pytest.mark.parametrize("invalid", ["a" * 15, "a" * 16, "g" * 64,
                                   "a" * 63, "a" * 65, "a" * 31 + " " + "a" * 32])
@pytest.mark.parametrize("invalid_first", [True, False])
def test_invalid_digest_is_rejected(mode, invalid, invalid_first):
    """Both fields require exact-length hexadecimal digests."""
    first, second = (invalid, "a" * 64) if invalid_first else ("a" * 64, invalid)
    enter_hashes(mode, first, second)
    mode.check()
    assert "valid" in mode.result_label["text"].lower()
    assert "SHA-256" in mode.result_label["text"]


@pytest.mark.parametrize("algorithm,length", [("SHA-256", 64), ("SHA-512", 128),
                                            ("SHA-1", 40), ("MD5", 32)])
def test_normalized_matching_hashes(mode, algorithm, length):
    """Matching works for every algorithm, ignoring case and edge whitespace."""
    enter_hashes(mode, " \n" + "AB" * (length // 2), "ab" * (length // 2) + "\t", algorithm)
    mode.check()
    assert "hashes match!" in mode.result_label["text"].lower()


def test_valid_mismatch_warns(mode):
    """A valid disagreement preserves the corruption/malicious warning."""
    enter_hashes(mode, "a" * 64, "b" * 64)
    mode.check()
    text = mode.result_label["text"].lower()
    assert "mismatch" in text
    assert "corrupted or malicious" in text
