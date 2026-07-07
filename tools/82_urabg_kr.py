# -*- coding: utf-8 -*-
# URA_BG0(카드 상세 화면 배경) 라벨 한글 식자
#  뷰(회전) 좌표로 bbox 지정 → 비트맵 좌표 변환 → 텍스트 인덱스 소거(행내 인페인트) → 한글 드로잉
import os, sys, json
from collections import Counter
from PIL import Image, ImageFont, ImageDraw, ImageFilter
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, scmimg, bgscm

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}
off, sz = files['URA_BG0.SCM']
orig = sang[off:off+sz]
info = bgscm.parse(orig)
bm, pmap = bgscm.index_bitmap(info, 32)
H, W = len(bm), len(bm[0])   # 200 x 256
pal = scmimg.pal_to_rgb(info['pal'])
print(f'비트맵 {W}x{H}, 팔레트 {len(pal)}색')

def luma(c): return 0.299*c[0]+0.587*c[1]+0.114*c[2]

def v2b(vx, vy):
    """뷰(200x256) → 비트맵 (row, col)"""
    return vx, 255 - vy

def make_mask(s, px, bold=True, thr=110):
    font = ImageFont.truetype(r'C:\Windows\Fonts\gulim.ttc', px)
    img = Image.new('L', (px*len(s)*2+8, px*2+8), 0)
    d = ImageDraw.Draw(img)
    d.text((4, 4), s, fill=255, font=font)
    if bold: d.text((5, 4), s, fill=255, font=font)
    img = img.point(lambda v: 255 if v >= thr else 0)
    img = img.crop(img.getbbox()).transpose(Image.ROTATE_270)
    dil = img.filter(ImageFilter.MaxFilter(3))
    Wm, Hm = img.size
    fill = {(x, y) for y in range(Hm) for x in range(Wm) if img.getpixel((x, y))}
    outl = {(x, y) for y in range(Hm) for x in range(Wm)
            if dil.getpixel((x, y)) and (x, y) not in fill}
    return fill, outl, Wm, Hm

def edit_label(vbox, s, px, vertical=False):
    vx0, vy0, vx1, vy1 = vbox
    r0, c0 = v2b(vx0, vy1)   # 비트맵 rows vx0..vx1, cols 255-vy1..255-vy0
    r1, c1 = v2b(vx1, vy0)
    r0, r1 = min(r0, r1), max(r0, r1)
    c0, c1 = min(c0, c1), max(c0, c1)
    # 팔레트행/패널색
    ring = []
    inner = []
    for r in range(max(0, r0-1), min(H, r1+2)):
        for c in range(max(0, c0-1), min(W, c1+2)):
            if r0 <= r <= r1 and c0 <= c <= c1:
                inner.append((r, c))
            else:
                ring.append((r, c))
    prow = Counter(pmap[r][c] for r, c in inner).most_common(1)[0][0]
    panel = Counter(bm[r][c] for r, c in ring
                    if pmap[r][c] == prow and bm[r][c] != 0).most_common(1)[0][0]
    pl = luma(pal[prow*16+panel])
    cnt = Counter(bm[r][c] for r, c in inner if bm[r][c] != 0)
    # 텍스트 = 패널과 22 이상 차이나는 모든 인덱스(0 제외)
    text_idx = {v for v in cnt if abs(luma(pal[prow*16+v]) - pl) > 22}
    if not text_idx:
        print(f'  경고: "{s}" 텍스트 인덱스 미검출 (panel={panel})')
    erased = []
    for r in range(r0, r1+1):
        for c in range(c0, c1+1):
            if bm[r][c] in text_idx:
                erased.append((r, c))
                v = panel
                for dd in range(1, 40):
                    if c-dd >= c0-4 and c-dd >= 0 and bm[r][c-dd] not in text_idx:
                        v = bm[r][c-dd]; break
                    if c+dd <= c1+4 and c+dd < W and bm[r][c+dd] not in text_idx:
                        v = bm[r][c+dd]; break
                bm[r][c] = v
    # 팔레트행 = 실제 지운 픽셀들의 최빈행 (라벨 셀 기준)
    if erased:
        prow = Counter(pmap[r][c] for r, c in erased).most_common(1)[0][0]
    # 색 선택 (0 금지)
    if text_idx:
        fi = max(text_idx, key=lambda v: cnt[v])
        rest = [v for v in text_idx if abs(luma(pal[prow*16+v]) - luma(pal[prow*16+fi])) > 50]
        oi = max(rest, key=lambda v: cnt[v]) if rest else None
    else:
        fi, oi = 15, None
    # 드로잉
    if vertical:
        # 뷰 세로쓰기: 글자별로 뷰 y를 내려가며 배치
        chs = list(s)
        n = len(chs)
        vyc0 = vy0
        step = (vy1 - vy0) / n
        for i, ch in enumerate(chs):
            fill, outl, Wm, Hm = make_mask(ch, px)
            cy = (vy0 + step*i + step/2)
            cx = (vx0 + vx1) / 2
            x0 = int(255 - cy - Wm/2)
            y0 = int(cx - Hm/2)
            drawmask(fill, outl, x0, y0, fi, oi, prow)
    else:
        fill, outl, Wm, Hm = make_mask(s, px)
        cx = (vx0 + vx1) / 2
        cy = (vy0 + vy1) / 2
        x0 = int(255 - cy - Wm/2)
        y0 = int(cx - Hm/2)
        drawmask(fill, outl, x0, y0, fi, oi, prow)
    print(f'"{s}": bbox r{r0}-{r1} c{c0}-{c1} pal행{prow} panel={panel} fill={fi:X} outl={oi if oi is None else hex(oi)}')

def drawmask(fill, outl, x0, y0, fi, oi, prow):
    if oi is not None:
        for (x, y) in outl:
            C, R = x0+x, y0+y
            if 0 <= C < W and 0 <= R < H:
                bm[R][C] = oi
    for (x, y) in fill:
        C, R = x0+x, y0+y
        if 0 <= C < W and 0 <= R < H:
            bm[R][C] = fi

JOBS = [
    ((30, 7, 68, 27), '성명:', 12, False),
    ((34, 27, 62, 45), '자:', 12, False),
    ((26, 43, 64, 61), '소속:', 12, False),
    ((64, 65, 154, 91), '인물상세', 14, False),
    ((97, 84, 115, 112), '병종', 12, True),
    ((120, 82, 148, 97), '무력', 12, False),
    ((154, 82, 182, 97), '지력', 12, False),
    ((38, 134, 104, 152), '필요 사기:', 11, False),
    ((34, 160, 100, 178), '효과 시간:', 11, False),
    ((64, 174, 154, 200), '계략상세', 14, False),
]
for vbox, s, px, vert in JOBS:
    edit_label(vbox, s, px, vert)

# 재조립 + 미리보기
new, nt = bgscm.rebuild(orig, info, bm, 32)
open(os.path.join(WORK, 'URA_BG0.SCM.kr'), 'wb').write(new)
info2 = bgscm.parse(new)
img = bgscm.render(info2, 32, 1).transpose(Image.ROTATE_90)
img = img.resize((img.width*3, img.height*3), Image.NEAREST)
img.save(os.path.join(WORK, 'preview_urabg0.png'))
print(f'재조립 타일 {nt}, {len(orig)}B -> {len(new)}B -> preview_urabg0.png')
