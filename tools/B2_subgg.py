# -*- coding: utf-8 -*-
# 군의 서브메뉴 배너(GG_TUB.SCM) 한글화 — 통합 파이프라인 (추출→편집→기록)
#  상태: slot1=무선택, 2=덱편성팝, 3=군주설정팝, 4=카드도감팝, 5=전기도감팝
import sys, os, json, zlib, struct
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, ndspy.lz10, bgscm
from PIL import Image, ImageFont, ImageDraw, ImageFilter

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
OUT = os.path.join(WORK, 'banner')
LCDM = 0x080f6d0 + 12
VMEM = 0x080e6b8 + 12
TILES_OFF = LCDM + 0x40000 + 0x10000
SRC_NAME = 'GG_TUB.SCM'
STATES = {k: rf'C:\Emul\Desmume\StateSlots\San Goku Shi Taisen (K).ds{k}' for k in range(1, 6)}
REST = [('군주설정', 68, 102), ('덱편성', 108, 142), ('전기도감', 148, 182), ('카드도감', 188, 222)]
POP = {2: ('덱편성', 104, 146), 3: ('군주설정', 64, 106),
       4: ('카드도감', 184, 226), 5: ('전기도감', 144, 186)}
TXT_REST = {49, 50, 51, 54}   # 모드선택과 동일 구성 가정 → 검증 후 조정

rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}
off, sz = files[SRC_NAME]
d0 = sang[off:off+sz]
info0 = bgscm.parse(d0)
SRC = bytes(info0['tiles'])
NT = info0['ntiles']

def flip4(tb, hf, vf):
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

LUT = {}
for t in range(NT):
    tb = SRC[t*32:(t+1)*32]
    for hf in (0, 1):
        for vf in (0, 1):
            LUT.setdefault(flip4(tb, hf, vf), (t, hf, vf))

