# -*- coding: utf-8 -*-
# DCHOOSE.SCM(덱 선택 화면 버튼) 한글 식자
#  결정(0-2,p4) 덱편집(3-5,p5) 이름변경(6-8,p3,32x64) 파기(9-11,p2) + 회색 12/13/14/15(p0)
#  버튼간 구슬 인덱스 비공유 → 상태변화(확실한 구슬) + 상태불변 픽셀은 글자로 보고 지움
#  (지움값: 같은 행의 상태변화 픽셀에서 국소 인페인트; 대부분 새 한글이 덮음)
#  회색: 컬러 글자마스크 위치 + 회색끼리 상호 차용(회색 구슬은 p0 공유 가정→검증)
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
off, sz = files['DCHOOSE.SCM']
orig = sang[off:off+sz]
r = scmimg.decode(orig)
g = bytearray(r['gfx'])
pal = scmimg.pal_to_rgb(r['pal'])
info = cncp.parse(g)

def cell_geom(ci):
    c = info['cells'][ci]
    xs=ys=999; x1=y1=-999
    for a0,a1,a2 in c['oams']:
        sh=(a0>>14)&3; szv=(a1>>14)&3
        w,h = cncp.OBJ_SIZES[(sh,szv)]
        x=cncp.sgn(a1&0x1FF,9); y=cncp.sgn(a0&0xFF,8)
        xs=min(xs,x); ys=min(ys,y); x1=max(x1,x+w); y1=max(y1,y+h)
    return xs,ys,x1-xs,y1-ys

