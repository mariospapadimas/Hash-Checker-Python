# Verify Files + Core Tests Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline, with TDD and one fresh whole-branch review. This is the user's already approved plan, recovered from the lost session.

**Goal:** Complete responsive file verification for SHA-256, SHA-512, SHA-1 and MD5 and add the first pytest suite.

**Architecture:** Preserve `src/app.py`, `src/utils.py` and `src/modes/`. Add only `src/hashing.py` for pure chunked hashing. AppUtils owns algorithm metadata, normalization and validation. Workers communicate through a queue; only Tk's main thread touches widgets.

**Tech Stack:** Python 3.9–3.11, Tkinter/ttk, hashlib, threading, queue, pytest.

**Spec:** The user-supplied implementation plan and follow-up instructions in this chat. No separate spec file was recovered.

## Global Constraints

- SHA-256 is the default in both modes.
- Accept hexadecimal digests of the selected algorithm's exact length; trim surrounding whitespace and compare without case sensitivity.
- Read files in 1 MiB chunks; keep UI responsive with byte progress.
- Switching modes must not update destroyed widgets.
- Preserve clear empty-input, unreadable-file and mismatch warnings.
- Apply shared rules to Compare Hashes at the end, as requested by the user.
- Make frequent focused commits using the existing user Git identity, without co-authors; push a new branch and open a draft PR.
- CI matrix, coverage thresholds, Actions maintenance and performance benchmarking belong to the next milestone.

## Review Focus

- Rapid mode switches during hashing: cancel polling and stop the abandoned worker cooperatively.
- Empty files: finish successfully and show complete progress without dividing by zero.
- Cancelled file dialog: preserve any previous selection.
- Edits after a result: clear stale verification status and update button eligibility.
- Long paths and long SHA-512 digests: wrap display text and keep controls accessible at 800x600.

### Task 1: Shared hash rules

**Files:** `src/utils.py`, `tests/test_utils.py`, `pyproject.toml`, `uv.lock`.

**Interfaces:** Produce `AppUtils.ALGORITHMS`, `normalize_hash(value: str) -> str`, `is_valid_hash(value: str, algorithm: str) -> bool`, `hashes_match(first: str, second: str) -> bool`, `get_hashlib_algorithm(algorithm: str) -> str`.

- [x] Write parameterized tests for algorithm lengths 64/128/40/32, mixed case, whitespace, invalid hex, empty values, unsupported algorithm and normalization.
- [x] Run tests first: expect assertion failures for missing shared rules.
- [x] Implement metadata and strict validation using ASCII hexadecimal characters.
- [x] Run targeted tests and full suite: expect all pass.
- [x] Commit shared rules and test harness.

### Task 2: Pure chunked hashing

**Files:** `src/hashing.py`, `tests/test_hashing.py`.

**Interfaces:** Consume AppUtils algorithm mapping. Produce `calculate_file_hash(file_path: str, algorithm: str, chunk_size: int = 1024 * 1024, progress_callback=None) -> str`; callback receives processed and total bytes.

- [x] Write literal known `b"abc"` digest tests for all algorithms, empty file, small/binary/multichunk data, progress completion, missing file and reliable mocked permission/read failures.
- [x] Test zero/negative chunk sizes and unsupported algorithms before reading.
- [x] Run tests first: expect failures because hashing is absent.
- [x] Implement hashlib streaming, use the opened file's size for progress and propagate OSError.
- [x] Run hashing tests and full suite: expect all pass.
- [x] Commit hashing core.

### Task 3: Responsive Verify Files

**Files:** `src/modes/verify_files.py`, `src/app.py`, `tests/test_verify_files.py`, `tests/test_app.py`, `tests/helpers.py`.

**Interfaces:** Consume shared rules and calculate_file_hash. Produce mode methods `verify()`, `clear()`, `dispose()` and queue-driven result handling; HashChecker retains and disposes its active mode before widget destruction.

- [x] Write deterministic behavior tests with lightweight widget doubles for no selection, invalid/empty digest, successful match, mismatch, read failures, selected-file hashing, selection/cancel, busy locking, reset, progress, stale edits and disposal.
- [x] Run before implementation: expect failures for missing verification behavior.
- [x] Add filename and wrapped path, readonly algorithm selector, expected input, Verify/Clear controls, wrapped status and determinate progress.
- [x] Run daemon worker with queue-only events; lock editing while hashing; poll with after and restore controls on completion or error.
- [x] On disposal cancel scheduled polling and signal cooperative worker cancellation, without blocking mode switches.
- [x] Remove debugging print and retain active mode in controller.
- [x] Run mode tests and full suite: expect all pass.
- [x] Commit in focused UI/lifecycle units.

### Task 4: Compare Hashes and final verification

**Files:** `src/modes/compare_hashes.py`, `tests/test_compare_hashes.py`, test configuration as needed.

**Interfaces:** Consume the same AppUtils metadata and shared rules; default algorithm SHA-256. Produce strict validation and normalized comparison in `check()`.

- [x] Write behavior tests for empty first/second/both, invalid hex, short and exactly 16-character values, valid algorithm digests, match/mismatch and case equivalence.
- [x] Run first: expect failures for old minimum-length validation and case-sensitive comparison.
- [x] Add selector and replace old validation using shared rules; preserve mismatch warning.
- [x] Run targeted tests and full suite: expect all pass.
- [x] Run Pylint on every tracked Python file with fail-under=9.0.
- [x] Commit compare-mode upgrade and remaining configuration separately when meaningful.
- [x] Request one fresh whole-branch review; fix important findings with failing regressions first.
- [x] Run final suite and Pylint, push feature branch and create draft PR for the user's code review.

## Acceptance

All four algorithms work in both modes. File hashing is chunked and responsive, displays byte progress, handles errors, clears state and survives switching modes. All pytest tests and current Pylint policy pass. Do not merge; the user reviews all code.
