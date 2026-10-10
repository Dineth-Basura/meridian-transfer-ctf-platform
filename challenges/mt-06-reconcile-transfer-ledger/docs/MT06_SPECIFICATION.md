# MT-06 – Reconcile the Transfer Ledger

Stage ID & Title: MT-06 – Reconcile the Transfer Ledger
Domain: Programming / Scripting
Difficulty: Hard
Value: 400 fixed points
Estimated solve time: 40–60 minutes
Responsible: Member 03
Reviewer: Member 02
Integration reviewer: Member 04
Implementation Status: IMPLEMENTED BUT NOT VERIFIED — independent human review PENDING.

## Difficulty justification

The algorithm uses only the Python standard library, but correct results require composing validation, offset normalization, filtering, retry handling, tie breaking and byte serialization across 1,000 physical rows. Invalid inputs must be counted without crashing, while semantic duplicate conflicts are fatal. A manageable parser is sufficient; no brute force or remote execution is needed.

## Scenario

The Meridian Transfer investigation reaches its final reconciliation stage. A synthetic ledger contains valid transfers, unrelated cases, failed operations, retries, malformed rows, out-of-window records and mixed timestamp offsets. Manual reconciliation is unreliable. The review team supplies all non-secret incident context independently of prior stages.

## Learning Objective

Practice Python scripting, JSONL parsing, schema validation, robust error handling, strict Base64, UTF-8, timezone-aware datetime parsing, UTC normalization, filtering, deduplication, deterministic sorting, exact byte serialization, SHA-256, test-driven reasoning and explainable automation.

## Challenge Environment

CTFd 3.8.7 on the existing Ubuntu 24.04 VirtualBox VM. Participant computation runs locally on Python 3 (Kali or another system). All evidence is synthetic, static and offline. There is no server-side arbitrary-code grader or participant execution inside CTFd.

## Player Task

Verify outer SHA-256, extract the evidence, verify all six inner hashes and read `schema.json`, `incident_context.json` and the worked example. Write a reproducible parser following the complete public contract in `public/README.txt` and `schema.json`. Exactly 1,000 physical LF-terminated JSONL rows include intentionally malformed/incomplete rows. Count invalid rows before filtering. Unknown extra fields are ignored.

## Flag Location / Logic

The flag is derived, not stored literally in the public evidence. Validate the six required string fields and lowercase ASCII identifiers; parse exact-second offset-aware timestamps; require canonical strict Base64 and valid nonempty UTF-8 tokens without CR/LF. Preserve all other token characters.

Across all schema-valid rows, repeated event IDs must have the same case, record, status, normalized timestamp and token bytes. Conflicts are fatal dataset errors, even if a row is later excluded. Equivalent offset representations are identical semantic times. Invalid rows do not participate in duplicate checks.

Filter matching case, allowed record, exact `completed` status and UTC interval `[start_utc, end_utc)`. Deduplicate by event ID before final sorting. Sort normalized UTC time ascending, then event ID in ASCII ascending order. Join decoded token strings using one LF between tokens, no final LF, no CR, no added spaces, no JSON and no event IDs. Hash exact UTF-8 bytes using SHA-256, then use the first 32 lowercase hexadecimal characters: `MT{mt06_<digest32>}`. An empty toy selection hashes empty bytes; production is nonempty.

## Required Tools / Dependencies

Python 3 standard library, text editor, `sha256sum`, `unzip`; optional `jq`. No Internet, previous-stage flag, third-party Python dependency or Docker workspace is required. Authoring uses Python 3.12.3 and deterministic standard-library ZIP compression.

## Expected Solution Path

Stream the lines, catch JSON/schema/time/Base64/UTF-8 failures, count rejected rows, compare semantic duplicates, filter, collapse retries, sort, decode and join tokens, encode UTF-8, hash and truncate. The small worked example demonstrates a retry, failed/out-of-window events, offset normalization and tie breaking. The two author solvers independently implement the algorithm (procedural dictionaries versus immutable event objects); only archive paths and the published rules overlap conceptually.

## Validation

`tests/test_mt06.py` covers T01–T64 and additional adversarial checks. It checks all required boundary events, Z/positive/negative offsets and date conversion, conflicts, exact bytes, empty selection, full intermediate solver agreement, wrong solutions, deterministic builds, public leakage and three corruption/recovery cycles. `validate_dataset.py` independently reads public data and compares both solvers before optional private comparisons. `validate_public_release.py` reads only public material and derives its own comparison values.

Run from the project root:

```bash
python3 challenges/mt-06-reconcile-transfer-ledger/author/build_mt06.py
python3 challenges/mt-06-reconcile-transfer-ledger/author/validate_dataset.py
python3 -m unittest discover challenges/mt-06-reconcile-transfer-ledger/tests -v
python3 challenges/mt-06-reconcile-transfer-ledger/author/reference_solver.py
python3 challenges/mt-06-reconcile-transfer-ledger/author/independent_reference_solver.py
python3 challenges/mt-06-reconcile-transfer-ledger/author/validate_public_release.py
python3 platform/setup_mt06.py
python3 platform/test_mt06_functional.py
MT_UI_RESULT_PATH="$PWD/.secrets/mt06_ui_browser_result.json" node platform/test_ui_browser.cjs
```

Solver CLIs print derived answers; capture output privately when producing shareable execution logs. The functional test uses only downloaded participant evidence for MT-06, compares both complete solver results, tests wrong/malformed/correct/repeated flags and preserves existing solves. It paces submissions to respect CTFd's protection. The original five-stage snapshot is created once with `--snapshot` before first integration; do not overwrite it.

## Hints

1. Separate parsing, validation, filtering and output construction. Count rejected rows rather than allowing one bad line to terminate the whole analysis.
2. Deduplicate by event_id before final sorting. Sort by normalized UTC time then event_id, and check the exact no-final-newline serialization rule.

Both hints cost zero. No prerequisite. Static scoring only.

## Reset / Recovery

Preserve the original archive. Modify only a temporary extracted copy to demonstrate checksum failure, delete that working copy, rerun the deterministic builder and compare archive bytes and derived solution. The unit suite performs three such cycles; the functional test additionally checks three baseline builds leave CTFd solve IDs unchanged. Do not delete/recreate challenges, reset databases or delete participants/solves. Cross-toolchain zlib byte identity is not promised; baseline reproducibility is tested on the recorded toolchain.

## Expected Skills

Basic Python functions, loops, dictionaries, exceptions, JSON, binary/text distinctions, datetime offsets, deterministic ordering and checksum verification. The learner should explain each inclusion/exclusion and serialization choice.

## Human validation boundary

The reviewer-only package is `review/mt-06-independent/`. Member 02 must write an independent parser using participant-facing material and complete the blank review template. Automated technical E2E is not human acceptance. Full load and full-platform backup/restore tests remain separately pending unless executed and documented.
