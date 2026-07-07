# -*- coding: utf-8 -*-
# 모드선택 배너 3단계(정정판): 셀 단위 희망내용 집계 → 타일 기록 규칙 적용 → 재조립 → 시뮬 렌더
#  규칙: 타일 t 기록 가능 ⇔ t의 모든 '서로 다른 셀'이 (어느 상태에서든) 편집됐고 희망내용 일치.
#        미편집 셀만 걸린 타일/불일치 타일 = 원본 유지(해당 편집 픽셀은 포기 → 리포트)
import sys, os, json, struct
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, ndspy.lz10, bgscm
from PIL import Image

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
OUT = os.path.join(WORK, 'banner')
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}
off, sz = files['TIT_1R.SCM']
d = sang[off:off+sz]
info = bgscm.parse(d)
tiles = bytearray(info['tiles'])
NT = info['ntiles']
cellmaps = json.load(open(os.path.join(OUT, 'cellmaps.json')))
changed = json.load(open(os.path.join(OUT, 'changed_cells.json')))
pal = json.load(open(os.path.join(OUT, 'pal.json')))

def cell4(idx, ci):
    cx, cy = (ci % 32)*8, (ci // 32)*8
    out = bytearray(32)
    for y in range(8):
        for x in range(0, 8, 2):
            out[y*4+x//2] = (idx[cy+y][cx+x] & 0xF) | ((idx[cy+y][cx+x+1] & 0xF) << 4)
    return bytes(out)

def unflip(tb, hf, vf):
    if not hf and not vf: return bytes(tb)
    out = bytearray(32)
    for y in range(8):
        for x in range(8):
            b = tb[y*4+x//2]
            v = (b>>4) if (x&1) else (b&0xF)
            sx = 7-x if hf else x; sy = 7-y if vf else y
            if sx & 1: out[sy*4+sx//2] |= v<<4
            else: out[sy*4+sx//2] |= v
    return bytes(out)

edits = json.load if False else None
idxs = {k: json.load(open(os.path.join(OUT, f'edit{k}_idx.json'))) for k in map(str, range(1, 7))}
chset = {k: set(changed[k]) for k in changed}

# 타일 → 셀별 정보
tinfo = defaultdict(lambda: defaultdict(list))  # t -> cell -> [(state, content, edited)]
for k in map(str, range(1, 7)):
    for ci_s, (t, hf, vf, p) in cellmaps[k].items():
        ci = int(ci_s)
        content = unflip(cell4(idxs[k], ci), hf, vf)
        tinfo[t][ci].append((k, content, ci in chset[k]))

writes = {}
skipped_tiles = []
for t, bycell in tinfo.items():
    orig = bytes(tiles[t*32:(t+1)*32])
    cell_desired = {}
    ok = True
    for ci, lst in bycell.items():
        ed = [c for (k, c, e) in lst if e]
        if ed:
            if len(set(ed)) > 1: ok = False; break
            cell_desired[ci] = ed[0]
        else:
            cell_desired[ci] = None   # 미편집 셀
    if not ok:
        skipped_tiles.append((t, '동일셀 상태간 불일치')); continue
    des = {c for c in cell_desired.values() if c is not None}
    if not des:
        continue                       # 아무 편집 없음
    if len(des) > 1:
        skipped_tiles.append((t, '셀간 희망내용 불일치')); continue
    C = next(iter(des))
    if C == orig:
        continue                       # 무변경
    if any(v is None for v in cell_desired.values()):
        skipped_tiles.append((t, f'미편집 셀 존재({sum(1 for v in cell_desired.values() if v is None)})'))
        continue
    writes[t] = C
print(f'기록 {len(writes)}타일, 포기 {len(skipped_tiles)}타일')
from collections import Counter as C_
print(C_(r for _, r in skipped_tiles))

for t, c in writes.items():
    tiles[t*32:(t+1)*32] = c

# 재조립
gofs = info['gofs']; mofs_old = info['mofs']
comp = ndspy.lz10.compress(bytes(tiles))
out = bytearray(d[:gofs])
out += comp
while len(out) % 16: out += b'\x00'
mofs_new = len(out)
out += d[mofs_old:]
struct.pack_into('<H', out, 8, mofs_new & 0xFFFF)
new = bytes(out)
info2 = bgscm.parse(new)
assert bytes(info2['tiles']) == bytes(tiles)
h1, e1, _ = bgscm.decode_map(d[mofs_old:])
h2, e2, _ = bgscm.decode_map(new[info2['u16'][4]:])
assert h1 == h2 and e1 == e2
print(f'재조립 {len(d)}B → {len(new)}B, 왕복 일치')
open(os.path.join(WORK, 'TIT_1R.SCM.kr'), 'wb').write(new)
print('저장: TIT_1R.SCM.kr')

# 시뮬 렌더: 최종 타일로 각 상태 화면 합성 (실기 결과 미리보기)
def flipped(tb, hf, vf):
    return unflip(tb, hf, vf)  # 대칭 연산이라 동일

for k in map(str, range(1, 7)):
    idx = idxs[k]
    img = Image.new('RGB', (256, 256), (255, 0, 255))
    px = img.load()
    # 배경: 편집본(비매핑/평탄 셀 포함)
    for y in range(256):
        for x in range(256):
            v = idx[y][x]
            if v: px[x, y] = tuple(pal[v])
    # 매핑 셀은 최종 타일로 덮어씀 (실제 결과)
    for ci_s, (t, hf, vf, p) in cellmaps[k].items():
        ci = int(ci_s)
        tb = flipped(tiles[t*32:(t+1)*32], hf, vf)
        cx, cy = (ci % 32)*8, (ci // 32)*8
        for y in range(8):
            for x in range(8):
                b = tb[y*4 + x//2]
                v = (b >> 4) if (x & 1) else (b & 0xF)
                px[cx+x, cy+y] = tuple(pal[p*16+v]) if v else (255, 0, 255)
    img.transpose(Image.ROTATE_90).resize((512, 512), Image.NEAREST).save(
        os.path.join(OUT, f'final{k}.png'))
print('시뮬 렌더 저장: final1-6.png')
