import hashlib
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'author'))
from build_mt01 import build
from reference_solver import analyze, solve
from validate_public_release import validate, EXPECTED

class MT01Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.alias = build(self.root)
        self.public = self.root / 'public'
        self.data = (self.public / 'digital_footprints.txt').read_bytes()
        self.text = self.data.decode('utf-8')
        self.flag = (self.root / 'private/flag.txt').read_text().strip()
        _, self.clues, self.candidates = analyze(self.text)

    def test_deterministic_build(self):
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        build(self.root)
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        self.assertEqual(self.data, (ROOT / 'public/digital_footprints.txt').read_bytes())

    def test_required_files(self):
        self.assertEqual({p.name for p in self.public.iterdir()}, EXPECTED)
        self.assertTrue((self.root / 'private/flag.txt').is_file())
        self.assertTrue((self.root / 'private/solution.md').is_file())

    def test_utf8_and_header(self):
        self.assertTrue(self.text.startswith('MERIDIAN TRANSFER\nPUBLIC EVIDENCE ARCHIVE\nStage: MT-01 – Digital Footprints'))

    def test_unique_alias(self):
        self.assertEqual(set.intersection(*self.clues), {self.alias})

    def test_candidate_count_and_format(self):
        self.assertGreaterEqual(len(self.candidates), 5)
        self.assertLessEqual(len(self.candidates), 7)
        for a in self.candidates:
            self.assertRegex(a, r'^[a-z0-9_]{6,18}$')

    def test_independent_clues(self):
        self.assertEqual(len(self.clues), 3)
        for i, clue in enumerate(self.clues):
            self.assertGreater(len(clue), 1)
            remaining = [s for j, s in enumerate(self.clues) if j != i]
            self.assertGreater(len(set.intersection(*remaining)), 1)

    def test_reference_solver(self):
        self.assertEqual(solve(self.public / 'digital_footprints.txt'), self.alias)

    def test_flag_format(self):
        self.assertRegex(self.flag, r'^MT\{mt01_[a-z0-9_]+\}$')

    def test_no_full_flag(self):
        for p in self.public.iterdir():
            self.assertNotIn(self.flag, p.read_text())

    def test_readme_no_alias(self):
        self.assertNotIn(self.alias, (self.public / 'README.txt').read_text())

    def test_checksum(self):
        self.assertEqual((self.public / 'SHA256SUMS').read_text(), hashlib.sha256(self.data).hexdigest() + '  digital_footprints.txt\n')

    def test_plausible_decoys(self):
        wrong = self.candidates - {self.alias}
        self.assertGreaterEqual(sum(sum(a in c for c in self.clues) >= 2 for a in wrong), 3)

    def test_wrong_candidate_flags(self):
        for a in self.candidates - {self.alias}:
            self.assertNotEqual('MT{mt01_' + a + '}', self.flag)

    def test_no_public_credentials(self):
        self.assertTrue(validate(self.root, verbose=False))

    def test_private_files_excluded(self):
        self.assertEqual({p.name for p in self.public.rglob('*')}, EXPECTED)

    def test_solver_rejects_no_match(self):
        with self.assertRaises(ValueError):
            analyze(self.text.replace('Disputed workstream: Estuary Model', 'Disputed workstream: Absent Stream'))

    def test_solver_rejects_ambiguity(self):
        wrong = next(iter((self.clues[0] & self.clues[1]) - {self.alias}))
        with self.assertRaises(ValueError):
            analyze(self.text.replace(f'BRIEFING|{wrong}|Display Styling 11', f'BRIEFING|{wrong}|Packet Review 42'))

    def test_validator_rejects_leak_and_extra_file(self):
        (self.public / 'README.txt').write_text(self.flag)
        self.assertFalse(validate(self.root, verbose=False))
        (self.public / 'flag.txt').write_text(self.flag)
        self.assertFalse(validate(self.root, verbose=False))

if __name__ == '__main__':
    unittest.main()
