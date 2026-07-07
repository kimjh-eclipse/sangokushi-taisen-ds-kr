# -*- coding: utf-8 -*-
# 같은 팔레트 셀들 행별 diff → 구슬 무늬가 버튼간 동일한지, 글자영역이 어디인지 정밀 파악
import os, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, scmimg, cncp

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}
r = scmimg.decode(sang[files['BTNALL.SCM'][0]:files['BTNALL.SCM'][0]+files['BTNALL.SCM'][1]])
g = r['gfx']
info = cncp.parse(g)

def index_map(ci):
    cell = info['cells'][ci]
    m = [[0]*32 for _ in range(40)]
    for a0, a1, a2 in cell['oams']:
        shape=(a0>>14)&3; size=(a1>>14)&3
        w,h = cncp.OBJ_SIZES[(shape,size)]
        x = cncp.sgn(a1&0x1FF,9)+20; y = cncp.sgn(a0&0xFF,8)+20
        tile = a2 & 0x3FF
        tw, th = w//8, h//8
        for ty in range(th):
            for tx in range(tw):
                tofs = cell['gfxBase'] + (tile+ty*tw+tx)*32
                for yy in range(8):
                    for xx in range(8):
                        b = g[tofs+yy*4+xx//2]
                        v = (b>>4) if (xx&1) else (b&0xF)
                        m[y+ty*8+yy][x+tx*8+xx] = v
    return m

pairs = [
    ('pal0: cell0(決定) vs cell6(はい)', 0, 6),
    ('pal0: cell0(決定) vs cell36(交換)', 0, 36),
    ('pal0: cell6(はい) vs cell36(交換)', 6, 36),
    ('pal2: cell9(戻る) vs cell12(いいえ)', 9, 12),
    ('pal2: cell9(戻る) vs cell15(切替)', 9, 15),
    ('pal4: cell29(はい灰) vs cell31(いいえ灰)', 29, 31),
    ('상태: cell6 vs cell7', 6, 7),
    ('교차팔레트: cell6(pal0) vs cell12(pal2)', 6, 12),
    ('교차팔레트: cell0(pal0) vs cell9(pal2)', 0, 9),
    ('회색vs빨강: cell29(pal4) vs cell6(pal0)', 29, 6),
]
for title, a, b in pairs:
    ma, mb = index_map(a), index_map(b)
    rows = []
    for y in range(40):
        d = sum(1 for x in range(32) if ma[y][x]!=mb[y][x])
        rows.append(d)
    tot = sum(rows)
    print(f'{title}: 총 {tot}')
    print('  행별: ' + ' '.join(f'{y}:{d}' for y,d in enumerate(rows) if d))
