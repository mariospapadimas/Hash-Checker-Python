# Verify Files implementation record

Implemented on `codex/verify-files`, starting at `97a2a82`. All commits use
the existing Git identity, Marios Papadimas, without co-author trailers.

## Verified

- Shared strict digest rules in both modes, default SHA-256.
- SHA-256, SHA-512, SHA-1 and MD5 chunked hashing with known-vector tests.
- Responsive verification, byte progress, reset, input guards and read errors.
- Safe mode switching and cancellation; workers own no UI objects.
- Full paths in a bounded, wrapped, scrollable display.
- 63 tests pass with `HASH_CHECKER_UI_TESTS=1`; normal headless run has
  62 passing tests and one deliberately skipped desktop layout test.
- Pylint on all tracked Python files: 10.00/10, using `--fail-under=9.0`.
- Hidden Windows/Tk smoke: default mode and algorithm, actual file match,
  switching during 64 MiB hashing, long paths through 3,000 characters;
  zero obsolete modes retained after garbage collection.

## Independent review and fixes

One fresh whole-branch reviewer found no critical issues and two important issues.
Both were fixed with regression tests watched fail before the changes:

- Tcl traces retained disposed modes. Tests now verify real Tcl trace cleanup
  and that an abandoned worker does not retain its UI mode.
- Very long paths hid essential controls. An opt-in real Tk test now verifies
  controls remain mapped at 800x600, the full path is retained and it scrolls.

The author ran the full suite after each fix; no second independent review was
performed, as prescribed by the executing-plans workflow.

## Deferred minor

Compare Hashes can retain the previous status after editing a hash or choosing
another algorithm. Press Check Hashes to recompute. The reviewer classified this
as minor; automatic status clearing is deferred.

## Rulings, in order

1. Work in the allowed checkout on a new branch, archiving the unused native
   worktree outside writable roots. Cost if wrong: less checkout isolation;
   the main branch itself was not changed.
2. Upgrade Compare Hashes last, following the user's instruction. Cost if wrong:
   its old validation stayed in place until the final feature task.
3. Install/configure pytest in Task 1 rather than Task 4 to enable TDD. Cost if
   wrong: dependency setup appears earlier in the commit history.
4. Add one opt-in rendered regression for the concrete geometry defect while
   keeping default CI headless. Cost if wrong: headless CI cannot detect later
   rendered layout regressions.
5. Keep CI matrices, coverage thresholds, Actions runtime maintenance and chunk
   benchmarks in the next milestone, as explicitly scoped. Cost if wrong:
   version/platform and performance verification remains incomplete.
6. Defer exhaustive platform/DPI UI verification. Cost if wrong: other desktop
   configurations may lay out differently from the tested Windows environment.
7. Keep hashing as a single opened stream without snapshot guarantees. Cost if
   wrong: concurrent file writes can change bytes or progress totals mid-check.
8. Retain current bounded-queue polling after review found no demonstrated
   starvation under one progress event per MiB. Cost if wrong: an unusually fast
   producer could delay other UI events.

## Delivery

Draft PR: https://github.com/mariospapadimas/Hash-Checker-Python/pull/11

GitHub CI passed: Python application tests and Pylint for Python 3.8, 3.9, 3.10.
The PR is draft for the user's code review; no merge was performed.