def index_map(ci):
    xs,ys,W,H = cell_geom(ci)
    c = info['cells'][ci]
    m=[[0]*W for _ in range(H)]
    for a0,a1,a2 in c['oams']:
        sh=(a0>>14)&3; szv=(a1>>14)&3
        w,h = cncp.OBJ_SIZES[(sh,szv)]
        x=cncp.sgn(a1&0x1FF,9)-xs; y=cncp.sgn(a0&0xFF,8)-ys
        t=a2&0x3FF
        for ty in range(h//8):
            for tx in range(w//8):
                tofs = c['gfxBase'] + (t+ty*(w//8)+tx)*32
                for yy in range(8):
                    for xx in range(8):
                        b=g[tofs+yy*4+xx//2]
                        m[y+ty*8+yy][x+tx*8+xx]=(b>>4) if (xx&1) else (b&0xF)
    return m

def writeback(ci, canvas):
    xs,ys,W,H = cell_geom(ci)
    c = info['cells'][ci]
    for a0,a1,a2 in c['oams']:
        sh=(a0>>14)&3; szv=(a1>>14)&3
        w,h = cncp.OBJ_SIZES[(sh,szv)]
        x=cncp.sgn(a1&0x1FF,9)-xs; y=cncp.sgn(a0&0xFF,8)-ys
        t=a2&0x3FF
        for ty in range(h//8):
            for tx in range(w//8):
                tofs = c['gfxBase'] + (t+ty*(w//8)+tx)*32
                for yy in range(8):
                    for xx in range(0,8,2):
                        lo = canvas[y+ty*8+yy][x+tx*8+xx]&0xF
                        hi = canvas[y+ty*8+yy][x+tx*8+xx+1]&0xF
                        g[tofs+yy*4+xx//2] = lo|(hi<<4)

maps = {i: index_map(i) for i in range(16)}
geoms = {i: cell_geom(i) for i in range(16)}

def luma(c): return 0.299*c[0]+0.587*c[1]+0.114*c[2]

# ---- 회색 오라클: 12/13/15 (48px, 동일 구슬) 다수결 ----
def gray_orb48():
    m = [[0]*32 for _ in range(48)]
    for y in range(48):
        for x in range(32):
            c = Counter(maps[i][y][x] for i in (12, 13, 15))
            v, n = c.most_common(1)[0]
            m[y][x] = v if n >= 2 else -1
    for y in range(48):
        for x in range(32):
            if m[y][x] == -1:
                for dd in range(1, 32):
                    if x-dd >= 0 and m[y][x-dd] not in (-1,): m[y][x] = m[y][x-dd]; break
                    if x+dd < 32 and m[y][x+dd] not in (-1,): m[y][x] = m[y][x+dd]; break
    return m

ORB4 = gray_orb48()

def dilate1(mask):
    return {(x+dx, y+dy) for (x, y) in mask for dx in (-1,0,1) for dy in (-1,0,1)}

def gray_tmask(g4):
    """회색 셀 글자마스크 (셀 자체 좌표계). 48px 셀은 ORB4 직접, 56px(cell14)는 시프트 매핑"""
    W, H = geoms[g4][2], geoms[g4][3]
    TZ = H - 26
    dy = H - 48    # 하단(구슬) 정렬
    dx = geoms[12][0] - geoms[g4][0]   # 화면좌표 정렬 (기준: cell12 원점)
    m = set()
    for y in range(H):
        for x in range(W):
            v = maps[g4][y][x]
            if y < TZ:
                if v: m.add((x, y))
            else:
                oy, ox = y - dy, x - dx
                ov = ORB4[oy][ox] if (0 <= oy < 48 and 0 <= ox < 32) else 0
                if v != ov: m.add((x, y))
    return dilate1(m)

def orb_at(g4, x, y):
    """회색 구슬값 (셀 좌표 → ORB4 좌표)"""
    W, H = geoms[g4][2], geoms[g4][3]
    dy = H - 48
    dx = geoms[12][0] - geoms[g4][0]
    oy, ox = y - dy, x - dx
    return ORB4[oy][ox] if (0 <= oy < 48 and 0 <= ox < 32) else 0

def analyze(tri, g4):
    """컬러 3상태: 글자마스크 = 회색 counterpart(모양 동일) 시프트. 지움: 행<TZ→0, 이후 행내 인페인트"""
    W, H = geoms[tri[0]][2], geoms[tri[0]][3]
    TZ = H - 26
    # 회색 마스크 → 컬러 셀 좌표 (화면좌표 기준 시프트)
    sx = geoms[g4][0] - geoms[tri[0]][0]
    sy = geoms[g4][1] - geoms[tri[0]][1]
    text = {(x+sx, y+sy) for (x, y) in gray_tmask(g4)
            if 0 <= x+sx < W and 0 <= y+sy < H}
    orbs = []
    for s in range(3):
        m = [row[:] for row in maps[tri[s]]]
        for (x, y) in sorted(text):
            if y < TZ:
                m[y][x] = 0
        for (x, y) in sorted(text):
            if y >= TZ:
                v = 0
                for dd in range(1, W):
                    if x-dd >= 0 and (x-dd, y) not in text and m[y][x-dd]: v = m[y][x-dd]; break
                    if x+dd < W and (x+dd, y) not in text and m[y][x+dd]: v = m[y][x+dd]; break
                m[y][x] = v
        orbs.append(m)
    return orbs, text

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

BUTTONS = {   # base: (문자열, px, palno, gray셀)
    0: ('결정', 13, 4, 12),
    3: ('덱편집', 11, 5, 13),
    6: ('이름변경', 11, 3, 14),
    9: ('파기', 13, 2, 15),
}
masks = {s: make_masks(s, px) for s, px, _, _ in BUTTONS.values()}

AN = {}
for base, (s, px, palno, g4) in BUTTONS.items():
    tri = (base, base+1, base+2)
    orbs, text = analyze(tri, g4)
    AN[base] = (orbs, text)
    W, H = geoms[base][2], geoms[base][3]
    TZ = H - 26
    oi, fi = text_indices(base, palno, TZ)
    fillW, fillH = masks[s][2], masks[s][3]
    x0 = 16 - fillW//2
    y0 = 1 if len(s) <= 2 else 0
    for st in range(3):
        canvas = typeset(orbs[st], masks[s], x0, y0, oi, fi)
        writeback(tri[st], canvas)
    print(f'cell{tri}: "{s}" 글자픽셀={len(text)} (외곽={oi:X} 채움={fi:X})')

# ---- 회색: 자기 글자마스크 지우고 회색 구슬값으로 복원 ----
GRAYS = {12: 0, 13: 3, 14: 6, 15: 9}   # gray -> colored base
for g4, base in GRAYS.items():
    s, px, palno, _ = BUTTONS[base]
    Wc, Hc = geoms[g4][2], geoms[g4][3]
    TZ = Hc - 26
    m = [row[:] for row in maps[g4]]
    for (x, y) in gray_tmask(g4):
        if not (0 <= x < Wc and 0 <= y < Hc): continue
        m[y][x] = 0 if y < TZ else orb_at(g4, x, y)
    oi, fi = text_indices(g4, 0, TZ)
    fillW = masks[s][2]
    x0 = 16 - fillW//2
    y0 = 1 if len(s) <= 2 else 0
    canvas = typeset(m, masks[s], x0, y0, oi, fi)
    writeback(g4, canvas)
    print(f'회색 cell{g4}: "{s}" 완료')

# ---- 미리보기 & 재인코드 ----
sheet = Image.new('RGB', (16*44, 2*80), (40, 40, 40))
dr = ImageDraw.Draw(sheet)
for k in range(16):
    im, _, _ = cncp.render_cell(bytes(g), info['cells'][k], pal)
    im0, _, _ = cncp.render_cell(r['gfx'], info['cells'][k], pal)
    if im: sheet.paste(im, (k*44+4, 12), im)
    if im0: sheet.paste(im0, (k*44+4, 92), im0)
    dr.text((k*44+4, 0), str(k), fill=(255, 255, 0))
sheet = sheet.resize((sheet.width*2, sheet.height*2), Image.NEAREST)
sheet.save(os.path.join(WORK, 'preview_DCHOOSE.png'))
new_scm = scmenc.rebuild(orig, bytes(g))
open(os.path.join(WORK, 'DCHOOSE.SCM.kr'), 'wb').write(new_scm)
chk = scmimg.decode(new_scm)
print(f'재인코드: {len(orig)}B -> {len(new_scm)}B 일치={chk["gfx"]==bytes(g)} -> preview_DCHOOSE.png')
