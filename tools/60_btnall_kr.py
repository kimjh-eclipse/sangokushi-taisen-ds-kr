# -*- coding: utf-8 -*-
# BTNALL.SCM 예/아니오 식자 (파일럿)
#  대상: cell6/7/8 はい→예(빨강), cell12/13/14 いいえ→아니오(파랑), cell29/31 회색판
#  구슬 복원 원리:
#   (1) 글자는 상태(버튼 3연속 셀) 간 불변, 구슬은 상태 간 변함 → 상태간 다른 픽셀 = 확실한 구슬
#   (2) 같은 팔레트·상태의 다른 버튼과 만장일치 → 안정 구슬(그림자 등)
#   (3) 남은 픽셀 = 글자 → 같은 팔레트 다른 버튼 중 "그 픽셀이 구슬인 버튼"에서 값 차용
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

def index_map(ci):
    cell = info['cells'][ci]
    m = [[0]*32 for _ in range(40)]
    for a0, a1, a2 in cell['oams']:
        shape=(a0>>14)&3; size=(a1>>14)&3
        w,h = cncp.OBJ_SIZES[(shape,size)]
        x = cncp.sgn(a1&0x1FF,9)+20; y = cncp.sgn(a0&0xFF,8)+20
        tile = a2 & 0x3FF
        tw, th = w//8, h//8
        for ty in range(th):
            for tx in range(tw):
                tofs = cell['gfxBase'] + (tile+ty*tw+tx)*32
                for yy in range(8):
                    for xx in range(8):
                        b = g[tofs+yy*4+xx//2]
                        m[y+ty*8+yy][x+tx*8+xx] = (b>>4) if (xx&1) else (b&0xF)
    return m

def writeback(ci, canvas):
    cell = info['cells'][ci]
    for a0, a1, a2 in cell['oams']:
        shape=(a0>>14)&3; size=(a1>>14)&3
        w,h = cncp.OBJ_SIZES[(shape,size)]
        x = cncp.sgn(a1&0x1FF,9)+20; y = cncp.sgn(a0&0xFF,8)+20
        tile = a2 & 0x3FF
        tw, th = w//8, h//8
        for ty in range(th):
            for tx in range(tw):
                tofs = cell['gfxBase'] + (tile+ty*tw+tx)*32
                for yy in range(8):
                    for xx in range(0, 8, 2):
                        lo = canvas[y+ty*8+yy][x+tx*8+xx] & 0xF
                        hi = canvas[y+ty*8+yy][x+tx*8+xx+1] & 0xF
                        g[tofs+yy*4+xx//2] = lo | (hi<<4)

STD = [i for i in range(48) if len(info['cells'][i]['oams'])==2
       and cncp.sgn(info['cells'][i]['oams'][0][0]&0xFF,8)==-20]
maps = {i: index_map(i) for i in STD}

TRIPLES = {0:(0,1,2), 6:(6,7,8), 9:(9,10,11), 12:(12,13,14),
           15:(15,16,17), 18:(18,19,20), 36:(36,37,38)}
PAL_POOLS = {'pal0': [0, 6, 36], 'pal2': [9, 12, 15, 18]}

def analyze(base, pool):
    """버튼(base)의 상태별 깨끗한 구슬 3장 + 글자마스크 반환"""
    tri = TRIPLES[base]
    others = [b for b in pool if b != base]
    orbs = [[[0]*32 for _ in range(40)] for _ in range(3)]
    text = set()
    leftover = []
    for y in range(14, 40):
        for x in range(32):
            vals = [maps[c][y][x] for c in tri]
            if len(set(vals)) > 1:                       # (1) 상태간 변화 = 구슬
                for s in range(3): orbs[s][y][x] = vals[s]
                continue
            uni = [maps[TRIPLES[b][0]][y][x] for b in pool]
            if len(set(uni)) == 1:                       # (2) 버튼간 만장일치 = 안정 구슬
                for s in range(3): orbs[s][y][x] = maps[TRIPLES[base][s]][y][x]
                continue
            text.add((x, y))                             # (3) 글자 → 타 버튼에서 차용
            got = False
            for s in range(3):
                cand = []
                for b in others:
                    bv = [maps[c][y][x] for c in TRIPLES[b]]
                    if len(set(bv)) > 1:                 # 그 버튼에선 구슬(상태간 변화)
                        cand.append(bv[s])
                if cand:
                    orbs[s][y][x] = Counter(cand).most_common(1)[0][0]
                    got = True
            if not got:
                leftover.append((x, y))
    # 잔여: 같은 상태 타 버튼 값의 최빈값(안정 영역인데 불일치 = 타버튼 글자겹침)으로
    for (x, y) in leftover:
        for s in range(3):
            cand = [maps[TRIPLES[b][s]][y][x] for b in others]
            orbs[s][y][x] = Counter(cand).most_common(1)[0][0]
    # 글자마스크에 행0~13 비투명 추가
    for y in range(14):
        for x in range(32):
            if maps[base][y][x]: text.add((x, y))
    return orbs, text, len(leftover)

def luma(c): return 0.299*c[0]+0.587*c[1]+0.114*c[2]

def text_indices(ci, palno):
    cnt = Counter(v for y in range(2, 13) for v in maps[ci][y] if v > 0)
    cand = [v for v, n in cnt.items() if n >= 4]
    o = min(cand, key=lambda v: luma(pal[palno*16+v]))
    f = max(cand, key=lambda v: luma(pal[palno*16+v]))
    return o, f

def make_masks(s, px):
    font = ImageFont.truetype(r'C:\Windows\Fonts\gulim.ttc', px)
    img = Image.new('L', (px*len(s)*2+8, px*2+8), 0)
    ImageDraw.Draw(img).text((4, 4), s, fill=255, font=font)
    img = img.point(lambda v: 255 if v >= 128 else 0)
    img = img.crop(img.getbbox()).transpose(Image.ROTATE_270)   # 90° 시계방향
    dil = img.filter(ImageFilter.MaxFilter(3))
    W, H = img.size
    fill = {(x, y) for y in range(H) for x in range(W) if img.getpixel((x, y))}
    outl = {(x, y) for y in range(H) for x in range(W)
            if dil.getpixel((x, y)) and (x, y) not in fill}
    return fill, outl, W, H

def typeset(base_canvas, mask, x0, y0, oi, fi):
    fill, outl, W, H = mask
    canvas = [row[:] for row in base_canvas]
    for (x, y) in outl:
        X, Y = x0+x, y0+y
        if 0 <= X < 32 and 0 <= Y < 40: canvas[Y][X] = oi
    for (x, y) in fill:
        X, Y = x0+x, y0+y
        if 0 <= X < 32 and 0 <= Y < 40: canvas[Y][X] = fi
    return canvas

# ---- 컬러 버튼 분석 ----
AN = {}   # base -> (orbs[3], text, leftover)
for palkey, pool in PAL_POOLS.items():
    for b in pool:
        orbs, text, lo = analyze(b, pool)
        AN[b] = (orbs, text)
        if b in (6, 12):
            print(f'버튼 cell{b}: 글자픽셀={len(text)} 차용불가(잔여)={lo}')

# ---- 회색(pal4) 대상: 컬러 counterpart의 글자마스크 위치를 그대로 사용 ----
BTN_GRAY = {0: 27, 6: 29, 9: 30, 12: 31, 15: 32, 18: 33, 36: 39}   # 앞서 유사도 1.00 매칭
def dilate1(mask):
    return {(x+dx, y+dy) for (x, y) in mask for dx in (-1,0,1) for dy in (-1,0,1)}

def gray_clean(target_base):
    """회색 셀 = 원본에서 글자픽셀만 타 회색버튼(그 자리가 구슬인) 값으로 치환"""
    t4 = BTN_GRAY[target_base]
    tmask = dilate1(AN[target_base][1])
    m = [row[:] for row in maps[t4]]
    unk = 0
    for (x, y) in tmask:
        if not (0 <= x < 32 and 0 <= y < 40): continue
        if y < 14:
            m[y][x] = 0
            continue
        cand = [maps[BTN_GRAY[b]][y][x] for b in BTN_GRAY
                if b != target_base and (x, y) not in dilate1(AN[b][1])]
        if cand:
            m[y][x] = Counter(cand).most_common(1)[0][0]
        else:
            unk += 1   # 그대로 두면 일본어 잔해 → 최빈 이웃값
            near = [m[y][x-d] for d in (1,2,3) if x-d >= 0] + [m[y][x+d] for d in (1,2,3) if x+d < 32]
            m[y][x] = Counter(near).most_common(1)[0][0] if near else 0
    return m, unk

# ---- 식자 ----
masks = {'예': make_masks('예', 13), '아니오': make_masks('아니오', 11)}
for s, mk in masks.items():
    print(f'마스크 "{s}": {mk[2]}x{mk[3]} (회전후)')

def place(s, W, H):
    if s == '예':
        return 16 - W//2, max(0, 14 - H//2)
    return 16 - W//2, 0

# 컬러: cell6/7/8=예(pal0), cell12/13/14=아니오(pal2)
for base, s, palno in ((6, '예', 0), (12, '아니오', 2)):
    oi, fi = text_indices(base, palno)
    W, H = masks[s][2], masks[s][3]
    x0, y0 = place(s, W, H)
    orbs, _ = AN[base]
    for st in range(3):
        canvas = typeset(orbs[st], masks[s], x0, y0, oi, fi)
        writeback(TRIPLES[base][st], canvas)
    print(f'cell{TRIPLES[base]}: "{s}" (외곽선={oi:X} 채움={fi:X} at {x0},{y0})')

# 회색: cell29=예, cell31=아니오
for base, s in ((6, '예'), (12, '아니오')):
    t4 = BTN_GRAY[base]
    oi, fi = text_indices(t4, 4)
    W, H = masks[s][2], masks[s][3]
    x0, y0 = place(s, W, H)
    m, unk = gray_clean(base)
    canvas = typeset(m, masks[s], x0, y0, oi, fi)
    writeback(t4, canvas)
    print(f'cell{t4}: "{s}" (외곽선={oi:X} 채움={fi:X}, 잔여보간={unk})')

# ---- 미리보기 ----
sheet = Image.new('RGB', (8*40, 2*56), (40, 40, 40))
dr = ImageDraw.Draw(sheet)
for k, ci in enumerate([6, 7, 8, 12, 13, 14, 29, 31]):
    im, _, _ = cncp.render_cell(bytes(g), info['cells'][ci], pal)
    sheet.paste(im, (k*40+4, 14), im)
    dr.text((k*40+4, 2), str(ci), fill=(255, 255, 0))
    im0, _, _ = cncp.render_cell(r['gfx'], info['cells'][ci], pal)
    sheet.paste(im0, (k*40+4, 70), im0)
sheet = sheet.resize((sheet.width*3, sheet.height*3), Image.NEAREST)
sheet.save(os.path.join(WORK, 'preview_btnall_kr.png'))
print('-> preview_btnall_kr.png (위=수정, 아래=원본)')

# ---- 재인코드 & 저장 ----
new_scm = scmenc.rebuild(orig, bytes(g))
open(os.path.join(WORK, 'BTNALL.SCM.kr'), 'wb').write(new_scm)
chk = scmimg.decode(new_scm)
print(f'재인코드: {len(orig)}B -> {len(new_scm)}B, 재해제일치={chk["gfx"]==bytes(g)}')
