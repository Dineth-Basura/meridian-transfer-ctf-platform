# MT-06 data dictionary

All data is synthetic. `MERIDIAN-MT06-V1` identifies the deterministic source. The main file has exactly 1,000 physical UTF-8 LF-terminated rows, including intentional malformed JSON and schema violations.

| Field | Required type | Rule |
|---|---|---|
| event_id | string | ASCII `[a-z][a-z0-9-]*`; semantic retry key |
| case_id | string | Same identifier rule; exact match to context |
| record_id | string | Same identifier rule; membership in context allow-list |
| status | string | Only exact `completed` qualifies; other strings are valid exclusions |
| timestamp | string | Valid `YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DDTHH:MM:SS±HH:MM`; explicit offset, no fractions/leap seconds |
| token_b64 | string | Canonical padded standard Base64, strict validation, UTF-8 bytes; decoded nonempty token has no CR/LF |

Offset hours range 00–23 and minutes 00–59. All other token characters are preserved. Extra JSON fields do not affect semantic equality. A valid row must satisfy every field rule before any filtering; invalid rows are counted and skipped. JSON scalars/arrays are invalid event rows.

`incident_context.json` includes non-secret `source`, `case_id`, a nonempty unique string list `allowed_record_ids`, and exact-second UTC-Z `start_utc`/`end_utc` with start strictly before end. Time selection is start inclusive and end exclusive.

Every schema-valid repeated event ID must agree on case, record, status, UTC time and decoded token bytes, including rows outside the selected case/window. Conflict is fatal. Equivalent timestamp offsets are allowed. Invalid rows never participate in duplicate comparison. Identical qualifying retries collapse before sorting.

Final ordering is actual UTC time, then ASCII event ID. Fixed-width normalized UTC-Z exact-second strings also preserve time order; lexical original offset-bearing timestamps do not. Serialization contains decoded token strings only, separated by LF and encoded in UTF-8 without a final LF. SHA-256 first32 lowercase hex produces the flag.

The worked example is intentionally answer-bearing for toy data only. The production expected counts and bytes are author validation material; they are not needed to solve the task. Both manifests use ordinary sha256sum format. Archive member timestamps, Unix permissions and ordering are fixed.
