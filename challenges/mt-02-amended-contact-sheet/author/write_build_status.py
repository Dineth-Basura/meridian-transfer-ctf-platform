#!/usr/bin/env python3
"""Format measured build facts and explicitly supplied audit results.

No test result is inferred from a file's existence or hardcoded as PASS.
Supply a fresh audit JSON produced after executing the named checks.
"""
from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import platform
import subprocess
import shutil
import os
from PIL import Image, __version__

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
PNG = ROOT / 'public/amended_contact_sheet.png'
CHECKS = ('Builder', 'Deterministic rebuild', 'RGB validation', 'Metadata clue',
          'Metadata flag leak', 'Reference extraction', 'Exact flag recovery',
          'Checksum', 'Public release validation', 'Participant download',
          'Wrong flag', 'Correct flag', 'Duplicate scoring', 'Recovery',
          'MT-01 regression', 'Browser/UI', 'Access policy', 'Security audit')

def main():
    parser = ArgumentParser()
    parser.add_argument('--results', type=Path, required=True,
                        help='Fresh JSON with timestamp, png_sha256, challenge_id and checks')
    args = parser.parse_args()
    results = json.loads(args.results.read_text())
    measured_at = datetime.fromisoformat(results['timestamp'])
    if measured_at.tzinfo is None or abs((datetime.now(timezone.utc)-measured_at).total_seconds()) > 3600:
        raise ValueError('Audit results must be timezone-aware and less than one hour old')
    actual_hash = hashlib.sha256(PNG.read_bytes()).hexdigest()
    if results['png_sha256'] != actual_hash:
        raise ValueError('Audit results refer to a different PNG')
    checks = results['checks']
    if set(checks) != set(CHECKS) or any(value not in ('PASS', 'FAIL') for value in checks.values()):
        raise ValueError('Audit results must supply every named PASS/FAIL check')
    with Image.open(PNG) as image:
        image.load()
        dimensions = f'{image.width}x{image.height}'
        mode = image.mode
        capacity = image.width * image.height
    payload_length = (ROOT/'private/payload.txt').stat().st_size
    exif = shutil.which('exiftool')
    env = os.environ.copy()
    if exif is None:
        local = PROJECT/'.venv-author/exiftool-root/usr/bin/exiftool'
        if not local.is_file():
            raise RuntimeError('ExifTool is required to record the build status')
        exif = str(local)
        env['PERL5LIB'] = str(PROJECT/'.venv-author/exiftool-root/usr/share/perl5')
    exif_version = subprocess.check_output([exif, '-ver'], env=env, text=True).strip()
    status = '\n'.join(f'{name}: {checks[name]}' for name in CHECKS)
    (ROOT/'docs/MT02_BUILD_STATUS.md').write_text(f'''# MT-02 build status

Audit date/time: {measured_at.isoformat()}
Python version: {platform.python_version()}
Pillow version: {__version__}
ExifTool version: {exif_version}
CTFd version: 3.8.7
MT-02 challenge ID: {results['challenge_id']}
MT-02 value: 150
PNG dimensions: {dimensions}
PNG mode: {mode}
Payload byte length: {payload_length}
Required embedding bits: {32+payload_length*8}
Available pixel capacity: {capacity}
PNG SHA-256: {actual_hash}

{status}

Independent human review: PENDING
Overall status: IMPLEMENTED BUT NOT VERIFIED
Technical implementation and platform tests pass; independent Member 03 participant-only solve remains pending.
''')

if __name__ == '__main__':
    main()
