#!/usr/bin/env python3
"""Deterministic, synthetic MT-02 contact sheet and red-LSB payload builder."""
from pathlib import Path
import hashlib
import random
import struct
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

ROOT = Path(__file__).resolve().parents[1]
SEED = 'MERIDIAN-MT02-V1'
TOKEN = 'quiet_manifest_revision'
FLAG = f'MT{{mt02_{TOKEN}}}'
CLUE = 'Creation note: the release annotation was preserved in the lowest-order red image data.'
SIZE = (1080, 720)

def payload_text():
    return ('MERIDIAN TRANSFER / RELEASE ANNOTATION\n'
            'Contact sheet revision: handover set C, amended copy.\n'
            'The original visible panels are retained for comparison.\n'
            f'Stage verification: {FLAG}\n')

def make_image():
    rng = random.Random(SEED)
    image = Image.new('RGB', SIZE, (235, 239, 235))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.rectangle((0, 0, 1079, 80), fill=(23, 51, 60))
    draw.text((35, 22), 'MERIDIAN TRANSFER  /  REVIEW CONTACT SHEET', fill='white', font=font)
    draw.text((35, 49), 'CASE MT-R17  |  SYNTHETIC HANDOVER RECORDS  |  REVISION C', fill=(183, 217, 205), font=font)
    labels = ['SEALED ENVELOPE', 'TRANSFER CRATE', 'RELEASE DESK', 'ROUTE CARD', 'ACCESS BADGE', 'ARCHIVE FILE']
    colors = [(70, 119, 132), (110, 129, 96), (158, 124, 81), (92, 110, 146), (130, 105, 130), (110, 133, 125)]
    for i, (label, color) in enumerate(zip(labels, colors)):
        col, row = i % 3, i // 3
        x, y = 35 + col * 345, 105 + row * 285
        draw.rectangle((x, y, x+320, y+260), fill=(250, 250, 246), outline=(135, 148, 145), width=2)
        draw.rectangle((x+15, y+15, x+305, y+205), fill=color)
        # Fictional specimen thumbnails use geometry only.
        for j in range(7):
            px = x + 28 + j * 38
            py = y + 32 + rng.randrange(20, 115)
            draw.rectangle((px, py, px+18, min(y+192, py+40+rng.randrange(15))), fill=(190+rng.randrange(30), 205, 196))
        draw.ellipse((x+105, y+45, x+215, y+155), outline=(238, 227, 194), width=6)
        draw.line((x+60, y+170, x+260, y+170), fill=(220, 225, 215), width=3)
        draw.text((x+17, y+219), f'{i+1:02d} / {label}', fill=(31, 56, 61), font=font)
        draw.text((x+17, y+240), 'MERIDIAN / FICTIONAL SPECIMEN', fill=(93, 110, 108), font=font)
    draw.text((35, 688), 'CONTROLLED REVIEW COPY  -  IMAGE PANELS ARE SYNTHETIC', fill=(62, 81, 83), font=font)
    return image

def build():
    public, private = ROOT/'public', ROOT/'private'
    public.mkdir(exist_ok=True); private.mkdir(exist_ok=True)
    data = payload_text().encode('utf-8')
    if len(data) > 0xffffffff:
        raise ValueError('Payload exceeds uint32 length')
    stream = struct.pack('>I', len(data)) + data
    image = make_image()
    if len(stream)*8 > image.width*image.height:
        raise ValueError('Payload exceeds red-channel capacity')
    pixels = image.load()
    for i, byte in enumerate(stream):
        for offset in range(8):
            bit_index = i*8 + offset
            x, y = bit_index % image.width, bit_index // image.width
            r, g, b = pixels[x, y]
            pixels[x, y] = ((r & 0xfe) | ((byte >> (7-offset)) & 1), g, b)
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text('Comment', CLUE)
    path = public/'amended_contact_sheet.png'
    image.save(path, format='PNG', pnginfo=metadata, compress_level=9, optimize=False)
    with Image.open(path) as saved:
        if saved.mode != 'RGB': raise AssertionError('Saved PNG is not RGB')
    (private/'payload.txt').write_bytes(data)
    (private/'flag.txt').write_text(FLAG+'\n', encoding='utf-8')
    (private/'flag.txt').chmod(0o600)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (public/'SHA256SUMS').write_text(f'{digest}  amended_contact_sheet.png\n')
    print(f'Built {path.name}: {image.width}x{image.height}, {len(data)} payload bytes, SHA-256 {digest}')
    return digest
if __name__ == '__main__': build()
