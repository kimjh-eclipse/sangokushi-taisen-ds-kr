# -*- coding: utf-8 -*-
# 모드배너 5상태 스크린샷 ↔ TIT_1L0~4 타일 매칭 → truemap_<파일>.json
import os, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, bgscm
from PIL import Image

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}

PAIRS = [
    ('TIT_1L0.SCM', 'mode_selA.png'),
    ('TIT_1L1.SCM', 'mode_selB.png'),
    ('TIT_1L2.SCM', 'mode_sel2.png'),
    ('TIT_1L3.SCM', 'mode_sel3.png'),
    ('TIT_1L4.SCM', 'mode_sel4.png'),
]

def cols_of(pal):
    cols = []
    for i in range(0, len(pal), 2):
        v = pal[i] | (pal[i+1] << 8)
        r = (v & 31); g = ((v >> 5) & 31); b = ((v >> 10) & 31)
        cols.append(((r<<3)|(r>>2), (g<<3)|(g>>2), (b<<3)|(b>>2)))
    return cols

for nm, shot in PAIRS:
    off, sz = files[nm]
    info = bgscm.parse(sang[off:off+sz])
    tiles = info['tiles']; pal = info['pal']
    ntiles = len(tiles)//32; nrows = len(pal)//32
    cols = cols_of(pal)
    lut = {}
    for i in range(ntiles):
        base = i*32
        idx = [[0]*8 for _ in range(8)]
        for y in range(8):
            for x in range(8):
                b = tiles[base+y*4+x//2]
                idx[y][x] = (b>>4) if (x&1) else (b&0xF)
        for p in range(nrows):
            row = [cols[p*16+v] for v in range(16)]
            for hf in (0,1):
                for vf in (0,1):
                    key = tuple(row[idx[7-y if vf else y][7-x if hf else x]] for y in range(8) for x in range(8))
                    lut.setdefault(key, (i, p, hf, vf))
    im = Image.open(os.path.join(WORK, shot)).convert('RGB')
    scr = im.crop((0, 192, 256, 384))
    spx = scr.load()
    got = []
    for cy in range(24):
        for cx in range(32):
            key = tuple(spx[cx*8+x, cy*8+y] for y in range(8) for x in range(8))
            m = lut.get(key)
            if m: got.append((cx, cy, list(m)))
    json.dump(got, open(os.path.join(WORK, f'truemap_{nm}.json'), 'w'))
    print(f'{nm} ({shot}): 매칭 {len(got)}셀 / 768')
