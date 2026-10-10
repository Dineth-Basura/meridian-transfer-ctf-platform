# MT-01 – Digital Footprints

Stage ID & Title: MT-01 – Digital Footprints

Domain: OSINT / Reconnaissance

Difficulty: Easy

Difficulty justification: Four readable snapshots, six candidates and three explicit
criteria make this an introductory correlation exercise. Each individual criterion
and each pair leaves plausible decoys. No exploitation or specialist tooling is needed.

Scenario: Meridian Transfer is a fictional research cooperative preparing a
research-data handover. Investigators must attribute the disputed handover from
independently archived contributor records. All content is synthetic.

Learning Objective: Inspect public-style evidence; distinguish useful clues from
background material; identify repeated indicators; correlate independent sources;
eliminate inconsistent candidates; reach one defensible conclusion.

Challenge Environment: Ubuntu 24.04 VM, Docker Compose, official CTFd 3.8.7;
standard challenge with a single UTF-8 attachment. Evidence is entirely offline.

Player Task: Identify the single contributor alias matching the project bulletin's
workstream, inclusive activity window and confirmed briefing conditions.

Flag Location / Logic: Submit `MT{mt01_<alias>}`. The full flag is not in the public
archive. Author-only flag storage is private/flag.txt; CTFd accepts one case-sensitive
static flag. Intersection of the three independent conditions determines the alias.

Required Tools: Browser or text editor; grep/ripgrep optional.

Dependencies: Local Docker Engine and Compose v2, Git, curl, Python 3. Author tools
use only the Python standard library. No Internet connection is required to solve.

Expected Solution Path: Read the bulletin, list directory aliases in the specified
workstream, filter recorded contribution dates, compare confirmed briefing speakers,
and intersect all three lists. Format the sole remaining alias as the requested flag.
Expected solve time: 10–15 minutes.

Validation: Deterministic build, UTF-8 verification, unique intersection, decoy and
ambiguity checks, solver, SHA-256 manifest, release leak checks, actual participant
registration/download/wrong and correct submissions/solve and duplicate score checks.

Hints (both cost 0):

1. Look for attributes that repeat across independent source snapshots. One source alone is not enough.
2. Build a short list of aliases satisfying each clue, then identify the candidate present in the intersection of all relevant conditions.

Reset / Recovery: Rebuild with author/build_mt01.py. Only a temporary copy is modified
in the recovery test. Confirm restored bytes match SHA256SUMS. Update CTFd with
platform/setup_mt01.py if necessary. Preserve platform data and solve records.

Expected Skills: Reading, public evidence assessment, alias attribution, set
intersection, documenting why each decoy fails. Archived public-style evidence
practices OSINT/reconnaissance skills without external targets or personal data.

Implementation status: IMPLEMENTED AND VERIFIED

Verification completed: all required local and real participant checks passed.
