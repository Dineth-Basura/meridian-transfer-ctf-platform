# Meridian Transfer

IE3132 – Penetration Testing

Platform: CTFd 3.8.7

Environment: Ubuntu 24.04 VM / Docker Compose

Implemented stages:

- MT-01 – Digital Footprints — OSINT / Reconnaissance — Easy — 100 points — IMPLEMENTED AND VERIFIED
- MT-02 – The Amended Contact Sheet — Steganography — Easy — 150 points — IMPLEMENTED BUT NOT VERIFIED (independent Member 03 participant-only solve pending)
- MT-03 – Dispatch Window — Cryptography — Moderate — 200 points — IMPLEMENTED BUT NOT VERIFIED (independent Member 03 participant-only solve pending)
- MT-04 – Release Register Exception — Web Security — Moderate — 250 points — IMPLEMENTED BUT NOT VERIFIED (independent Member 02 participant-only solve pending)
- MT-05 – The Offset in the Handover Log — Digital Forensics — Moderate-Hard — 300 points — IMPLEMENTED BUT NOT VERIFIED (independent Member 02 participant-only solve pending)

- MT-06 – Reconcile the Transfer Ledger — Programming / Scripting — Hard — 400 points — IMPLEMENTED BUT NOT VERIFIED (independent Member 02 participant-only solve pending)

Run the complete local setup and verification:

```bash
python3 platform/setup_local.py
```

Docker and Compose v2 must be available. If Docker access needs sudo, run the
same command with `--sudo-docker`; no group membership change is needed.
Repeat runs reuse the existing CTFd image. Pass `--rebuild` after changing the
CTFd source or when you need to rebuild the image. A first run must build it.
The official release is cloned if absent and its exact commit is checked. The
deployment override disables the upstream Nginx service and restricts HTTP to
loopback and the first private VM IPv4 address. Database and cache have no host
ports. No Docker socket or dynamic challenge plugins are used.

Local URL: http://127.0.0.1:8000

The build summary records the VM URL. Host reachability is not implied. A
VirtualBox NAT guest usually needs port forwarding for host access; networking
is not changed automatically. Restrict any future forwarding to the local lab.

Credentials: .secrets/ctfd_admin_credentials.txt (mode 600; do not commit).
CTFd SECRET_KEY: .secrets/ctfd.env (mode 600), using the environment interpolation
implemented in CTFd 3.8.7's CTFd/config.py. It is excluded from the Docker build
context and uploaded challenge content. The official container runs as UID 1001,
so this mechanism avoids making a host-owned mode-600 secret file readable to
another host user. A matching mode-600 .ctfd_secret_key is also created in the
upstream clone as the supported file fallback, excluded by its .dockerignore.
Setup uses the real /setup form and its CSRF nonce; integration
uses the official API with the authenticated administrator session and CSRF header.
No API token is generated or stored.

MT-01 and MT-02 public attachments are uploaded. Public content is deterministic with
author seed MERIDIAN-MT01-V1. Author-only content is under private/; the upstream
CTFd clone and its database/uploads are excluded from the project repository.
Rebuilds preserve administrator credentials, platform data and solve records.
Initialized installations without managed credentials or with a different CTF
name are refused. An existing exact-name/category MT-01 is updated in place.

Each functional verification registers a synthetic local participant, checks
the real attachment and submissions, preserves the solve, then hides that test
account from the scoreboard. Repeated tests never erase prior solve records.

Results: BUILD_STATUS_MT01.txt. Diagnostic logs and functional result JSON stay
in .secrets/. The stage specification is in
challenges/mt-01-digital-footprints/docs/MT01_SPECIFICATION.md.

Suggested Git commit: `feat(mt01): deploy CTFd and implement Digital Footprints`

Participant access: Use /register in a logged-out browser or private window.
If the navigation shows Administrator, use the visible Sign out button first.
New participant accounts redirect to login without retaining a signed-in session. Successful password login opens the challenges dashboard (`/challenges`).
CTFd deliberately redirects authenticated accounts away from registration.
The Admin Panel link is rendered only for administrators; all admin routes and
protected APIs also enforce role checks on the server.

