# -*- coding: utf-8 -*-
# 정규화(인덱스 등장순 치환) 타일 검색: EDCR01_4 決/戻 글자 타일과 모양이 같은 타일 보유 파일 탐색
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

def canon(tile32):
    """4bpp 타일 → 인덱스 등장순 정규화 니블 문자열"""
    mapping = {}
    out = []
    for b in tile32:
        for v in (b & 0xF, b >> 4):
            if v not in mapping:
                mapping[v] = len(mapping)
            out.append(mapping[v])
    return bytes(out)

off, sz = files['EDCR01_4.SCM']
src = scmimg.decode(sang[off:off+sz])['gfx']
probes = set()
for t in (0, 1, 2, 3, 8, 9, 24, 25, 26, 34, 54, 55, 62, 78, 79, 88):
    b = bytes(src[0x20 + t*32: 0x20 + (t+1)*32])
    if len(set(b)) > 4:
        probes.add(canon(b))
print(f'정규화 프로브 {len(probes)}개')

hits = {}
for nm, o, s in toc:
    if not nm.endswith('.SCM') or nm == 'EDCR01_4.SCM': continue
    d = sang[o:o+s]
    try:
        g = scmimg.decode(d)['gfx']
    except Exception:
        continue
    n = len(g)//32
    cnt = 0
    for i in range(n):
        c = canon(bytes(g[i*32:(i+1)*32]))
        if c in probes:
            cnt += 1
    if cnt:
        hits[nm] = cnt
for nm, cnt in sorted(hits.items(), key=lambda z: -z[1])[:15]:
    print(f'{nm}: 일치타일 {cnt}')
