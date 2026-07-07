# -*- coding: utf-8 -*-
# 모드선택 상단화면 (TIT_1L0-4) 한글 식자: 헤더 モード選択→모드 선택, 캡션 5종
#  자체 맵 = 화면 배열 + 범위밖 참조 0 → 비트맵 자유 편집 후 rebuild_c(타일 성장 허용)
import sys, os, json
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, bgscm, scmimg
from PIL import Image, ImageFont, ImageDraw, ImageFilter

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
OUT = os.path.join(WORK, 'banner')
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}

CAPTIONS = {'TIT_1L0.SCM': '삼국영걸전', 'TIT_1L1.SCM': '단련의 장',
            'TIT_1L2.SCM': '통신의 장', 'TIT_1L3.SCM': '군의', 'TIT_1L4.SCM': '튜토리얼'}

def load(nm):
    off, sz = files[nm]
    d = sang[off:off+sz]
    info = bgscm.parse(d)
    hdr, ent, _ = bgscm.decode_map(d[info['u16'][4]:])
    ent = list(ent[:1024])
    tl = info['tiles']
    bm = [[0]*256 for _ in range(256)]
    pm = [[0]*256 for _ in range(256)]
    for i, e in enumerate(ent):
        t = e & 0x3FF
        if t >= info['ntiles']: continue
        hf=(e>>10)&1; vf=(e>>11)&1; p=(e>>12)&0xF
        tx, ty = (i%32)*8, (i//32)*8
        base = t*32
        for y in range(8):
            for x in range(8):
                b = tl[base+y*4+x//2]
                v = (b>>4) if (x&1) else (b&0xF)
                sx = 7-x if hf else x; sy = 7-y if vf else y
                bm[ty+sy][tx+sx] = v
                pm[ty+sy][tx+sx] = p
    return d, info, ent, bm, pm

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

def luma_of(pal, p, v):
    ci = p*16+v
    if ci >= len(pal): return 0
    c = pal[ci]
    return 0.299*c[0]+0.587*c[1]+0.114*c[2]

def edit_region(bm, pm, pal, x0, x1, y0, y1, label, px, tag,
                white_thr=200, fill_min=180, tspan=None):
    """텍스트(밝은 픽셀) 소거 → 열별 배경 복원 → 한글 식자 (셀 팔레트행별 최적 인덱스)"""
    # 텍스트 = 밝은(luma>=white_thr) 픽셀
    tpix = [(x, y) for y in range(y0, y1) for x in range(x0, x1)
            if bm[y][x] and luma_of(pal, pm[y][x], bm[y][x]) >= white_thr]
    if not tpix:
        print(f'{tag}: 밝은 텍스트 없음'); return
    ys = sorted(p[1] for p in tpix)
    ts0, ts1 = ys[0], ys[-1]
    if tspan: ts0, ts1 = tspan
    # 열별 목표 배경색: 지배 팔레트행의 모드 → 각 행에서 최근접 색 인덱스
    colbg = {}
    for x in range(x0, x1):
        prows = Counter(pm[y][x] for y in range(y0, y1) if bm[y][x])
        if not prows: continue
        # 지배 행에서 배경 모드색
        dom = None
        for prow, _n in prows.most_common():
            cnt = Counter(bm[y][x] for y in range(y0, y1)
                          if pm[y][x] == prow and bm[y][x]
                          and luma_of(pal, prow, bm[y][x]) < white_thr)
            if cnt:
                dom = pal[prow*16 + cnt.most_common(1)[0][0]]
                break
        if dom is None: continue
        for prow in prows:
            best = min(range(1, 16),
                       key=lambda v: sum((a-b)**2 for a, b in zip(pal[prow*16+v] if prow*16+v < len(pal) else (0,0,0), dom)))
            colbg[(x, prow)] = best
    # 소거: 텍스트 스팬(±3) 전체를 열별 배경으로 평탄화
    for y in range(max(y0, ts0-3), min(y1, ts1+4)):
        for x in range(x0, x1):
            if not bm[y][x]: continue
            bg = colbg.get((x, pm[y][x]))
            if bg is not None:
                bm[y][x] = bg
    # 식자
    fill, outl, mw, mh = mask_h(label, px, bold=True)
    xs_t = sorted(p[0] for p in tpix)
    bx0, bx1 = xs_t[0], xs_t[-1]
    px0 = bx0 + (bx1 - bx0 + 1 - mw)//2
    py0 = ts0 + max(0, ((ts1 - ts0 + 1) - mh)//2)
    for pts, dark in ((outl, True), (fill, False)):
        for (x, y) in pts:
            X, Y = px0 + x, py0 + y
            if not (x0 <= X < x1 and y0 <= Y < y1): continue
            prow = pm[Y][X]
            cand = range(1, 16)
            if dark:
                v = min(cand, key=lambda v: abs(luma_of(pal, prow, v) - 20))
            else:
                v = max(cand, key=lambda v: luma_of(pal, prow, v) if luma_of(pal, prow, v) >= fill_min else luma_of(pal, prow, v))
            bm[Y][X] = v
    print(f'{tag}: 텍스트 y{ts0}-{ts1} 마스크 {mw}x{mh} @({px0},{py0})')

for nm, cap in CAPTIONS.items():
    d, info, ent, bm, pm = load(nm)
    pal = scmimg.pal_to_rgb(info['pal'])
    # 캡션 (raw x 112-141, y 40-210)
    edit_region(bm, pm, pal, 112, 141, 40, 210, cap, 13, f'{nm} 캡션')
    # 헤더 (raw x 224-256, y 0-110): モード選択 → 모드 선택
    edit_region(bm, pm, pal, 224, 256, 0, 140, '모드 선택', 12, f'{nm} 헤더', white_thr=150, tspan=(16, 126))
    new, nt = bgscm.rebuild_c(d, info, ent, bm)
    # 검증: 재파스 렌더 == bm
    info2 = bgscm.parse(new)
    hdr2, ent2, _ = bgscm.decode_map(new[info2['u16'][4]:])
    ok = list(ent2[:len(ent)]) == [e for e in ent] or True
    bm2 = [[0]*256 for _ in range(256)]
    tl2 = info2['tiles']
    bad = 0
    for i, e in enumerate(ent2[:1024]):
        t = e & 0x3FF
        hf=(e>>10)&1; vf=(e>>11)&1
        tx, ty = (i%32)*8, (i//32)*8
        base = t*32
        for y in range(8):
            for x in range(8):
                b = tl2[base+y*4+x//2]
                v = (b>>4) if (x&1) else (b&0xF)
                sx = 7-x if hf else x; sy = 7-y if vf else y
                if bm[ty+sy][tx+sx] != v: bad += 1
    print(f'{nm}: 타일 {info["ntiles"]}→{nt}, 재구성 픽셀불일치 {bad}')
    if bad == 0:
        open(os.path.join(WORK, nm + '.kr'), 'wb').write(new)
    # 미리보기
    cols = pal
    img = Image.new('RGB', (256, 256), (255,0,255))
    pxl = img.load()
    for y in range(256):
        for x in range(256):
            v = bm[y][x]
            if v:
                ci = pm[y][x]*16+v
                if ci < len(cols): pxl[x, y] = cols[ci]
    img.transpose(Image.ROTATE_90).resize((512,512), Image.NEAREST).save(
        os.path.join(OUT, f'topkr_{nm}.png'))
print('완료')
