# -*- coding: utf-8 -*-
# ED_BALL.SCM 한글 식자 — 덱편집 우하단 버튼 (61_btnall_all.py 이식)
#  셀: 0-2 決定 / 3-5 はい / 6-8 戻る / 9-11 いいえ / 12-14 計略説明(48) / 15-19 회색(決定,戻る,はい,いいえ,計略説明)
#  풀: pal0=[0,3], pal4=[6,9], pal1=[12](단독 → 평탄배경(3) 플레이트 소거 방식)
import os, sys, json
from collections import Counter
from PIL import Image, ImageFont, ImageDraw, ImageFilter
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, scmimg, cncp, scmenc

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}
off, sz = files['ED_BALL.SCM']
orig = sang[off:off+sz]
r = scmimg.decode(orig)
g = bytearray(r['gfx'])
pal = scmimg.pal_to_rgb(r['pal'])
info = cncp.parse(g)
NC = len(info['cells'])

def cell_geom(ci):
    cell = info['cells'][ci]
    xs, ys, x1, y1 = 999, 999, -999, -999
    for a0, a1, a2 in cell['oams']:
        shape=(a0>>14)&3; size=(a1>>14)&3
        w,h = cncp.OBJ_SIZES[(shape,size)]
        x = cncp.sgn(a1&0x1FF,9); y = cncp.sgn(a0&0xFF,8)
        xs=min(xs,x); ys=min(ys,y); x1=max(x1,x+w); y1=max(y1,y+h)
    return xs, ys, x1-xs, y1-ys

