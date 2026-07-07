# -*- coding: utf-8 -*-
# 실제 스크린샷에서 TIT_1L1 타일 매칭 → 진짜 맵 역산 → 저장 스트림과 상관
import os, sys, json, struct
from collections import Counter
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

nm = sys.argv[1] if len(sys.argv) > 1 else 'TIT_1L1.SCM'
shot = sys.argv[2] if len(sys.argv) > 2 else 'shot_e1.png'
off, sz = files[nm]
info = bgscm.parse(sang[off:off+sz])
tiles = info['tiles']; pal = info['pal']
ntiles = len(tiles)//32
nrows = len(pal)//32  # 팔레트 행수 (16색*2B=32B/행)

def mkcols(conv):
    cols = []
    for i in range(0, len(pal), 2):
        v = pal[i] | (pal[i+1] << 8)
        r = (v & 31); g = ((v >> 5) & 31); b = ((v >> 10) & 31)
        if conv == 0: cols.append(((r<<3), (g<<3), (b<<3)))
        else: cols.append(((r<<3)|(r>>2), (g<<3)|(g>>2), (b<<3)|(b>>2)))
    return cols

im = Image.open(os.path.join(WORK, shot)).convert('RGB')
# 하단(터치) 화면 = FB 행 192~383
scr = im.crop((0, 192, 256, 384))
spx = scr.load()

for conv in (0, 1):
    cols = mkcols(conv)
    # 타일 해시 사전: (i, p, hf, vf) -> 64픽셀 rgb tuple
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
    best = None
    for dy in range(8):
        for dx in range(8):
            hits = 0
            for cy in range((192-dy)//8):
                for cx in range((256-dx)//8):
                    key = tuple(spx[dx+cx*8+x, dy+cy*8+y] for y in range(8) for x in range(8))
                    if key in lut: hits += 1
            if best is None or hits > best[0]:
                best = (hits, dx, dy)
    print(f'conv={conv}: 최적 정렬 dx={best[1]} dy={best[2]} 매칭셀={best[0]}')
    if best[0] > 50:
        hits, dx, dy = best
        # 진짜 맵 추출
        out = []
        for cy in range((192-dy)//8):
            for cx in range((256-dx)//8):
                key = tuple(spx[dx+cx*8+x, dy+cy*8+y] for y in range(8) for x in range(8))
                m = lut.get(key)
                out.append((cx, cy, m))
        got = [(cx, cy, m) for cx, cy, m in out if m]
        print(f'  매칭 {len(got)}셀. 샘플 (cx,cy)->(tile,pal,hf,vf):')
        for cx, cy, m in got[:30]:
            print(f'    ({cx:2d},{cy:2d}) -> t{m[0]:3d} p{m[1]} h{m[2]} v{m[3]}')
        json.dump([[cx, cy, list(m)] for cx, cy, m in got],
                  open(os.path.join(WORK, 'truemap.json'), 'w'))
        print('  -> truemap.json')
        break
