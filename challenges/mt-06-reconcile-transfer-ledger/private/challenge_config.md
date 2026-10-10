Stage: MT-06
Name: Reconcile the Transfer Ledger
Category: Programming / Scripting
Difficulty: Hard
Value: 400
Type: standard/static
State: visible
Flag provider: static/exact
Dynamic scoring: disabled
Prerequisite: none
Attachments: mt06_ledger.zip, SHA256SUMS
Flag: MT{mt06_32f3e11d129dfe8a8646411e8e8576b9}
Hints: two free hints (0, 0)
Separate parsing, validation, filtering and output construction. Count rejected rows rather than allowing one bad line to terminate the whole analysis.
Deduplicate by event_id before final sorting. Sort by normalized UTC time then event_id, and check the exact no-final-newline serialization rule.
