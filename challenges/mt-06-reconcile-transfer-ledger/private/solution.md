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


## Private solution
Parse events.jsonl line-by-line as UTF-8. There are exactly 1000 physical
rows, including intentionally malformed JSON and schema-invalid records.
Count and skip invalid rows; validate ALL rows before filtering. Required fields
are strings: event_id, case_id, record_id, status, timestamp, token_b64.
Identifiers match [a-z][a-z0-9-]* (ASCII). Extra fields are ignored.
Timestamps use YYYY-MM-DDTHH:MM:SS followed by Z or +/-HH:MM; hours 00–23,
offset minutes 00–59, exact seconds, valid calendar date, no naive times,
fractional seconds or leap seconds. Normalize to UTC.
token_b64 uses canonical standard RFC 4648 Base64 with required padding,
strict alphabet validation, and no whitespace. Re-encoding decoded bytes must
match the original. Bytes must decode as UTF-8. Tokens are nonempty and contain
no CR or LF. Preserve all other token characters, including any spaces.
Validate duplicate event_id values across ALL schema-valid rows. Their semantic
values (case_id, record_id, status, normalized timestamp, token bytes) must agree.
An equivalent timestamp offset is not a conflict. Ignore invalid rows for this
check. Any conflicting duplicate is a fatal DATASET ERROR; never choose one.
Select rows only when case_id exactly matches incident_context.json, record_id
is in allowed_record_ids, status is exactly completed, and normalized time is
>= start_utc AND < end_utc (start inclusive, end exclusive).
Collapse identical qualifying retries by event_id BEFORE final sorting.
Sort by normalized UTC timestamp ascending, THEN event_id ascending using ASCII
ordering. Decode selected tokens and join the token strings with one LF (0x0A)
between adjacent tokens. Do not strip tokens, add spaces, include event IDs,
serialize JSON, use CRLF, or append a final LF. Encode the result as UTF-8.
Compute SHA-256; use the FIRST 32 lowercase hexadecimal digest characters.
Submit MT{mt06_<digest32>}. An empty toy selection hashes empty bytes; the
production dataset is guaranteed to have a nonempty selection.
No earlier stage secret is required. All context is supplied locally.

Use streaming JSONL parsing with robust exceptions. Validate before filtering; normalize timezone-aware datetime values; compare semantic duplicate tuples; sort deterministically and hash exact UTF-8 bytes. Empty toy selections are allowed, but production must be nonempty.

