# MT-02 specification

| Field | Assignment |
|---|---|
| Stage ID & Title | MT-02 – The Amended Contact Sheet |
| Domain | Steganography |
| Difficulty | Easy |
| Difficulty justification | Metadata names the channel and bit order; two free hints narrow the extraction path. Estimated 15–20 minutes. |
| Scenario | A routine contact sheet in the Meridian Transfer review has a creation note about a stored release annotation. |
| Learning Objective | Distinguish visible pixels, metadata, and pixel-hidden data; extract from lossless evidence without altering it. |
| Challenge Environment | Existing CTFd 3.8.7 standard challenge with two downloadable public files and no Internet target. |
| Player Task | Verify the PNG, inspect its metadata, recover the annotation, submit the embedded flag. |
| Flag Location / Logic | RGB PNG red-channel LSB, row-major order; 32-bit unsigned big-endian byte length, then UTF-8 bytes MSB-first. |
| Required Tools | `file`, `sha256sum`, ExifTool, Python 3, Pillow. |
| Dependencies | Existing CTFd; Pillow 10.2.0 for reproducible author build. No stage prerequisite. |
| Expected Solution Path | Check checksum, inspect Comment metadata, read red LSBs, parse length, decode UTF-8, find the single MT-02 flag. |
| Validation | 20 unit tests, ExifTool, reference extraction, public validator, real participant download/submission/score test, recovery. |
| Hints | 1. The creation note points to a channel, not an archive password. 2. Read the lowest bit of red pixels in row order. The first four bytes describe the payload length. Both free. |
| Reset / Recovery | Use a working copy; the manifest detects changed bytes. Rebuild the public PNG and verify baseline SHA-256 without touching CTFd scoring. |
| Expected Skills | Metadata inspection, bitwise operations, byte parsing, UTF-8 decoding, evidence integrity. |
| Responsible Member | Member 02 |
| Reviewer | Member 03 |
| Integration Reviewer | Member 04 |
| Implementation Status | IMPLEMENTED BUT NOT VERIFIED — technical implementation and platform tests pass; independent Member 03 participant-only solve remains pending. |
