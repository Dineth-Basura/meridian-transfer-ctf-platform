# MT-03 specification

| Field | Assignment |
|---|---|
| Stage ID & Title | MT-03 – Dispatch Window |
| Domain | Cryptography |
| Difficulty | Moderate |
| Difficulty justification | Two reversible layers must be identified and undone in order. The key comes from a separate date clue; estimated 20–30 minutes. |
| Scenario | A fictional Meridian Transfer dispatch note was transformed by a legacy training utility and archived with its release notice. |
| Learning Objective | Distinguish encoding from encryption, recognize Base64, apply an ASCII Caesar shift with modular arithmetic, derive a weak contextual key, and explain transformation order. |
| Challenge Environment | Existing CTFd 3.8.7 standard/static challenge with three local public attachments and no Internet target. |
| Player Task | Verify the files, infer the outer representation, derive the release-day shift, reverse both transformations, and submit the recovered literal flag. |
| Flag Location / Logic | Exactly one MT-03 flag occurs in the original dispatch plaintext. Public ciphertext is Base64 of UTF-8 text after ASCII letters were shifted forward by release day modulo 26. |
| Required Tools | Python 3, text editor, optional standard Base64 utility, SHA-256 utility. |
| Dependencies | Python standard library only; existing CTFd. No previous stage completion is required. |
| Expected Solution Path | Check SHA256SUMS; inspect the Base64 line; decode it; read the approved release date in the notice; calculate day modulo 26; shift ASCII letters backward; read the dispatch flag. |
| Validation | 28 unit tests, deterministic rebuild, strict Base64 and negative tests, reference solver from public files, public validator, real participant CTFd test, browser/UI test, recovery, MT-01/MT-02 regression. |
| Hints | Two free hints: outer representation reversible without a key; release day modulo alphabet length, then reverse the letter shift. |
| Reset / Recovery | Modify only temporary copies; SHA256SUMS must reject changed bytes. Rebuild public evidence to restore baseline hashes without touching CTFd scoring. |
| Expected Skills | Evidence integrity, Base64 recognition and decoding, ASCII-only character transformation, modular arithmetic, layered reasoning. |
| Responsible Member | Member 02 |
| Reviewer | Member 03 |
| Integration Reviewer | Member 04 |
| Implementation Status | IMPLEMENTED BUT NOT VERIFIED — automated and platform checks pass; independent Member 03 solve pending. |
