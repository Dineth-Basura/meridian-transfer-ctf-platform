# MT-05 data dictionary

All evidence is synthetic, sourced from MERIDIAN-MT05-V1.

| Source | Fields | Time representation |
|---|---|---|
| application_audit.csv | event_id, record_id, user_id, action, status, application_time, source | YYYY-MM-DD HH:MM:SS+05:30; fixed offset, second precision |
| web_access.log | synthetic session, [timestamp], quoted method/route/protocol, HTTP status, bytes, event=ID, record=ID | DD/Mon/YYYY:HH:MM:SS +0000; UTC; English month |
| browser_history.sqlite / visits | id INTEGER PRIMARY KEY; url TEXT; title TEXT; visit_time INTEGER; visit_type TEXT; non-null fields | Unix epoch milliseconds since 1970-01-01T00:00:00Z |

IDs are lowercase ASCII. user_id and session are fictional labels. `export` and `view` distinguish action; `completed`, `failed`, `cancelled` distinguish audit outcome. HTTP 200 marks web success; 403 and 500 mark failure. Browser types are `export` and `navigation`. Browser titles are generic and do not identify the answer. URLs use only reserved `http://mt04.lab.invalid`; event ID is the `event` query argument and record ID is in the path.

Selection uses the restricted `rst-` family and application UTC window [2026-10-17T08:00:00Z, 2026-10-17T11:00:00Z). Require audit completed/export, matching successful GET /export/ record and event IDs at exactly the same normalized second, and matching browser export URL with absolute time difference <=60 seconds inclusive. Case context is authoritative; no inference from the host timezone or daylight-saving rules is needed.

EVIDENCE_SHA256SUMS hashes the five evidence/context files, not itself. Public SHA256SUMS hashes the ZIP. Verify before analysis and inspect SQLite read-only or in working copies.
