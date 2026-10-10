#!/usr/bin/env python3
"""Fixed synthetic author seed, reproducible across Python versions."""
from pathlib import Path
import hashlib
from reference_solver import analyze

ROOT = Path(__file__).resolve().parents[1]
SEED = 'MERIDIAN-MT01-V1'
HINTS = [
    'Look for attributes that repeat across independent source snapshots. One source alone is not enough.',
    'Build a short list of aliases satisfying each clue, then identify the candidate present in the intersection of all relevant conditions.'
]

def build(root=ROOT):
    root = Path(root)
    for directory in ('public', 'private'):
        (root / directory).mkdir(parents=True, exist_ok=True)
    # Invented aliases contain a seed-derived suffix and are not copied from accounts.
    aliases = [stem + '_' + hashlib.sha256((SEED + ':' + stem).encode()).hexdigest()[:4]
               for stem in ('siltfolio', 'reedmatrix', 'dunetrace', 'mossvector', 'tidalquill', 'clayorbit')]
    masks = [(True, True, True), (True, True, False), (True, False, True),
             (False, True, True), (True, False, False), (False, True, False)]
    order = sorted(range(6), key=lambda i: hashlib.sha256((SEED + ':order:' + aliases[i]).encode()).digest())
    lines = ['MERIDIAN TRANSFER', 'PUBLIC EVIDENCE ARCHIVE', 'Stage: MT-01 – Digital Footprints', '',
             'All organizations, aliases, events and records below are fictional.',
             'These are offline snapshots, not websites or live accounts.', '',
             'SOURCE A – PROJECT BULLETIN', 'Archive reference: MT-BUL-014; issued 2031-04-21',
             'The review concerns a contributor assigned to the disputed workstream,',
             'with a recorded contribution during the relevant window, who also gave',
             'the required handover briefing. Directory assignment, repository dates',
             'and event attendance were recorded independently by separate clerks.',
             'Disputed workstream: Estuary Model',
             'Relevant window: 2031-04-14 through 2031-04-18',
             'Required briefing: Packet Review 42',
             'Background: the workshop on display styling concerns a different packet.', '',
             'SOURCE B – CONTRIBUTOR DIRECTORY',
             'Archive reference: MT-DIR-006; roster frozen 2031-04-12',
             'Fields: DIRECTORY|alias|assigned workstream|contributor role']
    for i in order:
        lines.append(f'DIRECTORY|{aliases[i]}|{"Estuary Model" if masks[i][0] else "Canopy Index"}|research contributor')
    lines += ['', 'SOURCE C – REPOSITORY ACTIVITY SUMMARY',
              'Archive reference: MT-REP-019; independent contribution ledger',
              'Fields: ACTIVITY|alias|contribution date (inclusive UTC day)|recorded change',
              'A contribution date alone does not establish assignment or briefing attendance.']
    for i in reversed(order):
        lines.append(f'ACTIVITY|{aliases[i]}|{"2031-04-16" if masks[i][1] else "2031-04-09"}|metadata review')
    lines += ['', 'SOURCE D – PUBLIC EVENT NOTICE',
              'Archive reference: MT-EVT-042; published after attendance reconciliation',
              'Fields: BRIEFING|alias|briefing title|capacity',
              'The notice lists confirmed speakers, not invitees.']
    for i in order[2:] + order[:2]:
        lines.append(f'BRIEFING|{aliases[i]}|{"Packet Review 42" if masks[i][2] else "Display Styling 11"}|confirmed speaker')
    lines += ['', 'End of synthetic archive.', '']
    data = '\n'.join(lines).encode('utf-8')
    alias, clues, candidates = analyze(data.decode('utf-8'))
    if alias != aliases[0] or len(clues) != 3 or len(candidates) != 6:
        raise ValueError('Author construction failed uniqueness validation')
    flag = 'MT{mt01_' + alias + '}'
    if flag.encode() in data:
        raise ValueError('Public flag leak')
    (root / 'public/digital_footprints.txt').write_bytes(data)
    (root / 'public/SHA256SUMS').write_text(hashlib.sha256(data).hexdigest() + '  digital_footprints.txt\n')
    (root / 'private/flag.txt').write_text(flag + '\n')
    (root / 'private/flag.txt').chmod(0o600)
    (root / 'public/README.txt').write_text('''Stage: MT-01
Title: Digital Footprints
Domain: OSINT / Reconnaissance
Difficulty: Easy
Objective: Correlate the supplied synthetic public-style records and identify the single alias that matches all relevant evidence.
Flag format: MT{mt01_<alias>}
Internet required: No
Required tools: Browser or text editor; grep/ripgrep optional.
''', encoding='utf-8')
    solution = '''# MT-01 – Digital Footprints
Domain: OSINT / Reconnaissance
Difficulty: Easy
Scenario: A fictional cooperative disputes a research-data handover.
Learning objective: Inspect records, separate background evidence, identify repeated indicators,
correlate independent sources, eliminate inconsistent candidates, and defend one conclusion.
Player task: Identify the alias satisfying all three bulletin conditions.
Useful clues: Estuary Model assignment; activity during 2031-04-14 through
2031-04-18 inclusive; confirmed speaker at Packet Review 42.
Expected solution path: Read A, filter B for assignment, C for dates, D for briefing.
Intersect the three lists. Each source alone leaves multiple plausible candidates.
Expected solve time: 10–15 minutes.
Expected skills: Careful reading, tabulation, evidence correlation, basic text searching.
Why offline OSINT / Reconnaissance: Archived public-style records reproduce the
collection, source comparison and attribution skills of OSINT without external targets.
Validation: Deterministic build, unique set intersection, reference solver, checksum,
release leak checks and actual participant download/submission tests.
Reset/recovery: Rerun author/build_mt01.py; attachment bytes and checksum are stable.
Do not reset the platform database or remove solve records.
'''
    solution += '\nCandidate elimination (assignment, window, briefing):\n'
    for a, mask in zip(aliases, masks):
        solution += f'- {a}: {mask}; ' + ('unique match' if all(mask) else 'decoy: fails at least one condition') + '\n'
    solution += f'\nUnique intended alias: {alias}\nExact flag: {flag}\n\nHints (zero cost):\n'
    solution += '\n'.join('- ' + h for h in HINTS) + '\n'
    (root / 'private/solution.md').write_text(solution, encoding='utf-8')
    (root / 'private/solution.md').chmod(0o600)
    return alias

if __name__ == '__main__':
    build()
    print('PASS: deterministic MT-01 build; exactly one intended candidate')
