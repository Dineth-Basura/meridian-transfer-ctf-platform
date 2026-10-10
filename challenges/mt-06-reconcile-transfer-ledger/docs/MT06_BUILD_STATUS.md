# MT-06 build status

Build timestamp: 2026-09-24T15:24:36.035451+00:00
Python version: 3.12.3
CTFd version: 3.8.7 (installed source and existing deployment)
CTFd challenge ID: 6
JSONL physical row count: 1000
ZIP byte size: 16406
ZIP SHA-256: 18779d10ed973f3ead659f67b04d032a1b882de7e29c3d31f681a387f91a38fa
Dataset source: MERIDIAN-MT06-V1
Case ID: meridian-transfer-review
Allowed record count: 4
Case window: [2026-10-17T08:00:00Z, 2026-10-17T11:00:00Z)
Final selected record count: 20
Rejected row count: 414
Deduplicated qualifying retry count: 8
Serialized byte length: 589

Dataset generation: PASS
1000 physical rows: PASS
Dataset validation: PASS
Boundary handling: PASS
Timezone normalization: PASS
Base64: PASS
Malformed rows: PASS
Wrong field types: PASS
UTF-8 decode: PASS
Identical retries: PASS
Conflicting duplicates: PASS
Equal timestamps: PASS
Sorting: PASS
Serialization: PASS
No-final-LF: PASS
SHA-256: PASS
First32 rule: PASS
Reference solver 1: PASS
Reference solver 2: PASS
Solver agreement: PASS
Worked example: PASS
Wrong-solution variants: PASS
Public validation: PASS
Outer checksum: PASS
Inner checksum: PASS
CTFd wrong flag: PASS
CTFd malformed flag: PASS
CTFd correct flag: PASS
Duplicate scoring: PASS
Participant downloads: PASS
Recovery: PASS
MT-01 regression: PASS
MT-02 regression: PASS
MT-03 regression: PASS
MT-04 regression: PASS
MT-05 regression: PASS
Browser/UI: PASS
Integration idempotence: PASS
Existing solve preservation: PASS
Automated technical E2E: PASS

Unit tests: 70/70 PASS (T01–T64 and six additional adversarial checks).
Working-copy corruption/recovery cycles: 3/3 PASS.
Live baseline rebuild/solution cycles: 3/3 PASS; CTFd solve IDs unchanged.
Configured fixed points: 100 + 150 + 200 + 250 + 300 + 400 = 1400 (programmatically verified).
Reviewer package: READY; exactly four participant-only files, template unfilled.
Human independent review: PENDING (Member 02).
Final status: IMPLEMENTED BUT NOT VERIFIED.

## Executed evidence

MT-05's automated pre-flight passed before MT-06 files were created; see its MT05_PRE_MT06_AUDIT.md. No human review was fabricated. Both MT-06 solver CLIs ran against only public downloads in a clean temporary workspace; no private expected values were copied into it. Complete result dictionaries agreed: rejection/candidate/selected/retry counts, event order, record IDs, UTC timestamps, token order, byte length, exact serialized bytes, digest/truncation and flag. Private expected files were compared only after independent computation.

The six-stage disposable participant downloaded each existing attachment and followed each reference path; MT-04 used the established training credentials and live application. Every stage rejected wrong and malformed flags, accepted the derived correct flag, and awarded points once. Total score was 1400. MT-01 historically uploads only its evidence file; its downloaded bytes were compared with the local public checksum. MT-06 downloaded both required files, verified outer and inner sha256sum manifests, and solved independently without a prerequisite flag.

Setup ran repeatedly with the same challenge ID, attachment metadata, hints and flags. Five-stage configuration snapshots (including attachments/hints/flags) and all prior correct submission IDs were preserved. Test users are hidden, and their solve history is retained.

Fresh browser regression covered guest access, registration, participant login/logout, admin role and denied participant admin access, six listings, MT-06 desktop/mobile detail/downloads, earlier attachments, submission, mobile layout and absence of JavaScript errors. Existing Chromium discovery was retained. Results went to .secrets/mt06_ui_browser_result.json, preserving unrelated tracked status edits.

## Failures investigated and corrected

- MT-04 container-only unit tests were initially invoked on the host and could not import app. The established container invocation then passed 24/24; live HTTP passed 9/9.
- The new E2E harness initially assumed MT-01 uploaded its manifest. It was corrected to honor the existing one-file attachment contract and verify against the local public manifest.
- A wrong-flag fixture format-string typo was fixed before rerunning the E2E.
- A rapid six-stage run hit CTFd HTTP 429. Seven-second submission pacing now respects the installed rate limit. Platform protections were unchanged; the final complete run passed.

No tests were removed or weakened. These were invocation/harness defects, not changes to previous-stage flags or contracts.

## Private execution records

.secrets/mt06_functional_result.json, mt06_ui_browser_result.json, mt06_regression_result.json, mt06_prior_recovery_result.json, mt06_security_result.json, mt06_idempotence_result.json and per-stage regression logs. The original pre-integration configuration/solve snapshot is mt06_preflight_snapshot.json. These files remain ignored and may contain sensitive author context.

## Limits / open issues

Member 02 human review is PENDING. MT-02/03/04/05 human reviews remain pending. MT-04 outbound egress remains PARTIAL under the existing documented local-lab limitation; DB/cache network membership is separate and fresh TCP probes were blocked. Full load testing and full-platform backup/restore were not executed. Stage recovery is not a full disaster-recovery claim. Byte-identical ZIP results apply to the recorded Python/zlib toolchain.

No additional stage was created. No CTFd reinstall, upgrade, database reset, participant deletion or solve deletion occurred.
