# -*- coding: utf-8 -*-
# 모드선택(軍議 선택) 스테이트에서 TIT_1L3 타일·맵 위치 추출
import os, sys, json, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, bgscm

SCRATCH = r'C:\Users\OXP2\AppData\Local\Temp\claude\C--Emul-Switch------xdeltaUI\9051f8c9-9e53-4b19-908e-4785eea82f4a\scratchpad'
BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
raw = open(os.path.join(SCRATCH, 'state.bin'), 'rb').read()
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}

hits_all = {}
for nm in ('TIT_1L3.SCM', 'TIT_1L.SCM', 'TIT_1L0.SCM', 'TIT_0L.SCM', 'TIT_1R.SCM'):
    off, sz = files[nm]
    info = bgscm.parse(sang[off:off+sz])
    tiles = info['tiles']
    hits = []
    for t in range(len(tiles)//32):
        b = bytes(tiles[t*32:(t+1)*32])
        if len(set(b)) <= 6: continue
        i = raw.find(b)
        if i >= 0:
            hits.append((t, i))
        if len(hits) >= 12: break
    hits_all[nm] = hits
    if hits:
        # 타일 t가 위치 i에 → VRAM 베이스 = i - t*32, 로드 차베이스(타일단위) 추정
        bases = [i - t*32 for t, i in hits]
        from collections import Counter
        cb = Counter(bases).most_common(3)
        print(f'{nm}: 히트 {len(hits)}, 베이스 후보 {[(hex(b), c) for b, c in cb]}')
    else:
        print(f'{nm}: 히트 0')