def index_map(ci):
    xs, ys, W, H = cell_geom(ci)
    cell = info['cells'][ci]
    m = [[0]*W for _ in range(H)]
    for a0, a1, a2 in cell['oams']:
        shape=(a0>>14)&3; size=(a1>>14)&3
        w,h = cncp.OBJ_SIZES[(shape,size)]
        x = cncp.sgn(a1&0x1FF,9)-xs; y = cncp.sgn(a0&0xFF,8)-ys
        tile = a2 & 0x3FF
        for ty in range(h//8):
            for tx in range(w//8):
                tofs = cell['gfxBase'] + (tile+ty*(w//8)+tx)*32
                for yy in range(8):
                    for xx in range(8):
                        b = g[tofs+yy*4+xx//2]
                        m[y+ty*8+yy][x+tx*8+xx] = (b>>4) if (xx&1) else (b&0xF)
    return m

def writeback(ci, canvas):
    xs, ys, W, H = cell_geom(ci)
    cell = info['cells'][ci]
    for a0, a1, a2 in cell['oams']:
        shape=(a0>>14)&3; size=(a1>>14)&3
        w,h = cncp.OBJ_SIZES[(shape,size)]
        x = cncp.sgn(a1&0x1FF,9)-xs; y = cncp.sgn(a0&0xFF,8)-ys
        tile = a2 & 0x3FF
        for ty in range(h//8):
            for tx in range(w//8):
                tofs = cell['gfxBase'] + (tile+ty*(w//8)+tx)*32
                for yy in range(8):
                    for xx in range(0, 8, 2):
                        lo = canvas[y+ty*8+yy][x+tx*8+xx] & 0xF
                        hi = canvas[y+ty*8+yy][x+tx*8+xx+1] & 0xF
                        g[tofs+yy*4+xx//2] = lo | (hi<<4)

maps = {i: index_map(i) for i in range(NC)}
geoms = {i: cell_geom(i) for i in range(NC)}

TRIPLES = {0:(0,1,2), 3:(3,4,5), 6:(6,7,8), 9:(9,10,11), 12:(12,13,14)}
PAL_POOLS = {'pal0': [0, 3], 'pal4': [6, 9]}
PALNO = {0:0, 3:0, 6:4, 9:4, 12:1}
GRAY_OF = {0:15, 6:16, 3:17, 9:18, 12:19}   # 렌더 육안 확인: 15=決定,16=戻る,17=はい,18=いいえ,19=計略説明
GRAY_PAL = 3

def topzone(base):
    return geoms[base][3] - 26

def analyze(base, pool):
    tri = TRIPLES[base]
    others = [b for b in pool if b != base]
    W, H = geoms[base][2], geoms[base][3]
    TZ = topzone(base)
    orbs = [[[0]*W for _ in range(H)] for _ in range(3)]
    text = set()
    leftover = []
    for y in range(TZ, H):
        for x in range(W):
            vals = [maps[c][y][x] for c in tri]
            if len(set(vals)) > 1:
                for s in range(3): orbs[s][y][x] = vals[s]
                continue
            uni = [maps[TRIPLES[b][0]][y][x] for b in pool]
            if len(set(uni)) == 1:
                for s in range(3): orbs[s][y][x] = maps[TRIPLES[base][s]][y][x]
                continue
            text.add((x, y))
            got = False
            for s in range(3):
                cand = []
                for b in others:
                    bv = [maps[c][y][x] for c in TRIPLES[b]]
                    if len(set(bv)) > 1:
                        cand.append(bv[s])
                if cand:
                    orbs[s][y][x] = Counter(cand).most_common(1)[0][0]
                    got = True
            if not got:
                leftover.append((x, y))
    for (x, y) in leftover:
        for s in range(3):
            cand = [maps[TRIPLES[b][s]][y][x] for b in others]
            orbs[s][y][x] = Counter(cand).most_common(1)[0][0]
    for y in range(TZ):
        for x in range(W):
            if maps[base][y][x]: text.add((x, y))
    return orbs, text, len(leftover)

def luma(c): return 0.299*c[0]+0.587*c[1]+0.114*c[2]

def text_indices(ci, palno, tz):
    cnt = Counter(v for y in range(2, tz) for v in maps[ci][y] if v > 0)
    cand = [v for v, n in cnt.items() if n >= 4]
    o = min(cand, key=lambda v: luma(pal[palno*16+v]))
    f = max(cand, key=lambda v: luma(pal[palno*16+v]))
    return o, f

def make_masks(s, px):
    font = ImageFont.truetype(r'C:\Windows\Fonts\gulim.ttc', px)
    img = Image.new('L', (px*len(s)*2+8, px*2+8), 0)
    ImageDraw.Draw(img).text((4, 4), s, fill=255, font=font)
    img = img.point(lambda v: 255 if v >= 128 else 0)
    img = img.crop(img.getbbox()).transpose(Image.ROTATE_270)
    dil = img.filter(ImageFilter.MaxFilter(3))
    W, H = img.size
    fill = {(x, y) for y in range(H) for x in range(W) if img.getpixel((x, y))}
    outl = {(x, y) for y in range(H) for x in range(W)
            if dil.getpixel((x, y)) and (x, y) not in fill}
    return fill, outl, W, H

def make_masks_scaled(s, target_h, max_w):
    """긴 라벨용: 32px 렌더 → LANCZOS 축소 (계략설명 4자를 36px 높이에)"""
    font = ImageFont.truetype(r'C:\Windows\Fonts\gulim.ttc', 32)
    img = Image.new('L', (32*len(s)*2+16, 96), 0)
    dr = ImageDraw.Draw(img)
    dr.text((8, 8), s, fill=255, font=font)
    dr.text((9, 8), s, fill=255, font=font)
    img = img.crop(img.getbbox())
    w0, h0 = img.size
    nw = min(max_w, max(1, round(w0 * target_h / h0)))
    img = img.resize((nw, target_h), Image.LANCZOS)
    img = img.point(lambda v: 255 if v >= 118 else 0)
    img = img.transpose(Image.ROTATE_270)
    W, H = img.size
    fill = {(x, y) for y in range(H) for x in range(W) if img.getpixel((x, y))}
    return fill, set(), W, H

def typeset(base_canvas, mask, x0, y0, oi, fi):
    fill, outl, W, H = mask
    CH, CW = len(base_canvas), len(base_canvas[0])
    canvas = [row[:] for row in base_canvas]
    for (x, y) in outl:
        X, Y = x0+x, y0+y
        if 0 <= X < CW and 0 <= Y < CH: canvas[Y][X] = oi
    for (x, y) in fill:
        X, Y = x0+x, y0+y
        if 0 <= X < CW and 0 <= Y < CH: canvas[Y][X] = fi
    return canvas

def dilate1(mask):
    return {(x+dx, y+dy) for (x, y) in mask for dx in (-1,0,1) for dy in (-1,0,1)}

# ---- 컬러 분석 (2버튼 풀) ----
AN = {}
for palkey, pool in PAL_POOLS.items():
    for b in pool:
        orbs, text, lo = analyze(b, pool)
        AN[b] = (orbs, text)
        print(f'{palkey} cell{b}: 글자픽셀={len(text)} 잔여={lo}')

TEXTS = {0: ('결정', 13), 3: ('예', 13), 6: ('뒤로', 13), 9: ('아니오', 11)}
masks = {}
for s, px in set(TEXTS.values()):
    masks[s] = make_masks(s, px)

def place(base, s):
    W, H = masks[s][2], masks[s][3]
    x0 = 16 - W//2
    if s == '예':
        y0 = max(0, topzone(base) - H//2)
    else:
        y0 = 1 if len(s) <= 2 else 0
    return x0, y0

for base, (s, px) in TEXTS.items():
    oi, fi = text_indices(base, PALNO[base], topzone(base))
    x0, y0 = place(base, s)
    orbs, _ = AN[base]
    for st in range(3):
        canvas = typeset(orbs[st], masks[s], x0, y0, oi, fi)
        writeback(TRIPLES[base][st], canvas)
    print(f'cell{TRIPLES[base]}: "{s}" (외곽={oi:X} 채움={fi:X} @{x0},{y0})')

# ---- 計略説明 (셀 12-14): 평탄배경(3) 플레이트 소거 + 상태변화 구슬 보존 ----
def plate_clean_and_typeset(cells, palno, label):
    tri_maps = [maps[c] for c in cells]
    H, W = len(tri_maps[0]), len(tri_maps[0][0])
    oi, fi = text_indices(cells[0], palno, 26)
    mk = make_masks_scaled(label, 14, 36)
    fill, outl, mw, mh = mk
    x0 = 8 + (17 - mw)//2   # 플레이트 내부 x8-24 중앙
    y0 = max(0, (37 - mh)//2)
    print(f'{label}: 마스크 {mw}x{mh} @{x0},{y0} (외곽={oi:X} 채움={fi:X})')
    for si, c in enumerate(cells):
        canvas = [row[:] for row in tri_maps[si]]
        for y in range(0, 37):
            for x in range(9, 25):
                vals = {tm[y][x] for tm in tri_maps}
                if len(vals) == 1 and canvas[y][x] != 0:
                    canvas[y][x] = 3          # 플레이트 배경 평탄 인덱스
        canvas = typeset(canvas, mk, x0, y0, oi, fi)
        writeback(c, canvas)
    return mk, x0, y0

mk12, x12, y12 = plate_clean_and_typeset([12, 13, 14], PALNO[12], '계략설명')

# ---- 회색 셀 (15-19): 대응 컬러의 글자마스크 위치 소거 후 식자 ----
# 40-tall 회색(15-18): 서로를 도너로 상호 복원 / 48-tall(19): 플레이트 소거
def gray_clean40(target_base, t4):
    tmask = dilate1(AN[target_base][1])
    W, H = geoms[t4][2], geoms[t4][3]
    TZ = topzone(target_base)
    m = [row[:] for row in maps[t4]]
    donors = [g4 for b, g4 in GRAY_OF.items()
              if g4 != t4 and geoms[g4][3] == H]
    unk = 0
    for (x, y) in tmask:
        if not (0 <= x < W and 0 <= y < H): continue
        if y < TZ:
            m[y][x] = 0
            continue
        cand = [maps[g4][y][x] for b, g4 in GRAY_OF.items()
                if g4 != t4 and geoms[g4][3] == H and (x, y) not in dilate1(AN[b][1])]
        if cand:
            m[y][x] = Counter(cand).most_common(1)[0][0]
        else:
            unk += 1
            near = [m[y][x-dd] for dd in (1,2,3) if x-dd >= 0] + \
                   [m[y][x+dd] for dd in (1,2,3) if x+dd < W]
            m[y][x] = Counter(near).most_common(1)[0][0] if near else 0
    return m, unk

for base, (s, px) in TEXTS.items():
    t4 = GRAY_OF[base]
    m, unk = gray_clean40(base, t4)
    cnt = Counter(v for y in range(2, topzone(base)) for v in maps[t4][y] if v > 0)
    cand = [v for v, n in cnt.items() if n >= 4]
    oi = min(cand, key=lambda v: luma(pal[GRAY_PAL*16+v]))
    fi = max(cand, key=lambda v: luma(pal[GRAY_PAL*16+v]))
    x0, y0 = place(base, s)
    canvas = typeset(m, masks[s], x0, y0, oi, fi)
    writeback(t4, canvas)
    print(f'회색 cell{t4}: "{s}" (잔여보간={unk})')

# 회색 계략설명 (19): 플레이트 소거 (배경 인덱스 확인 후 3 가정)
m19 = maps[19]
cnt = Counter(v for y in range(2, 26) for v in m19[y] if v > 0)
cand = [v for v, n in cnt.items() if n >= 4]
oi19 = min(cand, key=lambda v: luma(pal[GRAY_PAL*16+v]))
fi19 = max(cand, key=lambda v: luma(pal[GRAY_PAL*16+v]))
bg19 = Counter(m19[y][x] for y in range(0, 37) for x in range(9, 25) if m19[y][x]).most_common(1)[0][0]
canvas = [row[:] for row in m19]
for y in range(0, 37):
    for x in range(9, 25):
        if canvas[y][x] != 0:
            canvas[y][x] = bg19
canvas = typeset(canvas, mk12, x12, y12, oi19, fi19)
writeback(19, canvas)
print(f'회색 cell19: "계략설명" (bg={bg19:X} 외곽={oi19:X} 채움={fi19:X})')

# ---- 미리보기 ----
cw, ch = 44, 62
cols = 5
rows_n = (NC + cols - 1)//cols
sheet = Image.new('RGB', (cols*cw, rows_n*ch*2), (40, 40, 40))
dr = ImageDraw.Draw(sheet)
for k in range(NC):
    X, Y = (k % cols)*cw, (k // cols)*ch*2
    im, _, _ = cncp.render_cell(bytes(g), info['cells'][k], pal)
    if im: sheet.paste(im, (X+4, Y+12), im)
    dr.text((X+4, Y), str(k), fill=(255, 255, 0))
    im0, _, _ = cncp.render_cell(r['gfx'], info['cells'][k], pal)
    if im0: sheet.paste(im0, (X+4, Y+ch+12), im0)
sheet = sheet.resize((sheet.width*2, sheet.height*2), Image.NEAREST)
sheet.save(os.path.join(WORK, 'preview_edball.png'))
print('-> preview_edball.png (위=수정, 아래=원본)')

# ---- 재인코드 ----
new_scm = scmenc.rebuild(orig, bytes(g))
open(os.path.join(WORK, 'ED_BALL.SCM.kr'), 'wb').write(new_scm)
chk = scmimg.decode(new_scm)
print(f'재인코드: {len(orig)}B -> {len(new_scm)}B, 재해제일치={chk["gfx"]==bytes(g)}')