The project UI is stored in platform/ui/. The navbar is mounted read-only over
its upstream template, keeping the pinned CTFd source intact. Homepage and CSS
are applied through CTFd's page/configuration APIs by platform/configure_ui.py.
The prior homepage/configuration is backed up in .secrets/.
Local registration is enabled without registration codes, user caps or email
verification. Guest, participant and administrator navigation are separate.

Access regression checks: python3 platform/test_access_registration.py
Results: ACCESS_REGISTRATION_STATUS.json.
Browser checks: node platform/test_ui_browser.cjs (requires the local Playwright
installation under .secrets/ui-browser/). Results: UI_BROWSER_STATUS.json.

MT-02 uses a synthetic RGB PNG, a PNG textual metadata clue, red-channel LSBs in row-major order, a 32-bit big-endian payload byte length, UTF-8 payload bytes with MSB-first bits, and a public SHA-256 integrity manifest. Its author tools and specification are in challenges/mt-02-amended-contact-sheet/.

Challenge viewing, challenge APIs, attachments and submissions require a signed-in participant. Registration remains public; unauthenticated visitors can see the homepage and sign-in/register routes.

Challenge attachment URLs can carry signed download tokens in CTFd. The local `platform/plugins/challenge_signin` guard requires a live session for those challenge files as well. It is mounted read-only over the unused upstream dynamic-challenge plugin directory; MT-01 and MT-02 remain standard/static challenges.

MT-02 technical checks and CTFd participant tests pass. Independent review is pending; the participant-only package and blank result template are in `review/mt-02-independent/`. Do not treat the blank template as reviewer approval.

MT-03 uses deterministic offline evidence. Its outer Base64 representation contains a case-preserving ASCII Caesar shift; players derive the shift from the release notice day and reverse the layers in order. Public attachments are a ciphertext, release notice and SHA-256 manifest. MT-02 remains pending its own independent human review.

MT-04 is an intentionally vulnerable synthetic local lab application separate from CTFd. Its loopback URL is `http://127.0.0.1:8084`; only the authenticated export route omits object ownership verification. Its dedicated Docker bridge has no CTFd database/cache membership. Outbound egress is currently PARTIAL pending an operator-reviewed Docker-aware host firewall rule; see the MT-04 security boundary document.

MT-05 provides deterministic synthetic web logs, application audit CSV and browser-history SQLite. Players verify SHA-256 integrity, normalize timestamps and correlate all three sources before deriving a flag from canonical UTF-8 bytes. The 40-test suite, two independently structured public-only solvers, release validator and local CTFd participant tests verify its technical implementation. No prior stage flag is required. Author commands and recovery guidance are in `challenges/mt-05-offset-handover-log/docs/MT05_SPECIFICATION.md`; the answer-free review package is `review/mt-05-independent/`. Member 02 human review remains PENDING. MT-06 is now technically deployed; its separate human review also remains pending.

MT-04 passed a fresh automated pre-flight before MT-05 development; see `challenges/mt-04-release-register-exception/docs/MT04_PRE_MT05_AUDIT.md`. Its human review remains PENDING and egress remains PARTIAL under the documented local-lab limitation.

MT-06 is the final Programming / Scripting capstone: exactly 1,000 physical JSONL rows, strict validation, mixed timestamp offsets, semantic retry checks and deterministic UTF-8 token serialization. Its 70 automated tests, independent public-only solvers, release checks, three recovery cycles and CTFd/browser regressions pass. Both hints are free, scoring is static at 400 points, and no previous flag is required. Member 02 must still complete the independent participant-only review in `review/mt-06-independent/`.

All six stages are available. Configured fixed points sum programmatically to **1400**. A disposable participant completed the **AUTOMATED TECHNICAL E2E**, with wrong/malformed flags rejected, correct flags accepted and exactly one scoring award per stage. This does not certify human end-to-end acceptance. Existing challenge configuration and solve records were preserved.

See [automated release status](docs/AUTOMATED_RELEASE_STATUS.md), [testing scope](docs/TESTING_STATUS.md), and [MT-06 build status](challenges/mt-06-reconcile-transfer-ledger/docs/MT06_BUILD_STATUS.md). Full load testing and full-platform backup/restore remain pending. The existing MT-04 outbound-egress limitation remains PARTIAL.
