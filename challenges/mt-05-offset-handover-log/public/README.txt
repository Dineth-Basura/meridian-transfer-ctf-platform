Stage: MT-05
Title: The Offset in the Handover Log
Domain: Digital Forensics
Difficulty: Moderate-Hard
Estimated solve time: 30–45 minutes
Objective: Preserve and inspect the supplied forensic evidence, normalize
timestamps, correlate the three independent sources, identify the single
completed restricted export, and derive the stage flag.
Files: mt05_evidence.zip, SHA256SUMS
Suggested tools: sha256sum, file, unzip, grep, Python 3, sqlite3, CSV tools;
optional jq. Internet required: No.
Flag format: MT{mt05_<16 lowercase hex>}
Verify before extraction: sha256sum -c SHA256SUMS
Extract into a clean working directory: unzip mt05_evidence.zip
Then: cd meridian_mt05 && sha256sum -c EVIDENCE_SHA256SUMS
Read case_context.txt and schema_guide.txt. Preserve original evidence and use
working copies, or open SQLite read-only with mode=ro.
Canonical value: event_id|YYYY-MM-DDTHH:MM:SSZ|record_id
Use the normalized application audit timestamp in UTC with exact seconds,
lowercase ASCII event_id and record_id, uppercase literal Z, literal | separators,
no spaces, no surrounding whitespace, no CR or LF, and no trailing newline.
Encode the canonical value as UTF-8 bytes. Compute SHA-256 and take exactly
the first 16 lowercase hexadecimal characters. Submit MT{mt05_<digest16>}.
