# -*- coding: utf-8 -*-
# 덱편집 화면 우하단 버튼(計略説明/決定/戻る)의 소스 SCM 탐색:
#  스크린샷 해당 영역 8x8셀 ↔ 모든 CNCP SCM 타일 LUT 대조
import os, sys, json
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, scmimg, cncp
from PIL import Image

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))

SKIP = ('MA2','NP_','NPS','BU_','FCE','CA_','NV_','FC_','ITE','HAI','KE_','TKE','C20','GET')
cands = [n for n, o, s in toc if n.endswith('.SCM') and not n.startswith(SKIP)
         and not n.startswith(('F_0','F_1','F_2','F_3','F_4','F_5','F_6','F_7'))]
files = {n: (o, s) for n, o, s in toc}

im = Image.open(os.path.join(WORK, 'edit_1.png')).convert('RGB')
scr = im.crop((0, 192, 256, 384))
spx = scr.load()
# 대상 영역: cx 0..3, cy 2..23 (버튼 밴드)
targets = {}
for cy in range(2, 24):
    for cx in range(0, 4):
        key = tuple(spx[cx*8+x, cy*8+y] for y in range(8) for x in range(8))
        if len(set(key)) > 2:   # 단색/2색 셀 제외 (구조적 셀만)
            targets[(cx, cy)] = key
print(f'대상 구조셀 {len(targets)}개, 후보 파일 {len(cands)}개')

hits_by_file = {}
for nm in cands:
    off, sz = files[nm]
    d = sang[off:off+sz]
    try:
        r = scmimg.decode(d)
        g = r['gfx']
        if g[:4] != b'CNCP': continue
        info = cncp.parse(g)
    except Exception:
        continue
    pal = r['pal']
    cols = []
    for i in range(0, len(pal), 2):
        v = pal[i] | (pal[i+1] << 8)
        rr = (v & 31); gg = ((v >> 5) & 31); bb = ((v >> 10) & 31)
        cols.append(((rr<<3)|(rr>>2), (gg<<3)|(gg>>2), (bb<<3)|(bb>>2)))
    ntiles = (info['gfxStart'] and (len(g) - 0x20)//32) or 0
    # 타일 수: cellTbl 시작 전까지
    ntiles = (info['cellOfs'] - 0x20)//32
    nrows = len(pal)//32
    lut = set()
    keys = {}
    for i in range(ntiles):
        base = 0x20 + i*32
        idx = [[0]*8 for _ in range(8)]
        for y in range(8):
            for x in range(8):
                b = g[base+y*4+x//2]
                idx[y][x] = (b>>4) if (x&1) else (b&0xF)
        for p in range(nrows):
            row = [cols[p*16+v] if p*16+v < len(cols) else (255,0,255) for v in range(16)]
            for hf in (0,1):
                for vf in (0,1):
                    k = tuple(row[idx[7-y if vf else y][7-x if hf else x]] if idx[7-y if vf else y][7-x if hf else x] else None
                              for y in range(8) for x in range(8))
                    keys[k] = i
    cnt = 0
    where = []
    for (cx, cy), tk in targets.items():
        for k, ti in keys.items():
            solid = sum(1 for kv in k if kv is not None)
            if solid >= 40 and all(kv is None or kv == tv for kv, tv in zip(k, tk)):
                cnt += 1; where.append(((cx, cy), ti))
                break
    if cnt:
        hits_by_file[nm] = (cnt, where[:6])
for nm, (cnt, wh) in sorted(hits_by_file.items(), key=lambda z: -z[1][0])[:12]:
    print(f'{nm}: {cnt}셀 매칭  예: {wh}')
