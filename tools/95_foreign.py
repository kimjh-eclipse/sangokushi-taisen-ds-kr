# -*- coding: utf-8 -*-
# TIT_0R 외부참조 타일을 VRAM에서 추출 → NFP 전 파일에서 소스 검색
import os, sys, json, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, bgscm, scmimg

SCRATCH = r'C:\Users\OXP2\AppData\Local\Temp\claude\C--Emul-Switch------xdeltaUI\9051f8c9-9e53-4b19-908e-4785eea82f4a\scratchpad'
BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
raw = open(os.path.join(SCRATCH, 'state.bin'), 'rb').read()
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}

off, sz = files['TIT_0R.SCM']
d = sang[off:off+sz]
info = bgscm.parse(d)
hdr, ent, _ = bgscm.decode_map(d[info['u16'][4]:])
ntiles = info['ntiles']

# VRAM에서 TIT_0R 타일 베이스 찾기
tiles = info['tiles']
bases = []
for t in range(ntiles):
    b = bytes(tiles[t*32:(t+1)*32])
    if len(set(b)) <= 6: continue
    i = raw.find(b)
    if i >= 0: bases.append(i - t*32)
    if len(bases) >= 10: break
from collections import Counter
vb = Counter(bases).most_common(1)[0][0]
print('TIT_0R VRAM 베이스:', hex(vb))

foreign = sorted({e & 0x3FF for e in ent if (e & 0x3FF) >= ntiles})
print(f'외부 참조 타일 {len(foreign)}개: {foreign[:20]}')

# 외부 타일 바이트 추출 → NFP 전 파일 검색
probes = []
for idx in foreign:
    tb = raw[vb + idx*32: vb + (idx+1)*32]
    if len(set(tb)) > 6:
        probes.append((idx, bytes(tb)))
print(f'구조적 프로브 {len(probes)}개')
hits = {}
searched = 0
for nm, o, s in toc:
    if not nm.endswith('.SCM'): continue
    dd = sang[o:o+s]
    try:
        g = scmimg.decode(dd)['gfx']
    except Exception:
        continue
    searched += 1
    for idx, tb in probes[:24]:
        j = bytes(g).find(tb)
        if j >= 0:
            hits.setdefault(nm, []).append((idx, j))
print(f'검색 파일 {searched}')
for nm, hh in sorted(hits.items(), key=lambda z: -len(z[1])):
    print(f'{nm}: {len(hh)}개 일치 {hh[:4]}')