def extract(path):
    raw = zlib.decompress(open(path, 'rb').read()[0x20:])
    pal = []
    for i in range(256):
        v, = struct.unpack_from('<H', raw, VMEM + 0x400 + i*2)
        pal.append(((v&31)<<3, ((v>>5)&31)<<3, ((v>>10)&31)<<3))
    idx = [[0]*256 for _ in range(256)]
    cm = {}
    for i in range(1024):
        tb8 = raw[TILES_OFF + i*64: TILES_OFF + (i+1)*64]
        cx, cy = (i % 32)*8, (i // 32)*8
        for y in range(8):
            for x in range(8):
                idx[cy+y][cx+x] = tb8[y*8+x]
        if len(set(tb8)) == 1: continue
        b4 = bytearray(32)
        for k in range(0, 64, 2):
            b4[k//2] = (tb8[k] & 0xF) | ((tb8[k+1] & 0xF) << 4)
        hit = LUT.get(bytes(b4))
        if hit: cm[i] = hit
    return pal, idx, cm

print('=== 추출 ===')
pals, idxs, cms = {}, {}, {}
for k, p in STATES.items():
    pal, idx, cm = extract(p)
    pals[k], idxs[k], cms[k] = pal, idx, cm
    unmatched = sum(1 for i in range(1024)
                    if len({idxs[k][(i//32)*8+y][(i%32)*8+x] for y in range(8) for x in range(8)}) > 1
                    and i not in cm)
    print(f'state{k}: 매핑 {len(cm)}셀, 미매칭 {unmatched}')

def luma(c): return 0.299*c[0]+0.587*c[1]+0.114*c[2]

# 편집가능 셀: 타일이 전 상태에서 단일 셀 위치에만 등장
from collections import defaultdict as _dd
_occ = _dd(set)
for _k in STATES:
    for _ci, (_t, _hf, _vf) in cms[_k].items():
        _occ[_t].add(_ci)
EDITABLE = {k: {ci for ci, (t, hf, vf) in cms[k].items() if _occ[t] == {ci}} for k in STATES}
for k in STATES:
    print(f'state{k}: 편집가능 {len(EDITABLE[k])}/{len(cms[k])}')

def mask_h(s, px, bold=True, thr=128):
    font = ImageFont.truetype(r'C:\Windows\Fonts\gulim.ttc', px)
    img = Image.new('L', (px*len(s)*2+12, px*3), 0)
    dr = ImageDraw.Draw(img)
    dr.text((6, 6), s, fill=255, font=font)
    if bold: dr.text((7, 6), s, fill=255, font=font)
    img = img.point(lambda v: 255 if v >= thr else 0)
    img = img.crop(img.getbbox()).transpose(Image.ROTATE_270)
    dil = img.filter(ImageFilter.MaxFilter(3))
    W, H = img.size
    fill = {(x, y) for y in range(H) for x in range(W) if img.getpixel((x, y))}
    outl = {(x, y) for y in range(H) for x in range(W)
            if dil.getpixel((x, y)) and (x, y) not in fill}
    return fill, outl, W, H

print('=== 편집 ===')
changed = {k: set() for k in STATES}
# rest (state1): 어두운 텍스트 → 열별 배경, 12px
pal1 = pals[1]
idx1 = idxs[1]
for label, x0, x1 in REST:
    ys_nz = [y for y in range(256) if any(idx1[y][x] for x in range(x0, x1))]
    cap_end = min(ys_nz) + 14          # 캡 장식 보호
    tpix = [(x, y) for y in range(cap_end, 256) for x in range(x0+5, x1-5)
            if idx1[y][x] and luma(pal1[idx1[y][x]]) < 150 and (idx1[y][x] >> 4) == 3]
    if not tpix:
        print(f'rest {label}: 어두운 텍스트 없음 — 인덱스 구성 확인 필요'); continue
    ys = sorted(p[1] for p in tpix)
    ts0, ts1 = ys[0], ys[-1]
    tvals = Counter(idx1[y][x] for (x, y) in tpix)   # 소거 전 원문 텍스트 색
    colbg = {}
    for x in range(x0, x1):
        cnt = Counter(idx1[y][x] for y in range(256)
                      if idx1[y][x] and luma(pal1[idx1[y][x]]) >= 150)
        if cnt: colbg[x] = cnt.most_common(1)[0][0]
    for y in range(max(ts0, cap_end), ts1+1):
        for x in range(x0+5, x1-5):
            v = idx1[y][x]
            if v and luma(pal1[v]) < 150 and x in colbg:
                idx1[y][x] = colbg[x]
                changed[1].add((y//8)*32 + x//8)
    # 원문 글자 클러스터 → 글자별 슬롯
    rows = sorted({y for (x, y) in tpix})
    clusters = []
    for y in rows:
        if clusters and y - clusters[-1][1] <= 3: clusters[-1][1] = y
        else: clusters.append([y, y])
    fi = tvals.most_common(1)[0][0]
    chars = [c for c in label if c != ' ']
    n = len(chars)
    work = list(clusters)
    rowpix = Counter(y for (x, y) in tpix)
    def weight(cl):
        return sum(rowpix.get(y, 0) for y in range(cl[0], cl[1]+1))
    while len(work) > n:
        # 픽셀수 최소 클러스터 제거 (ー 등 세선 글자)
        ws = [weight(c) for c in work]
        med = sorted(ws)[len(ws)//2]
        thin = min(range(len(work)), key=lambda i: ws[i])
        if ws[thin] <= med * 0.4:
            work.pop(thin)
        else:
            break
    if len(work) == n:
        slots = [(a+b)//2 for a, b in work]
    else:
        c0 = (work[0][0]+work[0][1])//2
        c1 = (work[-1][0]+work[-1][1])//2
        slots = [c0 + int(i*(c1-c0)/max(1, n-1)) for i in range(n)]
    body = sorted(colbg)
    bx0, bx1 = body[0], body[-1]
    for i, chs in enumerate(chars):
        f1, o1, mw, mh = mask_h(chs, 12, bold=True)
        px0 = bx0 + (bx1 - bx0 + 1 - mw)//2
        py0 = max(cap_end, slots[i] - mh//2)
        for (x, y) in f1:
            X, Y = px0 + x, py0 + y
            if 0 <= X < 256 and 0 <= Y < 256 and idx1[Y][X] and luma(pal1[idx1[Y][X]]) >= 150:
                idx1[Y][X] = fi
                changed[1].add((Y//8)*32 + X//8)
    print(f'rest {label}: 클러스터{len(clusters)} 슬롯{slots} 채움={fi:#x}')

# popped (state2-5): 흰 텍스트, colbg 복원, 글자별 슬롯
for k, (label, x0, x1) in POP.items():
    palk, idxk = pals[k], idxs[k]
    ys_nz = [y for y in range(256) if any(idxk[y][x] for x in range(x0, x1))]
    yb0, yb1 = min(ys_nz), max(ys_nz)
    xs_nz = [x for x in range(x0, x1) if any(idxk[y][x] for y in range(yb0, yb1+1))]
    bx0, bx1 = min(xs_nz), max(xs_nz)
    colbg = {}
    for x in range(bx0, bx1+1):
        cnt = Counter(idxk[y][x] for y in range(yb0, yb1+1) if idxk[y][x])
        colbg[x] = cnt.most_common(1)[0][0] if cnt else 0
    ty0, ty1 = yb0 + 13, yb1 - 7
    wrow = [y for y in range(ty0, ty1+1)
            if sum(1 for x in range(bx0, bx1+1)
                   if idxk[y][x] and luma(palk[idxk[y][x]]) >= 225) >= 2]
    if not wrow:
        print(f'pop {label}: 흰 텍스트 없음'); continue
    clusters = []
    for y in wrow:
        if clusters and y - clusters[-1][1] <= 4: clusters[-1][1] = y
        else: clusters.append([y, y])
    ts0, ts1 = wrow[0], wrow[-1]
    for y in range(max(ty0, ts0-3), min(ty1, ts1+3)+1):
        for x in range(bx0, bx1+1):
            if idxk[y][x] and colbg[x] and idxk[y][x] != colbg[x]:
                idxk[y][x] = colbg[x]
                changed[k].add((y//8)*32 + x//8)
    # 흰/어두운 인덱스 (팔레트행 3 가정 아님 — 실제 밴드 행에서)
    prow = Counter(v >> 4 for x in range(bx0, bx1+1) for v in (colbg[x],) if v).most_common(1)[0][0]
    whites = [v for v in range(prow*16, prow*16+16) if luma(palk[v]) >= 225]
    darks = [v for v in range(prow*16, prow*16+16) if luma(palk[v]) < 90]
    wi = whites[0] if whites else prow*16+15
    di = min(darks, key=lambda v: luma(palk[v])) if darks else prow*16+1
    chars = [c for c in label if c != ' ']
    n = len(chars)
    wcount = {}
    for y in wrow:
        wcount[y] = sum(1 for x in range(bx0, bx1+1)
                        if idxk[y][x] and luma(palk[idxk[y][x]]) >= 225)
    work = list(clusters)
    def wgt(cl):
        return sum(wcount.get(y, 0) for y in range(cl[0], cl[1]+1))
    while len(work) > n:
        ws = [wgt(c) for c in work]
        med = sorted(ws)[len(ws)//2]
        thin = min(range(len(work)), key=lambda i: ws[i])
        if ws[thin] <= med * 0.4:
            work.pop(thin)
        else:
            break
    if len(work) == n:
        slots = [(a+b)//2 for a, b in work]
    else:
        c0 = (work[0][0]+work[0][1])//2
        c1 = (work[-1][0]+work[-1][1])//2
        slots = [c0 + int(i*(c1-c0)/max(1, n-1)) for i in range(n)]
    body = [x for x in range(bx0, bx1+1) if colbg[x] and luma(palk[colbg[x]]) < 225]
    ix0, ix1 = min(body), max(body)
    for i, chs in enumerate(chars):
        fill, outl, mw, mh = mask_h(chs, 16, bold=True)
        py0 = max(ty0, slots[i] - mh//2)
        px0 = ix0 + (ix1 - ix0 + 1 - mw)//2
        clip = 0
        for pts, col in ((outl, di), (fill, wi)):
            for (x, y) in pts:
                X, Y = px0 + x, py0 + y
                if ix0 <= X <= ix1 and ty0 <= Y <= ty1:
                    ci = (Y//8)*32 + X//8
                    if ci not in EDITABLE[k]:
                        clip += 1; continue
                    idxk[Y][X] = col
                    changed[k].add(ci)
    print(f'pop {label}: 스팬 y{ts0}-{ts1} 흰={wi:#x} 암={di:#x} 클러스터{len(clusters)}')

# 렌더 미리보기
for k in STATES:
    img = Image.new('RGB', (256, 256), (255, 0, 255))
    px = img.load()
    for y in range(256):
        for x in range(256):
            v = idxs[k][y][x]
            if v: px[x, y] = tuple(pals[k][v])
    img.transpose(Image.ROTATE_90).resize((512,512), Image.NEAREST).save(
        os.path.join(OUT, f'gg_edit{k}.png'))

print('=== 기록 ===')
def cell4(idx, ci):
    cx, cy = (ci % 32)*8, (ci // 32)*8
    out = bytearray(32)
    for y in range(8):
        for x in range(0, 8, 2):
            out[y*4+x//2] = (idx[cy+y][cx+x] & 0xF) | ((idx[cy+y][cx+x+1] & 0xF) << 4)
    return bytes(out)

tiles = bytearray(SRC)
tinfo = defaultdict(lambda: defaultdict(list))
for k in STATES:
    for ci, (t, hf, vf) in cms[k].items():
        content = flip4(cell4(idxs[k], ci), hf, vf)
        tinfo[t][ci].append((k, content, ci in changed[k]))
writes = {}
skipped = []
for t, bycell in tinfo.items():
    orig = bytes(tiles[t*32:(t+1)*32])
    des = {}
    ok = True
    for ci, lst in bycell.items():
        ed = [c for (k, c, e) in lst if e]
        if ed:
            if len(set(ed)) > 1: ok = False; break
            des[ci] = ed[0]
        else:
            des[ci] = None
    if not ok:
        skipped.append((t, '상태간 불일치')); continue
    vals = {c for c in des.values() if c is not None}
    if not vals: continue
    if len(vals) > 1:
        skipped.append((t, '셀간 불일치')); continue
    C = next(iter(vals))
    if C == orig: continue
    if any(v is None for v in des.values()):
        skipped.append((t, f'미편집셀 {sum(1 for v in des.values() if v is None)}')); continue
    writes[t] = C
print(f'기록 {len(writes)}, 포기 {len(skipped)}: {Counter(r for _, r in skipped)}')
for t, c in writes.items():
    tiles[t*32:(t+1)*32] = c
gofs = info0['gofs']; mofs = info0['mofs']
comp = ndspy.lz10.compress(bytes(tiles))
out = bytearray(d0[:gofs])
out += comp
while len(out) % 16: out += bytes(1)
mnew = len(out)
out += d0[mofs:]
struct.pack_into('<H', out, 8, mnew & 0xFFFF)
new = bytes(out)
i2 = bgscm.parse(new)
assert bytes(i2['tiles']) == bytes(tiles)
open(os.path.join(WORK, 'GG_TUB.SCM.kr'), 'wb').write(new)
print(f'저장: GG_TUB.SCM.kr ({len(d0)}→{len(new)}B)')
# 최종 시뮬
for k in STATES:
    img = Image.new('RGB', (256, 256), (255, 0, 255))
    px = img.load()
    for y in range(256):
        for x in range(256):
            v = idxs[k][y][x]
            if v: px[x, y] = tuple(pals[k][v])
    for ci, (t, hf, vf) in cms[k].items():
        tb = flip4(tiles[t*32:(t+1)*32], hf, vf)
        cx, cy = (ci % 32)*8, (ci // 32)*8
        prow_guess = None
        for y in range(8):
            for x in range(8):
                b = tb[y*4 + x//2]
                v = (b >> 4) if (x & 1) else (b & 0xF)
                ov = idxs[k][cy+y][cx+x]
                prow = (ov >> 4) if ov else 3
                px[cx+x, cy+y] = tuple(pals[k][prow*16+v]) if v else (255, 0, 255)
    img.transpose(Image.ROTATE_90).resize((512,512), Image.NEAREST).save(
        os.path.join(OUT, f'gg_final{k}.png'))
print('시뮬 저장: gg_final1-5.png')
