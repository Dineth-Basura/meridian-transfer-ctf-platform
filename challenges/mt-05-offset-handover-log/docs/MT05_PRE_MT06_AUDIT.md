# MT-05 automated pre-MT-06 audit

Executed: 2026-09-24T15:05:23.700398+00:00

MT05-PF01–PF22: PASS. Deterministic builder, dataset validator, 40/40 unittest checks and public release validator executed. Both solver CLIs ran with captured output; all intermediate values agreed. Tests cover outer/inner integrity, CSV/log/SQLite parsing, timezone and UTC normalization, unique event, browser window, canonical delimiters, whitespace/newline exclusion, UTF-8 and SHA-256 first16.

MT05-PF23–PF25: PASS. Existing disposable-participant functional test rejected the wrong flag, accepted the correct public-derived flag and prevented duplicate scoring.

MT05-PF26: PASS. Three corruption/detection/rebuild cycles restored identical baseline archive and derived solution (T40); repeated deterministic builds passed T38.

MT05-PF27: PASS. Existing functional test verified MT-01–MT-04 visibility, values, prior attachment bytes and prior solve preservation. MT-04 live HTTP tests passed 9/9. Host-wide discovery additionally attempted container-only unit tests and failed to import app; this invocation error was corrected by using the established container command.

CTFd HTTP: PASS. Existing direct Docker access works; sudo -n requires a password. CTFd remains 3.8.7; database/cache are not host-published. No reinstall or data reset performed.

Human independent review: PENDING (Member 02).
Current status: IMPLEMENTED BUT NOT VERIFIED.
Technical pre-flight: PASS. Pending human review does not block MT-06.

Existing unrelated working files remain untouched. No answers or credentials are included in this audit.

Corrected MT-04 container unit invocation: 24/24 PASS. MT-04 public release validator: PASS. No MT-05 implementation defect was found.
