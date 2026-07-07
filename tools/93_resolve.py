# -*- coding: utf-8 -*-
# 평문(P) 대조로 압축 스트림 토큰 의미를 자동 해석
import os, sys, json, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom

SCRATCH = r'C:\Users\OXP2\AppData\Local\Temp\claude\C--Emul-Switch------xdeltaUI\9051f8c9-9e53-4b19-908e-4785eea82f4a\scratchpad'
BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
raw = open(os.path.join(SCRATCH, 'state.bin'), 'rb').read()
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}
off, sz = files['TIT_1L3.SCM']
d = sang[off:off+sz]
mofs = struct.unpack_from('<8H', d, 0)[4]
C = d[mofs:]

P0 = 0x23d000
P = [raw[P0+i] | (raw[P0+i+1] << 8) for i in range(0, 0x2000, 2)]  # 4096엔트리(8KB) 넉넉히

pi = 874       # 평문 시작 엔트리 (92_crack에서 확인)
ci = 2         # 스트림 위치 (헤더 00 04 스킵)
stats = []
def u16c(o): return C[o] | (C[o+1] << 8)
steps = 0
while ci < len(C) - 1 and steps < 3000:
    ctrl = C[ci]
    if ctrl == 0x40:   # 확장 리터럴: 다음 바이트 = 개수(추정 N 또는 N+1) → P로 검증
        N = C[ci+1]
        got = 0
        o = ci + 2
        while o + 1 < len(C) and pi + got < len(P) and u16c(o) == P[pi + got]:
            got += 1; o += 2
            if got > 300: break
        stats.append(('XLIT', N, got))
        pi += got; ci = ci + 2 + got*2
        steps += 1
        continue
    nlit = 0
    o = ci + 1
    while o + 1 < len(C) and pi + nlit < len(P) and u16c(o) == P[pi + nlit]:
        nlit += 1; o += 2
        if nlit > 130: break
    nrle = ninc = 0
    if ci + 2 < len(C):
        v = u16c(ci + 1)
        while pi + nrle < len(P) and P[pi + nrle] == v:
            nrle += 1
            if nrle > 400: break
        while pi + ninc < len(P) and P[pi + ninc] == (v + ninc) & 0xFFFF:
            ninc += 1
            if ninc > 400: break
    if nlit == 0 and nrle == 0 and ninc == 0:
        print(f'@{ci} ctrl={ctrl:#04x}: 해석불가 (P[{pi}]={P[pi]:#06x}, next u16={u16c(ci+1):#06x}, next bytes={C[ci:ci+8].hex(" ")})')
        break
    # ctrl 범위로 종류 판별: <0x40 LIT, 0x80-0xBF RLE, 0xC0+ INC
    if ctrl < 0x40:
        stats.append(('LIT', ctrl, nlit))
        pi += nlit; ci = ci + 1 + nlit*2
    elif ctrl >= 0xC0:
        n = (ctrl & 0x3F) + 2
        stats.append(('INC', ctrl, min(ninc, n)))
        pi += n; ci = ci + 3
    else:
        n = (ctrl & 0x3F) + 2
        stats.append(('RLE', ctrl, min(nrle, n)))
        pi += n; ci = ci + 3
    steps += 1
print(f'토큰 {len(stats)}개 해석, 최종 ci={ci}/{len(C)} pi={pi}')
# ctrl → count 관계 도출
from collections import defaultdict
rel = defaultdict(set)
for kind, ctrl, cnt in stats:
    rel[(kind, ctrl)].add(cnt)
for (kind, ctrl), cnts in sorted(rel.items()):
    print(f'{kind} ctrl={ctrl:#04x}: counts={sorted(cnts)}')
