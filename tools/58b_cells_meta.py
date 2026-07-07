# -*- coding: utf-8 -*-
# BTNALL 48셀 전체 OAM 메타 덤프 + 동일 지오메트리 셀들 픽셀 다수결로 '깨끗한 구슬' 복원 가능성 확인
import os, sys, json
from collections import Counter
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
r = scmimg.decode(sang[off:off+sz])
g = r['gfx']
info = cncp.parse(g)

def geom(cell):
    gs = []
    for a0, a1, a2 in cell['oams']:
        shape=(a0>>14)&3; size=(a1>>14)&3
        w,h = cncp.OBJ_SIZES[(shape,size)]
        gs.append((w, h, cncp.sgn(a1&0x1FF,9), cncp.sgn(a0&0xFF,8)))
    return tuple(gs)

for i, c in enumerate(info['cells']):
    parts = []
    for a0, a1, a2 in c['oams']:
        shape=(a0>>14)&3; size=(a1>>14)&3
        w,h = cncp.OBJ_SIZES[(shape,size)]
        parts.append(f'{w}x{h}@({cncp.sgn(a1&0x1FF,9)},{cncp.sgn(a0&0xFF,8)}) t{a2&0x3FF} p{(a2>>12)&0xF}'
                     + ('H' if (a1>>12)&1 else '') + ('V' if (a1>>13)&1 else ''))
    print(f'cell{i:2d}: ' + ' | '.join(parts))
