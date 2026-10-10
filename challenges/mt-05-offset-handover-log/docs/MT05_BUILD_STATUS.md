# MT-05 build status

Build timestamp: 2026-09-23T14:24:33.696594+00:00
Python version: 3.12.3
SQLite version: 3.45.1
CTFd version: 3.8.7
CTFd challenge ID: 5
Archive: mt05_evidence.zip
Archive size: 5805 bytes
Archive SHA-256: b3dff092a114d2a9d6a770f7bf33d5fd5dcdb1dbd50a9914b876fef3cd908436
Source identifier: MERIDIAN-MT05-V1
Case window: [2026-10-17T08:00:00Z, 2026-10-17T11:00:00Z)
Timestamp representations: application YYYY-MM-DD HH:MM:SS+05:30; access DD/Mon/YYYY:HH:MM:SS +0000; browser Unix epoch milliseconds UTC.
Audit rows: 49
Access rows: 49
Browser rows: 48

Dataset generation: PASS
Unique event: PASS
Outer checksum: PASS
Inner checksums: PASS
CSV: PASS
Access log: PASS
SQLite: PASS
Timezone normalization: PASS
UTC boundary: PASS
60-second correlation: PASS
Canonicalization: PASS
UTF-8 serialization: PASS
SHA-256 derivation: PASS
Reference solver 1: PASS
Reference solver 2: PASS
Independent solver agreement: PASS
Public leak check: PASS
Archive size: PASS
Participant downloads: PASS
Wrong CTFd flag: PASS
Correct CTFd flag: PASS
Duplicate scoring: PASS
Recovery: PASS
MT-01 regression: PASS
MT-02 regression: PASS
MT-03 regression: PASS
MT-04 regression: PASS
Browser/UI: PASS

Unit tests: 40/40 PASS
Recovery working-copy cycles: 3/3 PASS
Repeated ZIP and SQLite bytes: identical on tested toolchain
Idempotent integration: PASS (same challenge ID and attachment metadata)
Existing correct submission IDs: preserved across rebuild/integration and earlier MT-04 reset
Reviewer package: READY (four participant-only files; unfilled template)
Independent human review: PENDING

Final status: **IMPLEMENTED BUT NOT VERIFIED**

## Actual execution evidence

Executed builder, dataset validator, 40 unittest checks, both solver CLIs (answer output captured privately), public release validator, outer sha256sum and inner sha256sum in a temporary extraction. Solvers independently agreed on event ID, record ID, UTC timestamp, canonical value, UTF-8 bytes, full SHA-256, first16 and flag. The signed-in functional test downloaded only participant files into a clean temporary dataset and ran both external solvers against it. No author/private files were copied into that dataset.

CTFd integration ran twice; second run reused the same challenge and files. A disposable participant started with zero score, was rejected for the specified wrong flag, received 300 points for the derived correct flag, and received no additional points on duplicate submission. The test account was hidden and its solve preserved. Both hints cost zero and requirements are absent.

Prior MT-01/02/03 challenge values, visibility and actual attachment bytes passed regression. MT-04 configuration remained intact; live HTTP 9/9 and private fixed comparison passed after integration. MT-04 remains healthy with loopback publishing, socket absent and no shared DB/cache network. Actual TCP attempts from MT-04 to CTFd DB/cache container addresses failed as required. Prior correct submission IDs remain present.

Existing Playwright browser regression passed desktop/mobile, role navigation, registration, sign-in/out, admin denial, downloads, submission and JavaScript error checks, plus MT-05 attachments and five-stage visibility. Results were written to `.secrets/mt05_ui_browser_result.json` to preserve the pre-existing UI_BROWSER_STATUS.json modification. Browser executable discovery remains managed by Playwright; no version hardcoding added.

Private execution records: `.secrets/mt05_functional_result.json`, `.secrets/mt05_recovery_result.json`, `.secrets/mt05_preflight_snapshot.json`, `.secrets/mt05_ui_browser_result.json`. These are excluded from Git.

## Open issues / limitations

- Member 02 independent MT-05 human review is PENDING. No human review has been fabricated. MT-02/03/04 human reviews remain pending.
- MT-04 egress remains PARTIAL under the documented local-lab exception; final Docker-aware host firewall controls have not been applied. No new public exposure or network service was introduced by MT-05.
- Byte-identical builds were verified with the recorded Python/SQLite toolchain. Cross-version SQLite/zlib binary identity is not promised; preserve the live baseline and validate any toolchain upgrade before republishing.
- Sandbox startup failed with a loopback namespace error; approved outside-sandbox commands were used. `sudo -n` required a password, so existing direct Docker access was used successfully.

MT-06 remains PLANNED / NOT IMPLEMENTED.