{
  "physical_rows": 1000,
  "rejected_rows": 414,
  "candidate_rows": 28,
  "selected_count": 20,
  "retries": 8,
  "selected": [
    {
      "event_id": "ev-40094",
      "record_id": "ledger-north",
      "utc_timestamp": "2026-10-17T08:00:00Z",
      "token": "Transfer/d73bc99cb505d:Ready"
    },
    {
      "event_id": "ev-54045",
      "record_id": "ledger-north",
      "utc_timestamp": "2026-10-17T08:04:00Z",
      "token": "Transfer/835038ffeacad:Ready"
    },
    {
      "event_id": "ev-75705",
      "record_id": "ledger-east",
      "utc_timestamp": "2026-10-17T08:11:11Z",
      "token": "Transfer/4c516cd4ff37d:café"
    },
    {
      "event_id": "ev-68751",
      "record_id": "ledger-west",
      "utc_timestamp": "2026-10-17T08:18:22Z",
      "token": "Transfer/e883cc6708112:Review"
    },
    {
      "event_id": "ev-22091",
      "record_id": "ledger-south",
      "utc_timestamp": "2026-10-17T08:25:33Z",
      "token": "Transfer/aac545c7c3cb6:Δelta"
    },
    {
      "event_id": "ev-40020",
      "record_id": "ledger-south",
      "utc_timestamp": "2026-10-17T08:30:00Z",
      "token": "Transfer/5671a32123a49:Δelta"
    },
    {
      "event_id": "ev-54886",
      "record_id": "ledger-west",
      "utc_timestamp": "2026-10-17T08:30:00Z",
      "token": "Transfer/f74fd23db63e4:Review"
    },
    {
      "event_id": "ev-80506",
      "record_id": "ledger-north",
      "utc_timestamp": "2026-10-17T08:32:44Z",
      "token": "Transfer/70468cefdc6c1:Ready"
    },
    {
      "event_id": "ev-47506",
      "record_id": "ledger-east",
      "utc_timestamp": "2026-10-17T08:39:55Z",
      "token": "Transfer/26e94fc29d6bc:café"
    },
    {
      "event_id": "ev-95278",
      "record_id": "ledger-west",
      "utc_timestamp": "2026-10-17T08:47:06Z",
      "token": "Transfer/face78b9bdb80:Review"
    },
    {
      "event_id": "ev-10605",
      "record_id": "ledger-south",
      "utc_timestamp": "2026-10-17T08:54:17Z",
      "token": "Transfer/f718a6882da2c:Δelta"
    },
    {
      "event_id": "ev-95407",
      "record_id": "ledger-north",
      "utc_timestamp": "2026-10-17T09:01:28Z",
      "token": "Transfer/c164ecf31966e:Ready"
    },
    {
      "event_id": "ev-69064",
      "record_id": "ledger-east",
      "utc_timestamp": "2026-10-17T09:08:39Z",
      "token": "Transfer/15cd3ceb1df86:café"
    },
    {
      "event_id": "ev-15570",
      "record_id": "ledger-west",
      "utc_timestamp": "2026-10-17T09:15:50Z",
      "token": "Transfer/5ef125f302ae1:Review"
    },
    {
      "event_id": "ev-13762",
      "record_id": "ledger-south",
      "utc_timestamp": "2026-10-17T09:23:01Z",
      "token": "Transfer/8d926a6e34e36:Δelta"
    },
    {
      "event_id": "ev-16923",
      "record_id": "ledger-north",
      "utc_timestamp": "2026-10-17T09:30:12Z",
      "token": "Transfer/114ce025833e4:Ready"
    },
    {
      "event_id": "ev-70548",
      "record_id": "ledger-east",
      "utc_timestamp": "2026-10-17T09:37:23Z",
      "token": "Transfer/2197b64730b40:café"
    },
    {
      "event_id": "ev-26173",
      "record_id": "ledger-west",
      "utc_timestamp": "2026-10-17T09:44:34Z",
      "token": "Transfer/65db6af0149c7:Review"
    },
    {
      "event_id": "ev-69654",
      "record_id": "ledger-south",
      "utc_timestamp": "2026-10-17T09:51:45Z",
      "token": "Transfer/5b1ca3b7e5656:Δelta"
    },
    {
      "event_id": "ev-67826",
      "record_id": "ledger-east",
      "utc_timestamp": "2026-10-17T10:59:59Z",
      "token": "Transfer/7d48c978ee10e:café"
    }
  ],
  "serialized_hex": "5472616e736665722f643733626339396362353035643a52656164790a5472616e736665722f383335303338666665616361643a52656164790a5472616e736665722f346335313663643466663337643a636166c3a90a5472616e736665722f653838336363363730383131323a5265766965770a5472616e736665722f616163353435633763336362363ace94656c74610a5472616e736665722f353637316133323132336134393ace94656c74610a5472616e736665722f663734666432336462363365343a5265766965770a5472616e736665722f373034363863656664633663313a52656164790a5472616e736665722f323665393466633239643662633a636166c3a90a5472616e736665722f666163653738623962646238303a5265766965770a5472616e736665722f663731386136383832646132633ace94656c74610a5472616e736665722f633136346563663331393636653a52656164790a5472616e736665722f313563643363656231646638363a636166c3a90a5472616e736665722f356566313235663330326165313a5265766965770a5472616e736665722f386439323661366533346533363ace94656c74610a5472616e736665722f313134636530323538333365343a52656164790a5472616e736665722f323139376236343733306234303a636166c3a90a5472616e736665722f363564623661663031343963373a5265766965770a5472616e736665722f356231636133623765353635363ace94656c74610a5472616e736665722f376434386339373865653130653a636166c3a9",
  "serialized_length": 589,
  "sha256": "32f3e11d129dfe8a8646411e8e8576b9cce80664d76a53655256ef89e9db4f6b",
  "first32": "32f3e11d129dfe8a8646411e8e8576b9",
  "flag": "MT{mt06_32f3e11d129dfe8a8646411e8e8576b9}"
}
