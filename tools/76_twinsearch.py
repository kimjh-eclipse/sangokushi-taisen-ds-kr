# -*- coding: utf-8 -*-
# EDCR01_4(決定/戻る) 원본 타일 바이트와 동일한 타일을 가진 SCM 전수 검색
import os, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, scmimg

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}

off, sz = files['EDCR01_4.SCM']
src = scmimg.decode(sang[off:off+sz])['gfx']
# 글자 타일들(셀0 t0-11, 셀2 t24-38): 0x20 + t*32
probes = []
for t in (0, 1, 2, 3, 8, 9, 24, 25, 26, 34, 54, 55, 62, 78, 79, 88):
    b = bytes(src[0x20 + t*32: 0x20 + (t+1)*32])
    if len(set(b)) > 2:
        probes.append((t, b))
print(f'프로브 타일 {len(probes)}개')

hits = {}
for nm, o, s in toc:
    if not nm.endswith('.SCM') or nm == 'EDCR01_4.SCM': continue
    d = sang[o:o+s]
    try:
        g = scmimg.decode(d)['gfx']
    except Exception:
        continue
    got = [t for t, b in probes if b in g]
    if got:
        hits[nm] = got
for nm, got in sorted(hits.items(), key=lambda z: -len(z[1])):
    print(f'{nm}: 프로브 {len(got)}개 일치 {got[:8]}')
