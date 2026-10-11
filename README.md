[![Pylint](https://github.com/mariospapadimas/Hash-Checker-Python/actions/workflows/pylint.yml/badge.svg?branch=main)](https://github.com/mariospapadimas/Hash-Checker-Python/actions/workflows/pylint.yml)
[![Python App](https://github.com/mariospapadimas/Hash-Checker-Python/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/mariospapadimas/Hash-Checker-Python/actions/workflows/python-app.yml)
# Hash-Checker-Python
A Python/Tkinter app for comparing hashes and verifying files.

Supports SHA-256 (default), SHA-512, SHA-1 and MD5. Both modes require the
selected algorithm's exact hexadecimal digest length and ignore surrounding
whitespace and letter case.

Use Python 3.9–3.11 (the current project version constraint ends at 3.11.9):

```powershell
python -m src.main
```

In **Verify Files Mode**, select a file, choose the algorithm, paste the expected
hash and click **Verify File**. Hashing runs in the background with byte progress
and reads 1 MiB at a time. **Clear** resets the selection and result. You can
switch modes while a file is being hashed.

The expected hash should come from a source you trust. A match confirms that the
file has that digest; it does not establish who published the file.

For development, install [uv](https://docs.astral.sh/uv/) and run:

```powershell
uv sync --dev
uv run pytest -v
uv run pylint --fail-under=9.0 src tests
```

Code is under `src/`, tests under `tests/`. The tests use real file hashing and
worker threads with lightweight Tk widget doubles, so they also run headlessly.

There is also an optional rendered Tk layout test. On a machine with a desktop:

```powershell
$env:HASH_CHECKER_UI_TESTS = "1"
uv run pytest tests/test_tk_ui.py -v
```

***All code must follow python naming conventions and be PEP8 compliant.***
