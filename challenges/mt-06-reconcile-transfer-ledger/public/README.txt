Stage: MT-06
Title: Reconcile the Transfer Ledger
Domain: Programming / Scripting
Difficulty: Hard
Estimated solve time: 40–60 minutes
Objective: Write a reproducible parser that validates the supplied JSONL transfer
ledger, filters incident events, handles retries, normalizes time, decodes tokens
and derives a deterministic final flag.
Files: mt06_ledger.zip, SHA256SUMS
Suggested tools: Python 3, text editor, sha256sum, unzip; optional jq.
Internet required: No. All evidence is synthetic and offline.
Flag format: MT{mt06_<32 lowercase hex>}
Verify: sha256sum -c SHA256SUMS
Extract: unzip mt06_ledger.zip
Then inside meridian_mt06: sha256sum -c EVIDENCE_SHA256SUMS
Read schema.json and incident_context.json. The worked_example directory shows
a toy calculation only. Preserve originals and work on a disposable copy.

Parse events.jsonl line-by-line as UTF-8. There are exactly 1000 physical
rows, including intentionally malformed JSON and schema-invalid records.
Count and skip invalid rows; validate ALL rows before filtering. Required fields
are strings: event_id, case_id, record_id, status, timestamp, token_b64.
Identifiers match [a-z][a-z0-9-]* (ASCII). Extra fields are ignored.
Timestamps use YYYY-MM-DDTHH:MM:SS followed by Z or +/-HH:MM; hours 00–23,
offset minutes 00–59, exact seconds, valid calendar date, no naive times,
fractional seconds or leap seconds. Normalize to UTC.
token_b64 uses canonical standard RFC 4648 Base64 with required padding,
strict alphabet validation, and no whitespace. Re-encoding decoded bytes must
match the original. Bytes must decode as UTF-8. Tokens are nonempty and contain
no CR or LF. Preserve all other token characters, including any spaces.
Validate duplicate event_id values across ALL schema-valid rows. Their semantic
values (case_id, record_id, status, normalized timestamp, token bytes) must agree.
An equivalent timestamp offset is not a conflict. Ignore invalid rows for this
check. Any conflicting duplicate is a fatal DATASET ERROR; never choose one.
Select rows only when case_id exactly matches incident_context.json, record_id
is in allowed_record_ids, status is exactly completed, and normalized time is
>= start_utc AND < end_utc (start inclusive, end exclusive).
Collapse identical qualifying retries by event_id BEFORE final sorting.
Sort by normalized UTC timestamp ascending, THEN event_id ascending using ASCII
ordering. Decode selected tokens and join the token strings with one LF (0x0A)
between adjacent tokens. Do not strip tokens, add spaces, include event IDs,
serialize JSON, use CRLF, or append a final LF. Encode the result as UTF-8.
Compute SHA-256; use the FIRST 32 lowercase hexadecimal digest characters.
Submit MT{mt06_<digest32>}. An empty toy selection hashes empty bytes; the
production dataset is guaranteed to have a nonempty selection.
No earlier stage secret is required. All context is supplied locally.
