"""Utilities for the application."""

import string


class AppUtils:
    """Utility functions for the application."""

    ALGORITHMS = {
        "SHA-256": ("sha256", 64),
        "SHA-512": ("sha512", 128),
        "SHA-1": ("sha1", 40),
        "MD5": ("md5", 32),
    }

    @staticmethod
    def normalize_hash(value: str) -> str:
        """Ignore surrounding whitespace and hexadecimal letter case."""
        return value.strip().lower()

    @classmethod
    def is_valid_hash(cls, value: str, algorithm: str) -> bool:
        """Require the selected algorithm's exact ASCII hexadecimal length."""
        metadata = cls.ALGORITHMS.get(algorithm)
        if metadata is None:
            return False
        digest = cls.normalize_hash(value)
        return len(digest) == metadata[1] and all(
            character in string.hexdigits for character in digest
        )

    @classmethod
    def hashes_match(cls, first: str, second: str) -> bool:
        """Compare normalized digests; callers validate them first."""
        return cls.normalize_hash(first) == cls.normalize_hash(second)

    @classmethod
    def get_hashlib_algorithm(cls, algorithm: str) -> str:
        """Translate a display name, rejecting unsupported algorithms."""
        try:
            return cls.ALGORITHMS[algorithm][0]
        except KeyError as error:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}") from error

    @staticmethod
    def concat_str(str1, str2) -> str:
        """Concatenate two strings with a newline for each one."""
        return str1 + "\n" + str2 + "\n"
