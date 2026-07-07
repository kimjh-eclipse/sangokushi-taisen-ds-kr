# -*- coding: utf-8 -*-
# EDCL01_1.SCM (덱편집 좌화면 라벨: 合計コスト/オーバー/勢力ボーナス!) 식자 — 전부 글자만(구슬 없음)
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
off, sz = files['EDCL01_1.SCM']
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

JOBS = {
    0: ('총코스트', 10),
    1: ('오버', 12),
    2: ('1세력보너스!', 10), 3: ('1세력보너스!', 10),
    4: ('1세력보너스!', 10), 5: ('1세력보너스!', 10),
    6: ('2세력보너스!', 10), 7: ('2세력보너스!', 10),
    8: ('2세력보너스!', 10), 9: ('2세력보너스!', 10),
}
for ci, (s, px) in JOBS.items():
    m = index_map(ci)
    W, H = cell_geom(ci)[2], cell_geom(ci)[3]
    palno = (info['cells'][ci]['oams'][0][2] >> 12) & 0xF
    cnt = Counter(v for row in m for v in row if v)
    cand = [v for v, n in cnt.items() if n >= 6]
    oi = min(cand, key=lambda v: luma(pal[palno*16+v]))
    fi = max(cand, key=lambda v: luma(pal[palno*16+v]))
    mask = make_masks(s, px)
    x0 = max(0, (W - mask[2])//2)
    y0 = max(0, (H - mask[3])//2)
    blank = [[0]*W for _ in range(H)]
    canvas_ = blank
    fill, outl, mw, mh = mask
    for (x, y) in outl:
        X, Y = x0+x, y0+y
        if 0 <= X < W and 0 <= Y < H: canvas_[Y][X] = oi
    for (x, y) in fill:
        X, Y = x0+x, y0+y
        if 0 <= X < W and 0 <= Y < H: canvas_[Y][X] = fi
    writeback(ci, canvas_)
    print(f'cell{ci}: "{s}" {mw}x{mh} in {W}x{H} 외곽={oi:X} 채움={fi:X}')

sheet = Image.new('RGB', (16*40, 2*100), (40, 40, 40))
dr = ImageDraw.Draw(sheet)
for k in range(16):
    im, _, _ = cncp.render_cell(bytes(g), info['cells'][k], pal)
    im0, _, _ = cncp.render_cell(r['gfx'], info['cells'][k], pal)
    if im: sheet.paste(im, (k*40+4, 12), im)
    if im0: sheet.paste(im0, (k*40+4, 112), im0)
    dr.text((k*40+4, 0), str(k), fill=(255,255,0))
sheet = sheet.resize((sheet.width*2, sheet.height*2), Image.NEAREST)
sheet.save(os.path.join(WORK, 'preview_EDCL.png'))
new_scm = scmenc.rebuild(orig, bytes(g))
open(os.path.join(WORK, 'EDCL01_1.SCM.kr'), 'wb').write(new_scm)
chk = scmimg.decode(new_scm)
print(f'재인코드: {len(orig)}B -> {len(new_scm)}B 일치={chk["gfx"]==bytes(g)}')
