# -*- coding: utf-8 -*-
# URA_BG0 라벨 재도전: 원본 ST_FONT 글리프 템플릿 매칭 → 정밀 마스크 지움 → 한글 식자
import os, sys, json
from collections import Counter
from PIL import Image, ImageFont, ImageDraw
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, scmimg, bgscm
from nftr import NFTR

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
H, W = len(bm), len(bm[0])
pal = scmimg.pal_to_rgb(info['pal'])

font = NFTR(open(os.path.join(WORK, 'ST_FONT.nftr'), 'rb').read())

def luma_at(r, c):
    i = pmap[r][c]*16 + bm[r][c]
    if i >= len(pal): return 128.0
    col = pal[i]
    return 0.299*col[0] + 0.587*col[1] + 0.114*col[2]

def glyph_cw(ch):
    """문자 → 타일공간(시계 90도 회전) 12x12 비트그리드"""
    code = int.from_bytes(ch.encode('cp932'), 'big')
    g = font.code2glyph.get(code)
    if g is None: return None
    grid = font.get_glyph_bitmap(g)
    gh, gw = len(grid), len(grid[0])
    rot = [[0]*gh for _ in range(gw)]   # (gw x gh)
    for y in range(gh):
        for x in range(gw):
            if grid[y][x]:
                rot[x][gh-1-y] = 1      # CW: (x,y)->(col=gh-1-y, row=x)
    return rot

def template(s, pitch=12):
    """문자열 → [(dr, dc)] ON 오프셋 (행=진행방향)"""
    ons = []
    r0 = 0
    for ch in s:
        rot = glyph_cw(ch)
        if rot is None:
            print('  글리프없음:', ch); r0 += pitch; continue
        for rr in range(len(rot)):
            for cc in range(len(rot[0])):
                if rot[rr][cc]:
                    ons.append((r0+rr, cc))
        r0 += pitch
    return ons, r0

import numpy as np
LUMA = np.array([[luma_at(r, c) for c in range(W)] for r in range(H)], dtype=np.float64)

def match(ons, tlen):
    """제로민 커널 FFT 상관 → |corr| 최대 앵커"""
    th = tlen + 1
    tw = 13
    K = np.zeros((th, tw))
    ring = set()
    onset = set(ons)
    for (r, c) in ons:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                p = (r+dr, c+dc)
                if p not in onset and 0 <= p[0] < th and 0 <= p[1] < tw:
                    ring.add(p)
    for (r, c) in ons:
        if 0 <= r < th and 0 <= c < tw:
            K[r, c] = 1.0
    for (r, c) in ring:
        K[r, c] = -1.0
    sup = (K != 0).astype(np.float64)
    K[K != 0] -= K[K != 0].mean()
    kn = np.sqrt((K**2).sum())
    n = sup.sum()
    # FFT 상관 (커널은 뒤집어야 상관이 됨 → conj 사용 방식 대신 커널 반전)
    fh, fw = H + th, W + tw
    def corr2(img, ker):
        FI = np.fft.rfft2(img, (fh, fw))
        FK = np.fft.rfft2(ker[::-1, ::-1], (fh, fw))
        full = np.fft.irfft2(FI * FK, (fh, fw))
        return full[th-1:th-1+H-th+1, tw-1:tw-1+W-tw+1]
    num = corr2(LUMA, K)
    s1 = corr2(LUMA, sup)
    s2 = corr2(LUMA**2, sup)
    var = np.maximum(s2 - s1*s1/n, 1e-6)
    zncc = num / (np.sqrt(var) * kn)
    idx = np.unravel_index(np.argmax(np.abs(zncc)), zncc.shape)
    return (abs(zncc[idx]), int(idx[0]), int(idx[1]))

