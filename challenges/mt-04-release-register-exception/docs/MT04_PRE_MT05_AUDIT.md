# MT-04 pre-MT-05 audit

Executed 2026-09-23 on the existing CTFd 3.8.7 deployment. Status: **IMPLEMENTED BUT NOT VERIFIED**. Independent Member 02 human review: **PENDING**.

| Checks | Actual result / evidence |
|---|---|
| PF01 | PASS: CTFd localhost HTTP and authenticated functional test |
| PF02 | PASS: Docker health healthy; `/healthz` returns ok |
| PF03–PF09 | PASS: existing live HTTP suite 9/9; guest denial, participant login, own normal/export, cross-owner normal denial, vulnerable export with one flag |
| PF10 | PASS: existing container unit suite 24/24 and reset helper fixed authorization comparison |
| PF11–PF13 | PASS: existing `platform/test_mt04_functional.py`; wrong rejected, correct accepted, duplicate no extra score |
| PF14 | PASS: no container mounts; Docker socket absent |
| PF15 | PASS: MT-04 network membership disjoint from CTFd DB/cache networks |
| PF16 | PASS: CTFd DB/cache Docker ports have no host bindings |
| PF17–PF20 | PASS: UID/GID 10001, no-new-privileges, ALL capabilities dropped, memory/CPU/PID limits present |
| PF21 | PASS: reset helper reran live/fixed tests; CTFd configuration, attachment metadata and all correct submission IDs unchanged across audited reset |
| PF22 | PASS: MT-01/02/03 visible with 100/150/200 points; configuration and attachment metadata unchanged across reset |

Commands: `python3 -m unittest discover challenges/mt-04-release-register-exception/tests -p test_mt04_http.py -v`; `docker exec -i mt04_release_register-portal-1 python - < challenges/mt-04-release-register-exception/tests/test_mt04_unit.py`; `python3 platform/test_mt04_functional.py`; `python3 challenges/mt-04-release-register-exception/author/validate_release.py`; `python3 platform/reset_mt04.py`. Runtime inspection and authenticated before/after snapshots supplement these existing tests. Snapshot is private in `.secrets/mt05_preflight_snapshot.json`.

No implementation defect found. Audit harness initially used an unavailable `/solves` endpoint and assumed optional `requirements` was always serialized; corrected to the installed paginated submissions API and optional-field handling, then reran successfully. No tests weakened.

Egress remains **PARTIAL**, as documented in MT04_SECURITY_BOUNDARY.md. No firewall changes made. MT-04 is loopback-only, has no Docker socket or CTFd database/cache network membership, and no new host/public exposure was introduced. Development is permitted under the local-lab exception. `sudo -n` required a password; existing direct Docker access worked. No human review result was generated.

Post-integration regression: live HTTP 9/9 and private fixed comparison PASS. Actual TCP connections from MT-04 to every inspected CTFd DB/cache container address failed. Recovered vulnerable flag matched the private configured flag exactly once, without printing it.
