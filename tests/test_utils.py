"""Shared digest validation independent of the UI."""

import pytest

from src.utils import AppUtils


@pytest.mark.parametrize("algorithm,name,length", [
    ("SHA-256", "sha256", 64), ("SHA-512", "sha512", 128),
    ("SHA-1", "sha1", 40), ("MD5", "md5", 32),
])
def test_algorithm_rules(algorithm, name, length):
    """Each supported algorithm maps to its real digest length."""
    assert AppUtils.get_hashlib_algorithm(algorithm) == name
    assert AppUtils.is_valid_hash("aB" * (length // 2), algorithm)
    assert AppUtils.is_valid_hash(" \n" + "a" * length + "\t", algorithm)
    assert not AppUtils.is_valid_hash("a" * (length - 1), algorithm)
    assert not AppUtils.is_valid_hash("a" * (length + 1), algorithm)
    assert not AppUtils.is_valid_hash("g" * length, algorithm)
    assert not AppUtils.is_valid_hash("１" * length, algorithm)
    assert not AppUtils.is_valid_hash("a" * (length - 1) + " ", algorithm)
    assert not AppUtils.is_valid_hash("", algorithm)


def test_normalize_and_match():
    """Case and surrounding whitespace do not change a digest."""
    assert AppUtils.normalize_hash(" \nAB12\t") == "ab12"
    assert AppUtils.hashes_match(" AB12 ", "ab12")
    assert not AppUtils.hashes_match("ab12", "ab13")


def test_unknown_algorithm():
    """Unknown algorithms are rejected rather than silently defaulting."""
    assert not AppUtils.is_valid_hash("a" * 64, "unknown")
    with pytest.raises(ValueError, match="algorithm"):
        AppUtils.get_hashlib_algorithm("unknown")