def erase_and_draw(label, korean, vbox=None, px=12):
    best = None
    for pitch in (12, 13):
        ons, tlen = template(label, pitch)
        if not ons: return
        b = match(ons, tlen)
        if b and (best is None or b[0] > best[0][0]):
            best = (b, ons, tlen, pitch)
    b, ons, tlen, pitch = best
    if b is None:
        print(f'"{label}": 매칭 실패 — 건너뜀')
        return
    score, ar, ac = b
    # 지움: 마스크+1px 팽창 → 행방향 인페인트
    mask = set()
    for (dr, dc) in ons:
        for ddr in (-1, 0, 1):
            for ddc in (-1, 0, 1):
                mask.add((ar+dr+ddr, ac+dc+ddc))
    # 지운 픽셀 원래값(글자색) 수집
    tcnt = Counter()
    prow_cnt = Counter()
    for (dr, dc) in ons:
        R, C = ar+dr, ac+dc
        if 0 <= R < H and 0 <= C < W:
            tcnt[bm[R][C]] += 1
            prow_cnt[pmap[R][C]] += 1
    prow = prow_cnt.most_common(1)[0][0]
    fi = tcnt.most_common(1)[0][0]
    for (R, C) in sorted(mask):
        if not (0 <= R < H and 0 <= C < W): continue
        v = None
        for dd in range(1, 30):
            if C-dd >= 0 and (R, C-dd) not in mask: v = bm[R][C-dd]; break
            if C+dd < W and (R, C+dd) not in mask: v = bm[R][C+dd]; break
        if v is not None: bm[R][C] = v
    # 한글 드로잉 (라벨 앵커에 정렬)
    gfont = ImageFont.truetype(r'C:\Windows\Fonts\gulim.ttc', px)
    img = Image.new('L', (px*len(korean)*2+8, px*2+8), 0)
    d = ImageDraw.Draw(img)
    d.text((4, 4), korean, fill=255, font=gfont)
    d.text((5, 4), korean, fill=255, font=gfont)
    img = img.point(lambda v: 255 if v >= 110 else 0)
    img = img.crop(img.getbbox()).transpose(Image.ROTATE_270)
    mw, mh = img.size
    # 앵커: 라벨 시작(row=ar), 글자 세로중심 = ac+6
    x0 = ac + 6 - mw//2
    y0 = ar
    for y in range(mh):
        for x in range(mw):
            if img.getpixel((x, y)):
                R, C = y0+y, x0+x
                if 0 <= R < H and 0 <= C < W:
                    bm[R][C] = fi
    print(f'"{label}"→"{korean}": score={score:.1f} anchor=({ar},{ac}) fill={fi:X} prow={prow}')

JOBS = [
    ('姓名：', '성명:', (33, 8, 64, 24)),
    ('字：', '자:', (36, 30, 58, 46)),
    ('所属：', '소속:', (18, 112, 58, 130)),
    ('人物詳細', '인물상세', (74, 64, 152, 88)),
    ('兵種', '병종', (100, 84, 116, 112)),     # 세로쓰기 별도
    ('戦力', '무력', (122, 82, 146, 96)),
    ('知力', '지력', (154, 82, 178, 96)),
    ('必要士気：', '필요 사기:', (38, 140, 104, 158)),
    ('効果時間：', '효과 시간:', (34, 164, 100, 182)),
    ('計略詳細', '계략상세', (74, 176, 152, 200)),
]
for label, kor, vbox in JOBS:
    if label == '兵種':
        continue   # 세로쓰기 별도
    erase_and_draw(label, kor, vbox)

new, nt = bgscm.rebuild(orig, info, bm, 32)
open(os.path.join(WORK, 'URA_BG0.SCM.kr'), 'wb').write(new)
info2 = bgscm.parse(new)
img = bgscm.render(info2, 32, 1).transpose(Image.ROTATE_90)
img.resize((img.width*3, img.height*3), Image.NEAREST).save(os.path.join(WORK, 'preview_urabg0.png'))
print(f'재조립 타일 {nt} -> preview_urabg0.png')
