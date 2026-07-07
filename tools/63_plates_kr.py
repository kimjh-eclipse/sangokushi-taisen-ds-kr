# -*- coding: utf-8 -*-
# 판(plate)형 버튼/배너 한글 식자: FR_BTN2(지우기/종료), FR_BTN(군주명/칭호/상태),
#  KEYCH(터치조작/십자버튼조작), TIT_OBJ(맛보기대전/카드도감)
# 배경 복원: 글자는 판 중앙부에만 있음 → 각 열(x)의 끝단(캡 안쪽) 행들에서 배경색 샘플링
#  (판 그라데이션은 X방향, Y방향은 디더 외 균일) → 글자픽셀(배경과 불일치)을 배경으로 치환
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

def load(nm):
    off, sz = files[nm]
    orig = sang[off:off+sz]
    r = scmimg.decode(orig)
    return orig, bytearray(r['gfx']), scmimg.pal_to_rgb(r['pal']), cncp.parse(r['gfx'])

def cell_geom(info, ci):
    cell = info['cells'][ci]
    xs, ys, x1, y1 = 999, 999, -999, -999
    for a0, a1, a2 in cell['oams']:
        shape=(a0>>14)&3; size=(a1>>14)&3
        w,h = cncp.OBJ_SIZES[(shape,size)]
        x = cncp.sgn(a1&0x1FF,9); y = cncp.sgn(a0&0xFF,8)
        xs=min(xs,x); ys=min(ys,y); x1=max(x1,x+w); y1=max(y1,y+h)
    return xs, ys, x1-xs, y1-ys

def index_map(g, info, ci):
    xs, ys, W, H = cell_geom(info, ci)
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

def writeback(g, info, ci, canvas):
    xs, ys, W, H = cell_geom(info, ci)
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

def make_masks(s, px, thr=128, bold=False):
    font = ImageFont.truetype(r'C:\Windows\Fonts\gulim.ttc', px)
    img = Image.new('L', (px*len(s)*2+8, px*2+8), 0)
    d = ImageDraw.Draw(img)
    d.text((4, 4), s, fill=255, font=font)
    if bold:
        d.text((5, 4), s, fill=255, font=font)
    img = img.point(lambda v: 255 if v >= thr else 0)
    img = img.crop(img.getbbox()).transpose(Image.ROTATE_270)
    dil = img.filter(ImageFilter.MaxFilter(3))
    W, H = img.size
    fill = {(x, y) for y in range(H) for x in range(W) if img.getpixel((x, y))}
    outl = {(x, y) for y in range(H) for x in range(W)
            if dil.getpixel((x, y)) and (x, y) not in fill}
    return fill, outl, W, H

def clean_plate(m, capskip=3, sample=5, fullbg=False):
    """열별 배경(디더 패리티 포함) 샘플링 → 글자픽셀 치환. (clean_map, text_pixels, bg_fn)
    fullbg=True: 끝단 대신 열 전체 최빈값(글자가 판 끝까지 차는 긴 라벨용)"""
    H, W = len(m), len(m[0])
    bg = {}
    for x in range(W):
        ys = [y for y in range(H) if m[y][x] != 0]
        if not ys: continue
        y0, y1 = min(ys), max(ys)
        if fullbg:
            rows = list(range(y0+capskip, y1-capskip+1))
        else:
            rows = list(range(y0+capskip, min(y0+capskip+sample, y1))) + \
                   list(range(max(y1-capskip-sample+1, y0), y1-capskip+1))
        for par in (0, 1):
            vals = [m[y][x] for y in rows if y % 2 == par and m[y][x] != 0]
            if vals:
                bg[(x, par)] = Counter(vals).most_common(1)[0][0]
        if (x, 0) not in bg and (x, 1) in bg: bg[(x, 0)] = bg[(x, 1)]
        if (x, 1) not in bg and (x, 0) in bg: bg[(x, 1)] = bg[(x, 0)]
    text = set()
    for y in range(H):
        for x in range(W):
            v = m[y][x]
            if v == 0: continue
            b = bg.get((x, y % 2))
            if b is not None and v != b:
                text.add((x, y))
    # 1px 팽창(안티앨리어스 잔여 제거) 후 배경 치환
    dil = {(x+dx, y+dy) for (x, y) in text for dx in (-1,0,1) for dy in (-1,0,1)}
    clean = [row[:] for row in m]
    for (x, y) in dil:
        if 0 <= x < W and 0 <= y < H and m[y][x] != 0:
            b = bg.get((x, y % 2))
            if b is not None:
                clean[y][x] = b
    return clean, text, bg

