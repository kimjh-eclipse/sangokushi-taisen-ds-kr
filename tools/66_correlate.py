# -*- coding: utf-8 -*-
# truemap(화면 역산) ↔ 저장 맵 스트림 상관: 엔트리 값·위치 관계 규명
import os, sys, json, struct
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, bgscm

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}
nm = 'TIT_1L1.SCM'
off, sz = files[nm]
d = sang[off:off+sz]
u16h = struct.unpack_from('<8H', d, 0)
mofs = u16h[4]
raw = d[mofs:]
print(f'맵 영역 {len(raw)}B')

tm = json.load(open(os.path.join(WORK, 'truemap.json'), encoding='utf-8'))
# 기대 엔트리값
exp = {}
for cx, cy, (t, p, hf, vf) in tm:
    exp[(cx, cy)] = t | (hf << 10) | (vf << 11) | (p << 12)

# 저장 스트림에서 각 기대값의 등장 위치(바이트 오프셋, 모든 정렬)
pos = {}
for (c, e) in exp.items():
    b = struct.pack('<H', e)
    ps = []
    st = 0
    while True:
        i = raw.find(b, st)
        if i < 0: break
        ps.append(i); st = i+1
    pos[c] = ps

found = sum(1 for c in pos if pos[c])
uniq = [(c, pos[c][0]) for c in pos if len(pos[c]) == 1]
print(f'기대값이 스트림에 존재: {found}/{len(exp)}  유일위치: {len(uniq)}')
for (cx, cy), p in sorted(uniq, key=lambda z: z[1])[:40]:
    print(f'  ({cx:2d},{cy:2d}) -> 바이트오프셋 {p} (홀짝 {p%2})')
