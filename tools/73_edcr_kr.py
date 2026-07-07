# -*- coding: utf-8 -*-
# EDCR01_4.SCM (덱편집 화면 결정/뒤로 버튼) 식자
#  cell0/1=決定소(글자+구슬), 2/3=決定대(글자만), 4/5=戻る소, 6/7=戻る대
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
off, sz = files['EDCR01_4.SCM']
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

maps = {i: index_map(i) for i in range(8)}
def luma(c): return 0.299*c[0]+0.587*c[1]+0.114*c[2]

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

def text_indices(ci, palno, ylo, yhi):
    cnt = Counter(v for y in range(ylo, yhi) for v in maps[ci][y] if v > 0)
    cand = [v for v, n in cnt.items() if n >= 4]
    o = min(cand, key=lambda v: luma(pal[palno*16+v]))
    f = max(cand, key=lambda v: luma(pal[palno*16+v]))
    return o, f

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

# 결정 대(2/3)는 글자만(ASCII 확인) → 전부 지우고 그리기
BIG = {2: ('결정', 16, 3), 3: ('결정', 16, 3)}
for ci, (s, px, palno) in BIG.items():
    oi, fi = text_indices(ci, palno, 2, 34)
    mask = make_masks(s, px)
    W, H = cell_geom(ci)[2], cell_geom(ci)[3]
    x0, y0 = max(0, (W - mask[2])//2), max(0, (35 - mask[3])//2)
    blank = [[0]*W for _ in range(H)]
    canvas = typeset(blank, mask, x0, y0, oi, fi)
    writeback(ci, canvas)
    print(f'cell{ci}(대): "{s}" 외곽={oi:X} 채움={fi:X} at({x0},{y0}) {mask[2]}x{mask[3]}')

# 소형/뒤로 대(6/7, 구슬 포함): 2상태 변화=구슬, 불변=글자 → 행0-(TZ-1) 지움, TZ+ 인페인트
SMALL = {(0, 1): ('결정', 11, 3, 13), (4, 5): ('뒤로', 11, 4, 13), (6, 7): ('뒤로', 13, 4, 14)}
for (a, b), (s, px, palno, TZ) in SMALL.items():
    W, H = cell_geom(a)[2], cell_geom(a)[3]
    text = set()
    for y in range(H):
        for x in range(W):
            va, vb = maps[a][y][x], maps[b][y][x]
            if y < TZ:
                if va or vb: text.add((x, y))
            elif va == vb and va:
                text.add((x, y))
    orbs = {}
    for ci in (a, b):
        m = [row[:] for row in maps[ci]]
        for (x, y) in sorted(text):
            if y < TZ: m[y][x] = 0
        for (x, y) in sorted(text):
            if y >= TZ:
                v = 0
                for dd in range(1, W):
                    if x-dd >= 0 and (x-dd, y) not in text and m[y][x-dd]: v = m[y][x-dd]; break
                    if x+dd < W and (x+dd, y) not in text and m[y][x+dd]: v = m[y][x+dd]; break
                m[y][x] = v
        orbs[ci] = m
    oi, fi = text_indices(a, palno, 1, 12)
    mask = make_masks(s, px)
    x0, y0 = max(0, (W - mask[2])//2 - 2), 1
    for ci in (a, b):
        canvas = typeset(orbs[ci], mask, x0, y0, oi, fi)
        writeback(ci, canvas)
    print(f'cell{a}/{b}(소): "{s}" 글자픽셀={len(text)} 외곽={oi:X} 채움={fi:X}')

# 미리보기 + 재인코드
sheet = Image.new('RGB', (8*36, 2*60), (40, 40, 40))
dr = ImageDraw.Draw(sheet)
for k in range(8):
    im, _, _ = cncp.render_cell(bytes(g), info['cells'][k], pal)
    im0, _, _ = cncp.render_cell(r['gfx'], info['cells'][k], pal)
    if im: sheet.paste(im, (k*36+4, 12), im)
    if im0: sheet.paste(im0, (k*36+4, 72), im0)
    dr.text((k*36+4, 0), str(k), fill=(255,255,0))
sheet = sheet.resize((sheet.width*3, sheet.height*3), Image.NEAREST)
sheet.save(os.path.join(WORK, 'preview_EDCR.png'))
new_scm = scmenc.rebuild(orig, bytes(g))
open(os.path.join(WORK, 'EDCR01_4.SCM.kr'), 'wb').write(new_scm)
chk = scmimg.decode(new_scm)
print(f'재인코드: {len(orig)}B -> {len(new_scm)}B 일치={chk["gfx"]==bytes(g)} -> preview_EDCR.png')