def typeset_plate(nm, jobs, out_suffix='.kr', fopts=None):
    """jobs: [(cells, 문자열, px[, opts])] opts={'thr':int,'bold':bool,'dark':bool}"""
    orig, g, pal, info = load(nm)
    lum = lambda c: 0.299*c[0]+0.587*c[1]+0.114*c[2]
    for job in jobs:
        cells, s, px = job[0], job[1], job[2]
        opts = dict(fopts or {})
        if len(job) > 3: opts.update(job[3])
        fillmask, outlmask, W, H = make_masks(s, px, opts.get('thr', 128), opts.get('bold', False))
        for ci in cells:
            m = index_map(g, info, ci)
            clean, text, bg = clean_plate(m, fullbg=opts.get('fullbg', False))
            if not text:
                print(f'{nm} cell{ci}: 글자 미검출 스킵'); continue
            palno = (info['cells'][ci]['oams'][0][2] >> 12) & 0xF
            # 배경 밝기: 글자가 실제 덮는 열에서만 (판 테두리 왜곡 배제)
            tcols = {x for (x, y) in text}
            bvals = [v for (x, p), v in bg.items() if x in tcols]
            bgl = sum(lum(pal[palno*16+v]) for v in bvals) / max(1, len(bvals))
            cnt = Counter(m[y][x] for (x, y) in text)
            th = max(20, len(text)//10)
            cand = [v for v, c in cnt.items() if c >= th] or [cnt.most_common(1)[0][0]]
            mx = max(abs(lum(pal[palno*16+v]) - bgl) for v in cand)
            good = [v for v in cand if abs(lum(pal[palno*16+v]) - bgl) >= 0.55*mx]
            if opts.get('dark'):
                good = [min(cand, key=lambda v: lum(pal[palno*16+v]))]
            tc = max(good, key=lambda v: cnt[v])   # 충분히 대비되는 색 중 최다 빈도
            # 듀오톤: 채움과 밝기차 큰 대비색이 또 있으면 밝은쪽=채움, 어두운쪽=외곽선
            oc = None
            duo = [v for v in good if abs(lum(pal[palno*16+v]) - lum(pal[palno*16+tc])) > 60]
            if duo:
                o2 = max(duo, key=lambda v: cnt[v])
                if lum(pal[palno*16+o2]) > lum(pal[palno*16+tc]):
                    tc, oc = o2, tc
                else:
                    oc = o2
            CH, CW = len(clean), len(clean[0])
            xs = [x for y in range(CH) for x in range(CW) if m[y][x] != 0]
            ys = [y for y in range(CH) for x in range(CW) if m[y][x] != 0]
            cx = (min(xs)+max(xs))//2; cy = (min(ys)+max(ys))//2
            x0, y0 = cx - W//2, cy - H//2
            canvas = [row[:] for row in clean]
            if oc is not None:
                for (x, y) in outlmask:
                    X, Y = x0+x, y0+y
                    if 0 <= X < CW and 0 <= Y < CH and canvas[Y][X] != 0:
                        canvas[Y][X] = oc
            for (x, y) in fillmask:
                X, Y = x0+x, y0+y
                if 0 <= X < CW and 0 <= Y < CH and canvas[Y][X] != 0:
                    canvas[Y][X] = tc
            writeback(g, info, ci, canvas)
            ocs = f'{oc:X}' if oc is not None else '-'
            print(f'{nm} cell{ci}: "{s}" 글자픽셀={len(text)} 채움={tc:X} 외곽={ocs} at({x0},{y0})')
    # 미리보기
    n = len(info['cells'])
    im_list = []
    r0 = scmimg.decode(orig)
    for ci in range(n):
        im, _, _ = cncp.render_cell(bytes(g), info['cells'][ci], pal)
        im0, _, _ = cncp.render_cell(r0['gfx'], info['cells'][ci], pal)
        im_list.append((im, im0))
    cw = max(im.width for im, _ in im_list if im) + 6
    ch = max(im.height for im, _ in im_list if im) + 14
    sheet = Image.new('RGB', (n*cw, ch*2), (40, 40, 40))
    dr = ImageDraw.Draw(sheet)
    for ci, (im, im0) in enumerate(im_list):
        if im: sheet.paste(im, (ci*cw+3, 12), im)
        if im0: sheet.paste(im0, (ci*cw+3, ch+12), im0)
        dr.text((ci*cw+3, 0), str(ci), fill=(255, 255, 0))
    sheet = sheet.resize((sheet.width*2, sheet.height*2), Image.NEAREST)
    sheet.save(os.path.join(WORK, f'preview_{nm}.png'))
    new_scm = scmenc.rebuild(orig, bytes(g))
    open(os.path.join(WORK, nm + out_suffix), 'wb').write(new_scm)
    chk = scmimg.decode(new_scm)
    print(f'{nm}: {len(orig)}B -> {len(new_scm)}B 재해제일치={chk["gfx"]==bytes(g)} -> preview_{nm}.png')

JOBS = {
    'FR_BTN2.SCM': [ (list(range(0, 6)), '지우기', 11), (list(range(6, 12)), '종료', 12) ],
    'NACR01_5.SCM': [ (list(range(0, 6)), '지우기', 11), (list(range(6, 12)), '종료', 12) ],
    'FR_BTN.SCM':  [ ([0, 1], '군주명', 11), ([2, 3], '칭호', 12), ([4, 5], '상태', 12) ],
    'KEYCH.SCM':   [ ([0], '터치조작', 10), ([1], '십자버튼조작', 10) ],
    'TIT_OBJ.SCM': [ ([0, 2, 4], '맛보기대전', 18), ([1, 3, 5], '카드도감', 20) ],
    'ED_BOTAN.SCM': [
        ([0], '세력', 10), ([1], '위', 10), ([2], '촉', 10), ([3], '오', 10),
        ([4], '량', 10), ([5], '원', 10), ([6], '기타', 9),
        ([7], '병종', 10), ([8], '보병', 10), ([9], '기병', 10), ([10], '창병', 10),
        ([11], '궁병', 10), ([13], '상병', 10),   # 12(공성병)은 판 끝장식 간섭으로 원본 유지
        ([14], '특기', 10), ([15], '복병', 10), ([16], '부활', 10), ([17], '용맹', 10),
        ([19], '방책', 10), ([20], '매력', 10), ([21], '모병', 10),   # 18(초부활) 원본 유지
        ([22], '연계', 10), ([23], '코스트', 9),
        ([29], '계략', 10), ([30], '강화', 10), ([31], '방해', 10),   # 32(데미지) 원본 유지
        ([33], '지원', 10), ([34], '호령', 10), ([35], '무도', 10), ([36], '기타', 9),
    ],
}
FOPTS = {'ED_BOTAN.SCM': {'bold': True, 'thr': 100, 'dark': True}}
for nm, jobs in JOBS.items():
    typeset_plate(nm, jobs, fopts=FOPTS.get(nm))
