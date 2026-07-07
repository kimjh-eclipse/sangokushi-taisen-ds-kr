# -*- coding: utf-8 -*-
# BTNALL.SCM 전 버튼 한글 식자 (60_btnall_kr.py 파일럿의 일반화)
#  구슬 복원: (1)상태간 변화=구슬 (2)같은팔레트 버튼간 만장일치=안정구슬 (3)글자=타 버튼 차용
#  회색(단일상태): 컬러 counterpart의 글자마스크 위치를 지워 타 회색버튼 값으로 치환
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
off, sz = files['BTNALL.SCM']
orig = sang[off:off+sz]
r = scmimg.decode(orig)
g = bytearray(r['gfx'])
pal = scmimg.pal_to_rgb(r['pal'])
info = cncp.parse(g)

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

maps = {i: index_map(i) for i in range(48)}
geoms = {i: cell_geom(i) for i in range(48)}

# ---- 버튼 구성 ----
TRIPLES = {0:(0,1,2), 3:(3,4,5), 6:(6,7,8), 9:(9,10,11), 12:(12,13,14),
           15:(15,16,17), 18:(18,19,20), 21:(21,22,23), 24:(24,25,26),
           36:(36,37,38), 40:(40,41,42), 44:(44,45,46)}
PAL_POOLS = {           # 같은 팔레트·지오메트리
    'pal0': [0, 3, 6, 36],
    'pal2': [9, 12, 15, 18],
    'pal1': [21, 40],
    'pal3': [24, 44],
}
PALNO = {0:0, 3:0, 6:0, 36:0, 9:2, 12:2, 15:2, 18:2, 21:1, 40:1, 24:3, 44:3}

def topzone(base):        # 구슬 위 순수 글자영역 경계 (구슬높이 26 고정)
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

# ---- 컬러 버튼 분석 ----
AN = {}
for palkey, pool in PAL_POOLS.items():
    for b in pool:
        orbs, text, lo = analyze(b, pool)
        AN[b] = (orbs, text)
        print(f'{palkey} cell{b}: 글자픽셀={len(text)} 잔여={lo}')

# ---- 컬러↔회색 매칭 (글자모양 자카드) ----
GRAYS40 = [27, 28, 29, 30, 31, 32, 33, 35, 39, 47]
GRAYS48 = [34, 43]
def glyph_mask(ci, tz):
    return {(x, y) for y in range(tz) for x in range(len(maps[ci][0])) if maps[ci][y][x] != 0}

BTN_GRAY = {}
for base in TRIPLES:
    tz = topzone(base)
    a = glyph_mask(base, tz)
    grays = GRAYS48 if geoms[base][3] == 48 else GRAYS40
    best, bs = None, -1
    for c4 in grays:
        b4 = glyph_mask(c4, tz)
        s = len(a & b4) / max(1, len(a | b4))
        if s > bs: best, bs = c4, s
    BTN_GRAY[base] = (best, bs)
    print(f'버튼 cell{base} ↔ 회색 cell{best} (유사도 {bs:.2f})')

def gray_clean(target_base):
    t4 = BTN_GRAY[target_base][0]
    tmask = dilate1(AN[target_base][1])
    W, H = geoms[t4][2], geoms[t4][3]
    TZ = topzone(target_base)
    m = [row[:] for row in maps[t4]]
    unk = 0
    donors = [(b, c4s[0]) for b, c4s in BTN_GRAY.items()
              if b != target_base and geoms[c4s[0]][3] == H]
    for (x, y) in tmask:
        if not (0 <= x < W and 0 <= y < H): continue
        if y < TZ:
            m[y][x] = 0
            continue
        cand = [maps[c4][y][x] for b, c4 in donors if (x, y) not in dilate1(AN[b][1])]
        if cand:
            m[y][x] = Counter(cand).most_common(1)[0][0]
        else:
            unk += 1
            near = [m[y][x-d] for d in (1,2,3) if x-d >= 0] + [m[y][x+d] for d in (1,2,3) if x+d < W]
            m[y][x] = Counter(near).most_common(1)[0][0] if near else 0
    return m, unk

