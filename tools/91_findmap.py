# -*- coding: utf-8 -*-
# 스테이트에서 BG 맵 탐색: 32엔트리 스트라이드로 타일값 +1씩 증가하는 세로열 시그니처
import os, sys, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
SCRATCH = r'C:\Users\OXP2\AppData\Local\Temp\claude\C--Emul-Switch------xdeltaUI\9051f8c9-9e53-4b19-908e-4785eea82f4a\scratchpad'
raw = open(os.path.join(SCRATCH, 'state.bin'), 'rb').read()

def u16(o): return raw[o] | (raw[o+1] << 8)

cands = {}
LO, HI = 0x1F0000, 0x270000
for o in range(LO, HI, 2):
    v0 = u16(o)
    t0 = v0 & 0x3FF
    if t0 == 0 or t0 > 1000: continue
    run = 1
    while run < 20:
        v = u16(o + 64*run)
        if (v & 0x3FF) == t0 + run and (v >> 12) == (v0 >> 12):
            run += 1
        else:
            break
    if run >= 12:
        cands[o] = (t0, run)
# 정리: 같은 맵의 열들이 다수 → 2KB 정렬 기준으로 군집
from collections import Counter
grp = Counter()
for o, (t0, run) in cands.items():
    grp[o & ~0x7FF] += 1
for base, cnt in grp.most_common(10):
    print(f'맵후보 base~{base:#x}: 세로열 {cnt}개')
    for o, (t0, run) in sorted(cands.items()):
        if (o & ~0x7FF) == base:
            print(f'   @{o:#x} tile{t0} run{run} col={(o-base)//2%32}')
            break
