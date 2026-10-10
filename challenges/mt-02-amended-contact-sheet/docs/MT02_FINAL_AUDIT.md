# MT-02 final audit

Audit date: 2026-09-21 UTC
Git commit at audit start: `b598219`
CTFd version: 3.8.7, pinned upstream clone
CTFd service state: Running; HTTP 200 on `http://127.0.0.1:8000/`. Database and cache remain running with no published host ports.

| Check | Actual result |
|---|---|
| MT-01 regression | PASS. Challenge ID 1 remains visible, in OSINT / Reconnaissance, worth 100. Attachment matched the public baseline. The disposable participant test rejected a wrong answer, accepted the correct answer, recorded a solve, and prevented duplicate scoring. Database solve records remained present. MT-01 unit tests: 18/18. |
| MT-02 unit tests | PASS: 20/20. |
| Deterministic build | PASS: two direct builds and test-suite rebuilds produced the approved PNG SHA-256 `8069803fbac09a8379847f0e7d0246002b42b4337844a35e2463486fa8050504`. No asset change. |
| Metadata | PASS: ExifTool 12.76 shows an RGB PNG and the lowest-order red-data clue. No flag or payload appears in metadata. |
| Reference extraction | PASS: the extractor read public PNG pixels, parsed a 32-bit big-endian length of 203 bytes, decoded UTF-8, and found exactly one valid MT-02 flag. The flag is omitted here. |
| Public release | PASS: validator, SHA256SUMS and participant-only review package checksum. Public files contain no private answer files or real credentials. |
| CTFd functional | PASS: challenge ID 2 is visible, standard/static, worth 150, with exactly two free hints, the expected public attachments and no prerequisite. A disposable participant downloaded both files, had a wrong flag rejected, had the correct flag accepted, received one solve and 150 points, and could not earn another 150 for a repeated submission. |
| Browser/UI | PASS: fresh Playwright test covers desktop and mobile layouts, guest registration, signed-in navigation, both implemented stages, planned-stage absence, attachment download, submission and administrator navigation. The hardcoded Chromium revision was removed. |
| Access control | PASS: guests can register but cannot view challenges, call challenge APIs, download challenge attachments or submit flags. A signed-in participant can access both stages and downloads; logout restores denial. Admin controls remain restricted. |
| Recovery | PASS: a temporary modified PNG failed SHA-256 validation; rebuilding restored the approved hash. CTFd remained available. Database solve counts after recovery: MT-01 9, MT-02 2, including hidden test accounts. |
| Security | PASS: synthetic image only; no real photographs or personal data; no flag in metadata or public README; CTFd serves only public attachments; admin credentials, CTFd secret, API tokens, private flags, venv and upstream clone are untracked/ignored; no Docker socket or database/cache host ports; MT-02 requires no Internet target. |
| Independent reviewer | PENDING. The participant-only package and blank result template are ready for Member 03. No independent human result was created or inferred. |

Open issues: Independent Member 03 participant-only solve and CTFd submission remain pending.

Overall MT-02 status: **IMPLEMENTED BUT NOT VERIFIED**.

Technical implementation and platform tests pass; independent Member 03 participant-only solve remains pending.
