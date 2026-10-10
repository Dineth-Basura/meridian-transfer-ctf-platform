#!/usr/bin/env python3
"""Correlate the archive alone; never consult author/private data."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

def analyze(text):
    def field(key):
        match = re.search(r'^' + key + r': (.+)$', text, re.M)
        if not match:
            raise ValueError('Missing bulletin field: ' + key)
        return match.group(1)
    stream = field('Disputed workstream')
    start, end = field('Relevant window').split(' through ')
    event = field('Required briefing')
    directory = dict(re.findall(r'^DIRECTORY\|([a-z0-9_]{6,18})\|([^|\n]+)\|[^\n]+$', text, re.M))
    activity = re.findall(r'^ACTIVITY\|([a-z0-9_]{6,18})\|([^|\n]+)\|[^\n]+$', text, re.M)
    briefings = re.findall(r'^BRIEFING\|([a-z0-9_]{6,18})\|([^|\n]+)\|[^\n]+$', text, re.M)
    clues = [set(a for a, s in directory.items() if s == stream),
             set(a for a, date in activity if start <= date <= end),
             set(a for a, e in briefings if e == event)]
    matches = set.intersection(*clues)
    if len(matches) != 1:
        raise ValueError(f'Ambiguous evidence: {len(matches)} candidates match')
    return next(iter(matches)), clues, set(directory)

def solve(path=ROOT / 'public/digital_footprints.txt'):
    return analyze(Path(path).read_text(encoding='utf-8'))[0]

if __name__ == '__main__':
    alias = solve()
    print('Identified alias: ' + alias)
    print('Flag: MT{mt01_' + alias + '}')
