# -*- coding: utf-8 -*-
# 세이브스테이트에서 OBJ VRAM 특정: 알려진 한글 타일 바이트 검색 → 주변을 4bpp 타일시트로 렌더
import os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import scmimg
from PIL import Image

SCRATCH = r'C:\Users\OXP2\AppData\Local\Temp\claude\C--Emul-Switch------xdeltaUI\9051f8c9-9e53-4b19-908e-4785eea82f4a\scratchpad'
WORK = r'C:\Emul\Switch\패치유틸.xdeltaUI\work'
raw = open(os.path.join(SCRATCH, 'state.bin'), 'rb').read()

# 프로브: 우리가 식자한 EDCR01_4.kr / BTNALL.kr / NP 명판의 타일들
probes = []
def add_probes(path, nm):
    d = open(path, 'rb').read()
    g = scmimg.decode(d)['gfx']
    if g[:4] != b'CNCP': return
    for t in range(0, len(g)//32):
        b = bytes(g[0x20 + t*32: 0x20 + (t+1)*32])
        if len(set(b)) > 6:
            probes.append((nm, t, b))
for nm in ('NPS_3042.SCM', 'NPS_1039.SCM', 'NP_3042.SCM'):
    add_probes(os.path.join(WORK, 'np_kr', nm), nm)
for nm in ('EDCL01_1.SCM.kr', 'ED_BOTAN.SCM.kr', 'EDCR01_4.SCM.kr'):
    add_probes(os.path.join(WORK, nm), nm)
print(f'프로브 {len(probes)}')
hitbases = {}
for nm, t, b in probes:
    i = raw.find(b)
    if i >= 0:
        hitbases.setdefault(nm, []).append((t, i))
for nm, hits in hitbases.items():
    print(nm, f'히트 {len(hits)}:', [(t, hex(i)) for t, i in hits[:8]])
