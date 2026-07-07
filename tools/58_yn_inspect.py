# -*- coding: utf-8 -*-
# BTNALL cell6(はい)/cell12(いいえ) 픽셀을 팔레트 인덱스 단위로 ASCII 덤프
# → 글자 영역·사용 색인덱스 파악 (식자 전 분석)
import os, sys, json, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, scmimg, cncp

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}
off, sz = files['BTNALL.SCM']
d = sang[off:off+sz]
r = scmimg.decode(d)
g = r['gfx']
pal = scmimg.pal_to_rgb(r['pal'])
info = cncp.parse(g)

def index_map(cell):
    """셀의 OAM들을 조립해 팔레트 인덱스 2D 배열 반환 (bg=-1)"""
    boxes = []
    for a0, a1, a2 in cell['oams']:
        shape = (a0 >> 14) & 3; size = (a1 >> 14) & 3
        w, h = cncp.OBJ_SIZES[(shape, size)]
        x = cncp.sgn(a1 & 0x1FF, 9); y = cncp.sgn(a0 & 0xFF, 8)
        boxes.append((x, y, w, h))
    x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
    x1 = max(b[0]+b[2] for b in boxes); y1 = max(b[1]+b[3] for b in boxes)
    W, H = x1-x0, y1-y0
    m = [[-1]*W for _ in range(H)]
    pals = set()
    for a0, a1, a2 in cell['oams']:
        shape = (a0 >> 14) & 3; size = (a1 >> 14) & 3
        w, h = cncp.OBJ_SIZES[(shape, size)]
        x = cncp.sgn(a1 & 0x1FF, 9) - x0; y = cncp.sgn(a0 & 0xFF, 8) - y0
        hf = (a1 >> 12) & 1; vf = (a1 >> 13) & 1
        tile = a2 & 0x3FF; palno = (a2 >> 12) & 0xF
        pals.add(palno)
        tw, th = w//8, h//8
        for ty in range(th):
            for tx in range(tw):
                tofs = cell['gfxBase'] + (tile + ty*tw + tx)*32
                for yy in range(8):
                    for xx in range(8):
                        b = g[tofs + yy*4 + xx//2]
                        v = (b >> 4) if (xx & 1) else (b & 0xF)
                        sx = tx*8+xx; sy = ty*8+yy
                        if hf: sx = w-1-sx
                        if vf: sy = h-1-sy
                        m[y+sy][x+sx] = v   # 인덱스 자체 기록(0 포함)
    return m, pals

HEX = '0123456789ABCDEF'
for ci in (6, 12):
    cell = info['cells'][ci]
    print(f'=== cell {ci} === oams:')
    for a0, a1, a2 in cell['oams']:
        shape=(a0>>14)&3; size=(a1>>14)&3
        w,h = cncp.OBJ_SIZES[(shape,size)]
        print(f'  {w}x{h} x={cncp.sgn(a1&0x1FF,9)} y={cncp.sgn(a0&0xFF,8)} '
              f'tile={a2&0x3FF} pal={(a2>>12)&0xF} hf={(a1>>12)&1} vf={(a1>>13)&1}')
    m, pals = index_map(cell)
    print(f'  size={len(m[0])}x{len(m)} pals={sorted(pals)}')
    for row in m:
        print('  ' + ''.join('.' if v <= 0 else HEX[v] for v in row))
    # 인덱스 히스토그램
    from collections import Counter
    c = Counter(v for row in m for v in row if v > 0)
    palno = sorted(pals)[0]
    print('  히스토그램(인덱스: 개수, RGB):')
    for v, n in c.most_common():
        rgb = pal[palno*16 + v]
        print(f'    {HEX[v]}: {n:4d}  {rgb}')
