# MT-04 build status

Build timestamp: 2026-09-21T17:00:54.067670+00:00
Python version (host): 3.12.3
Flask version: 3.1.1
SQLite version (container): 3.40.1
Container image: meridian-mt04:local (sha256:6c0de142cc39e9586658b6884775762b57ec576e86700a67ffa61ce146a99565)
CTFd version: 3.8.7
CTFd challenge ID: 4
Service URL/bind: http://127.0.0.1:8084 / loopback
Target container port: 8000
Network: mt04_release_register_mt04_challenge_net (dedicated bridge)
Seed SQLite SHA-256: c023258562c5013090a8762d2689318bda7dfb6de62640e5ac665ff7b5b762af

Deterministic seed: PASS
Unit tests: 24/24 PASS
Live HTTP tests: 9/9 PASS
Guest denied: PASS
Own record: PASS
Own export: PASS
Cross-owner normal: PASS
Vulnerable export: PASS
Fixed export: PASS
Flag uniqueness: PASS
CTFd wrong flag: PASS
CTFd correct flag: PASS
Duplicate scoring: PASS
CTFd DB isolation: PASS
CTFd cache isolation: PASS
Docker socket absent: PASS
Egress: PARTIAL
Resource limits: PASS
Recovery cycles: 3/3 PASS
MT-01 regression: PASS
MT-02 regression: PASS
MT-03 regression: PASS
Browser/UI: PASS
Independent human review: PENDING

Overall status: IMPLEMENTED BUT NOT VERIFIED

Technical and platform tests pass. Strict outbound egress remains PARTIAL pending an operator-reviewed Docker-aware host firewall rule. Independent Member 02 participant-only review remains pending.
