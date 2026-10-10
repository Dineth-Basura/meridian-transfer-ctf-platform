# MT-05 – The Offset in the Handover Log

Stage ID & Title: MT-05 – The Offset in the Handover Log

Domain: Digital Forensics

Difficulty: Moderate-Hard. Estimated solve time: 30–45 minutes. Value: 300 points.

Difficulty justification: Players must distinguish completed exports from plausible failures and views, convert explicit offset timestamps and epoch milliseconds, and join three independent evidence sources. Nearby times, mismatched identifiers and a duplicate timestamp prevent single-source inference. Difficulty comes from correlation rather than data volume.

Scenario: The Meridian Transfer portal and a synthetic analyst workstation appear to disagree about a restricted handover. All data is fictional; no real history, personal information, credentials or external systems are involved.

Learning Objective: Evidence integrity and SHA-256 verification; inventory and triage; structured log, CSV and SQLite analysis; timestamp interpretation, timezone normalization and UTC conversion; identifier correlation; failed versus completed actions; corroboration and deterministic flag derivation.

Challenge Environment: CTFd 3.8.7 on Ubuntu 24.04 VirtualBox. Offline ZIP with web_access.log, application_audit.csv, browser_history.sqlite, schema_guide.txt, case_context.txt and EVIDENCE_SHA256SUMS. No service or runtime network is introduced by MT-05.

Player Task: Verify the outer archive hash and inner hashes; preserve originals; read schema/context; identify exactly one completed restricted export supported by all three sources; serialize and hash the event using the published contract.

Flag Location / Logic: No literal flag is stored in the public package. Canonical value is `event_id|YYYY-MM-DDTHH:MM:SSZ|record_id`, using the application timestamp normalized to UTC, lowercase ASCII IDs, uppercase Z, literal pipes, exact seconds and no whitespace or trailing newline. Encode UTF-8, SHA-256, take exactly the first 16 lowercase hex characters and wrap as `MT{mt05_<digest16>}`.

Required Tools: sha256sum, file, unzip, grep, Python 3 standard library, sqlite3/CSV inspection tools; jq optional.

Dependencies: No Internet and no earlier challenge flag required. Author build and tests use Python standard library only. Python 3.12.3 and the recorded SQLite version are the tested build environment.

Expected Solution Path: Verify hashes, inventory files, read case/context and schemas, filter application completed exports in the start-inclusive/end-exclusive UTC window and restricted family, match web GET export/HTTP 200 with identical event ID, record ID and normalized time, then corroborate browser export URL identifiers within absolute 60 seconds inclusive. Reject all decoys. Construct canonical UTF-8 bytes, compute SHA-256, truncate and submit.

Validation: 40 unittest checks include manifest integrity, exact archive inventory, read-only SQLite, offset and date-boundary conversions, positive and negative 60-second boundaries, unique selection, malformed canonical values, independent solver intermediate agreement, leaks, repeated builds and three restore cycles. Live CTFd checks cover downloads, wrong/correct submissions, duplicate scoring, prior attachments/configuration/solves and browser UI. Independent human review remains PENDING.

Hints: Two free hints (cost 0 each):
1. The timestamp suffix or epoch definition determines the conversion. Normalize the relevant application event before correlating it.
2. Correlate identifiers and completion status first. Use browser history as corroboration, then build the canonical value exactly as specified.

Reset / Recovery: Keep the baseline ZIP untouched. Extract to a temporary working directory, modify a working evidence file and confirm a checksum mismatch, delete only that temporary directory, rebuild from fixed MERIDIAN-MT05-V1 source, compare archive hashes, then verify fresh download. Never delete the CTFd challenge or solves. Three local working-copy cycles are covered by T40.

Expected Skills: Basic command line, integrity hashing, structured text filtering, SQL SELECT queries, timestamp arithmetic, identifier joins and byte-exact hashing.

Responsible Member: Member 03

Reviewer: Member 02

Integration Reviewer: Member 04

Implementation Status: IMPLEMENTED BUT NOT VERIFIED. Automated checks do not substitute for human review.

## Dataset and determinism

Source identifier: MERIDIAN-MT05-V1. Investigation window: 2026-10-17T08:00:00Z inclusive to 2026-10-17T11:00:00Z exclusive. Application format is explicit +05:30, web logs use UTC +0000, browser times are Unix epoch milliseconds. Browser corroboration is absolute time difference <=60 seconds inclusive. Web entries must match the exact normalized audit second. The public context defines all these rules.

49 audit rows, 49 web rows and 48 browser rows. Decoys include failed/cancelled exports, normal views, out-of-window completions (both window boundaries), unrelated records, mismatched web event IDs, mismatched browser IDs/records, a 61-second browser visit, a duplicate timestamp on another record, failed HTTP status and a missing browser visit. Only one row meets all criteria.

Build uses fixed rows, stable SHA-256 ordering, explicit SQLite schema/insertion order/VACUUM, fixed ZIP timestamps, member ordering, permissions and compression. Repeated builds are byte-identical on the tested Python/SQLite/zlib environment, including SQLite bytes. Cross-version SQLite/zlib byte identity is not promised; keep the baseline archive for a live event and test a toolchain upgrade before replacing it.

## Commands

```bash
python3 challenges/mt-05-offset-handover-log/author/build_mt05.py
python3 challenges/mt-05-offset-handover-log/author/validate_dataset.py
python3 -m unittest discover challenges/mt-05-offset-handover-log/tests -v
python3 challenges/mt-05-offset-handover-log/author/validate_public_release.py
python3 platform/setup_mt05.py
python3 platform/test_mt05_functional.py
```

Both reference solver CLIs accept a public directory and print the flag by default; `--details` emits intermediate answers for private author comparison only. Never publish or paste that output. Their implementations share no selection/canonicalization functions. Solver 1 uses dictionary joins; solver 2 uses an in-memory SQL join and separate parsing/serialization.