# ---- 식자 목록: base -> (문자열, 폰트px) ----
TEXTS = {
    0: ('결정', 13), 3: ('결정', 13), 6: ('예', 13), 9: ('뒤로', 13),
    12: ('아니오', 11), 15: ('전환', 13), 18: ('덱편성', 11),
    21: ('이름변경', 11), 24: ('파기', 13), 36: ('교환', 13),
    40: ('계략설명', 11), 44: ('삭제', 13),
}
masks = {}
for s, px in set(TEXTS.values()):
    masks[s] = make_masks(s, px)
    print(f'마스크 "{s}"({px}px): {masks[s][2]}x{masks[s][3]}')

def place(base, s):
    W, H = masks[s][2], masks[s][3]
    CW, CH = geoms[base][2], geoms[base][3]
    x0 = 16 - W//2
    if s == '예':
        y0 = max(0, topzone(base) - H//2)
    elif len(s) <= 2:
        y0 = 1
    else:
        y0 = 0
    return x0, y0

# 컬러 식자
for base, (s, px) in TEXTS.items():
    oi, fi = text_indices(base, PALNO[base], topzone(base))
    x0, y0 = place(base, s)
    orbs, _ = AN[base]
    for st in range(3):
        canvas = typeset(orbs[st], masks[s], x0, y0, oi, fi)
        writeback(TRIPLES[base][st], canvas)
    print(f'cell{TRIPLES[base]}: "{s}" (외곽선={oi:X} 채움={fi:X} at {x0},{y0})')

# 회색 식자 (매칭 유사도 0.9 이상만)
for base, (s, px) in TEXTS.items():
    t4, sim = BTN_GRAY[base]
    if sim < 0.9:
        print(f'회색 cell{t4}: 유사도 {sim:.2f} < 0.9 → 스킵 (버튼 cell{base})')
        continue
    if t4 in [BTN_GRAY[b][0] for b in TEXTS if b != base and BTN_GRAY[b][1] > sim]:
        continue
    oi, fi = text_indices(t4, 4, topzone(base))
    x0, y0 = place(base, s)
    m, unk = gray_clean(base)
    canvas = typeset(m, masks[s], x0, y0, oi, fi)
    writeback(t4, canvas)
    print(f'회색 cell{t4}: "{s}" (잔여보간={unk})')

# ---- 미리보기 (전체 셀 시트) ----
sheet_cells = list(range(48))
cw, ch = 44, 62
cols = 8
rows_n = (len(sheet_cells)+cols-1)//cols
sheet = Image.new('RGB', (cols*cw, rows_n*ch*2), (40, 40, 40))
dr = ImageDraw.Draw(sheet)
for k, ci in enumerate(sheet_cells):
    X, Y = (k % cols)*cw, (k // cols)*ch*2
    im, _, _ = cncp.render_cell(bytes(g), info['cells'][ci], pal)
    if im: sheet.paste(im, (X+4, Y+12), im)
    dr.text((X+4, Y), str(ci), fill=(255, 255, 0))
    im0, _, _ = cncp.render_cell(r['gfx'], info['cells'][ci], pal)
    if im0: sheet.paste(im0, (X+4, Y+ch+12), im0)
sheet = sheet.resize((sheet.width*2, sheet.height*2), Image.NEAREST)
sheet.save(os.path.join(WORK, 'preview_btnall_all.png'))
print('-> preview_btnall_all.png (각 행: 위=수정, 아래=원본)')

# ---- 재인코드 ----
new_scm = scmenc.rebuild(orig, bytes(g))
open(os.path.join(WORK, 'BTNALL.SCM.kr'), 'wb').write(new_scm)
chk = scmimg.decode(new_scm)
print(f'재인코드: {len(orig)}B -> {len(new_scm)}B, 재해제일치={chk["gfx"]==bytes(g)}')
