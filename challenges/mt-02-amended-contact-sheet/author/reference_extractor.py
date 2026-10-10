#!/usr/bin/env python3
"""Extract only from the public RGB PNG, using red LSBs in row-major order."""
from pathlib import Path
import re
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
def extract(path=None):
    path = Path(path) if path else ROOT/'public/amended_contact_sheet.png'
    with Image.open(path) as image:
        if image.mode != 'RGB': raise ValueError('Expected RGB PNG')
        capacity = image.width * image.height
        if capacity < 32: raise ValueError('Truncated length header')
        pixels = image.load()
        def byte_at(start):
            value = 0
            for index in range(start, start+8):
                x, y = index % image.width, index // image.width
                value = (value << 1) | (pixels[x, y][0] & 1)
            return value
        length = int.from_bytes(bytes(byte_at(i) for i in range(0, 32, 8)), 'big')
        if length == 0 or length > (capacity-32)//8:
            raise ValueError('Impossible or truncated payload length')
        data = bytes(byte_at(32+i*8) for i in range(length))
    text = data.decode('utf-8')
    flags = re.findall(r'MT\{mt02_[a-z0-9_]+\}', text)
    if len(flags) != 1: raise ValueError(f'Expected exactly one MT-02 flag, found {len(flags)}')
    return length, text, flags[0]
if __name__ == '__main__':
    length, text, flag = extract()
    print(f'Payload length: {length} bytes\nRecovered payload:\n{text}\nRecovered flag:\n{flag}')
