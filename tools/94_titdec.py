# -*- coding: utf-8 -*-
# TIT_1L* 압축 맵 해독·왕복 검증·렌더 (타일 베이스 자동 추정)
import os, sys, json, struct
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, bgscm, scmimg
from PIL import Image

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}

for nm in ('TIT_1R.SCM', 'TIT_0R.SCM', 'TIT_0.SCM', 'TIT_2L.SCM', 'TIT_2L_.SCM', 'TIT_L.SCM', 'TIT_R.SCM', 'TITLE_L.SCM', 'TITLE_R.SCM'):
    off, sz = files[nm]
    d = sang[off:off+sz]
    info = bgscm.parse(d)
    mofs = info['u16'][4]
    C = d[mofs:]
    hdr, ent, used = bgscm.decode_map(C)
    # 왕복
    enc = bgscm.encode_map(hdr, ent)
    hdr2, ent2, _ = bgscm.decode_map(enc)
    ok = ent2 == ent
    # 타일 베이스 추정: 커버리지 최대
    ntiles = info['ntiles']
    tiles = [e & 0x3FF for e in ent if e]
    bestB = 0; bestCov = -1
    for B in range(0, 1024 - 1, 32):
        cov = sum(1 for t in tiles if B <= t < B + ntiles)
        if cov > bestCov:
            bestCov, bestB = cov, B
    print(f'{nm}: 해독 {len(ent)}엔트리(스트림 {used}/{len(C)}B) 왕복={ok} '
          f'재인코딩 {len(enc)}B(원본 {len(C)}B) 베이스≈{bestB} 커버 {bestCov}/{len(tiles)}')
    # 렌더 (32폭, 베이스 보정)
    cols = scmimg.pal_to_rgb(info['pal'])
    tl = info['tiles']
    Wt = 32
    Ht = (len(ent) + Wt - 1) // Wt
    img = Image.new('RGB', (Wt*8, Ht*8), (255, 0, 255))
    px = img.load()
    for i, e in enumerate(ent):
        t = (e & 0x3FF) - bestB
        if not (0 <= t < ntiles): continue
        hf = (e >> 10) & 1; vf = (e >> 11) & 1; p = (e >> 12) & 0xF
        tx, ty = (i % Wt)*8, (i // Wt)*8
        base = t*32
        for y in range(8):
            for x in range(8):
                b = tl[base+y*4+x//2]
                v = (b >> 4) if (x & 1) else (b & 0xF)
                ci = p*16+v
                sx = 7-x if hf else x; sy = 7-y if vf else y
                if ci < len(cols):
                    px[tx+sx, ty+sy] = cols[ci]
    img = img.transpose(Image.ROTATE_90)
    img.save(os.path.join(WORK, f'titdec_{nm}.png'))
print('렌더 저장 완료')
