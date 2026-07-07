# -*- coding: utf-8 -*-
# NP_XXXX(무장명 명판) 일괄 한글 식자
#  매핑: CARDS2 col2 = 명판번호(NP_XXXX), 한글 = cd_out CARDS2.name의 {row}_4
#  구조: NP = LZ10(팔레트16) + LZ10(CNCP 1셀, 글자만/투명배경) → 지우고 한글 드로잉
import os, sys, json
from collections import Counter
from PIL import Image, ImageFont, ImageDraw, ImageFilter
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
import ndspy.rom, ndspy.lz10, scmimg, cncp
import struct

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
OUT = os.path.join(WORK, 'np_kr')
os.makedirs(OUT, exist_ok=True)
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
sang = bytes(rom.files[rom.filenames.idOf('SANGOKU.NFP')])
toc = json.load(open(os.path.join(WORK, 'sangoku_toc.json'), encoding='utf-8'))
files = {n: (o, s) for n, o, s in toc}

# ---- 매핑 구축 ----
off, sz = files['CARDS2.DAT']
d = sang[off:off+sz]
nl = b'\r\n' if b'\r\n' in d else b'\n'
rows = [ln.split(b',') for ln in d.split(nl)]
ko = json.load(open(os.path.join(WORK, 'cd_out', 'CARDS2.DAT.name.json'), encoding='utf-8'))
npmap = {}   # np_id -> (row, kanji, korean)
for ri, r in enumerate(rows):
    if len(r) < 5: continue
    kanji = r[4].decode('cp932', errors='replace')
    kor = ko.get(f'{ri}_4', '')
    if not kor: continue
    ids = []
    if r[0].isdigit() and int(r[0]) > 0: ids.append(int(r[0]))   # col0 = 카드ID
    if r[2].isdigit() and int(r[2]) > 0: ids.append(int(r[2]))   # col2 = 별쇄 명판
    for np_id in ids:
        if np_id in npmap and npmap[np_id][2] != kor:
            print(f'경고: NP{np_id} 충돌 {npmap[np_id][2]} vs {kor}')
        npmap[np_id] = (ri, kanji, kor)
print(f'명판 매핑 {len(npmap)}개 (min {min(npmap)}, max {max(npmap)})')
have = [i for i in npmap if f'NP_{i:04d}.SCM' in files]
print(f'NP 파일 존재 {len(have)}개')

def make_masks(s, px, bold=True, thr=110):
    font = ImageFont.truetype(r'C:\Windows\Fonts\gulim.ttc', px)
    img = Image.new('L', (px*len(s)*2+8, px*2+8), 0)
    dr = ImageDraw.Draw(img)
    dr.text((4, 4), s, fill=255, font=font)
    if bold:
        dr.text((5, 4), s, fill=255, font=font)
    img = img.point(lambda v: 255 if v >= thr else 0)
    bb = img.getbbox()
    if bb is None: return None
    img = img.crop(bb).transpose(Image.ROTATE_270)
    dil = img.filter(ImageFilter.MaxFilter(3))
    W, H = img.size
    fill = {(x, y) for y in range(H) for x in range(W) if img.getpixel((x, y))}
    outl = {(x, y) for y in range(H) for x in range(W)
            if dil.getpixel((x, y)) and (x, y) not in fill}
    return fill, outl, W, H

def _gray_scaled(s, target_h, max_w, srcpx, bold):
    font = ImageFont.truetype(r'C:\Windows\Fonts\gulim.ttc', srcpx)
    img = Image.new('L', (srcpx*len(s)*2+16, srcpx*3), 0)
    dr = ImageDraw.Draw(img)
    dr.text((8, 8), s, fill=255, font=font)
    if bold: dr.text((9, 8), s, fill=255, font=font)
    bb = img.getbbox()
    if bb is None: return None
    img = img.crop(bb)
    w0, h0 = img.size
    nw = min(max_w, max(1, round(w0 * target_h / h0)))
    return img.resize((nw, target_h), Image.LANCZOS)

def make_masks_scaled(s, target_h, max_w):
    """굴림 최소크기(11px)보다 작은 캔버스용: 슈퍼샘플 → LANCZOS 축소 → 재이진화.
    (srcpx, bold, thr) 후보를 고해상 참조 마스크와의 F1로 채점해 이름별 최적안 선택.
    크롭으로 획을 깎지 않으므로 글자 상단 잘림이 없다. 외곽선 없음(공간 부족)."""
    font = ImageFont.truetype(r'C:\Windows\Fonts\gulim.ttc', 32)
    ref = Image.new('L', (32*len(s)*2+16, 96), 0)
    ImageDraw.Draw(ref).text((8, 8), s, fill=255, font=font)
    bb = ref.getbbox()
    if bb is None: return None
    ref = ref.crop(bb).point(lambda v: 255 if v >= 128 else 0)
    rp = ref.load()
    best = None; bestF1 = -1.0
    for srcpx, bold in ((32, True), (32, False), (16, False), (12, False), (11, False)):
        g = _gray_scaled(s, target_h, max_w, srcpx, bold)
        if g is None: continue
        for thr in (80, 100, 118, 140):
            b = g.point(lambda v: 255 if v >= thr else 0)
            up = b.resize(ref.size, Image.NEAREST)
            upx = up.load()
            tp = fp = fn = 0
            for y in range(0, ref.size[1], 2):     # 2px 스트라이드 샘플링
                for x in range(0, ref.size[0], 2):
                    r_ = rp[x, y] > 0; u_ = upx[x, y] > 0
                    if r_ and u_: tp += 1
                    elif u_: fp += 1
                    elif r_: fn += 1
            f1 = 2*tp / (2*tp + fp + fn) if tp else 0.0
            if f1 > bestF1:
                bestF1, best = f1, b
    img = best.transpose(Image.ROTATE_270)
    W, H = img.size
    fill = {(x, y) for y in range(H) for x in range(W) if img.getpixel((x, y))}
    return fill, set(), W, H

def luma(c): return 0.299*c[0]+0.587*c[1]+0.114*c[2]

def cell_geom(info, ci):
    c = info['cells'][ci]
    xs=ys=999; x1=y1=-999
    for a0,a1,a2 in c['oams']:
        sh=(a0>>14)&3; szv=(a1>>14)&3
        w,h = cncp.OBJ_SIZES[(sh,szv)]
        x=cncp.sgn(a1&0x1FF,9); y=cncp.sgn(a0&0xFF,8)
        xs=min(xs,x); ys=min(ys,y); x1=max(x1,x+w); y1=max(y1,y+h)
    return xs,ys,x1-xs,y1-ys

def rebuild_np(orig, new_gfx):
    """NP형 MC 재조립: 헤더+LZ10팔레트 원본 유지, u16[3] 오프셋까지 0패딩, gfx LZ10 재압축"""
    h = struct.unpack_from('<8H', orig, 0)
    gofs = h[3]
    out = bytearray(orig[:gofs])          # 헤더+팔레트+패딩 그대로
    comp = ndspy.lz10.compress(bytes(new_gfx))
    out += comp
    while len(out) % 4: out += b'\x00'
    return bytes(out)

# 공용 팔레트 (NPS 계열용)
off0, sz0 = files['NPSCOL.SCM']
NPSPAL = scmimg.pal_to_rgb(sang[off0+0x20:off0+0x20+32])

jobs = []
for np_id in sorted(have):
    jobs.append((f'NP_{np_id:04d}.SCM', np_id, 0))
for np_id in sorted(npmap):
    nm = f'NPS_{np_id:04d}.SCM'
    if nm in files:
        jobs.append((nm, np_id, 1))
print(f'작업 {len(jobs)}건 (NP+NPS)')

done = skip = 0
fails = []
for nm, np_id, small in jobs:
    ri, kanji, kor = npmap[np_id]
    off, sz = files[nm]
    orig = sang[off:off+sz]
    try:
        r = scmimg.decode(orig)
        g = bytearray(r['gfx'])
        assert g[:4] == b'CNCP'
        info = cncp.parse(g)
        pal = scmimg.pal_to_rgb(r['pal']) if r['pal'] else NPSPAL
        # 셀0 캔버스와 원본 글자색
        xs, ys, W, H = cell_geom(info, 0)
        # 원본 픽셀 인덱스 히스토그램 (글자만)
        cnt = Counter()
        cell = info['cells'][0]
        for a0, a1, a2 in cell['oams']:
            sh=(a0>>14)&3; szv=(a1>>14)&3
            w,hh = cncp.OBJ_SIZES[(sh,szv)]
            t=a2&0x3FF
            for ti in range(t, t+(w//8)*(hh//8)):
                base = cell['gfxBase'] + ti*32
                for b in g[base:base+32]:
                    if b & 0xF: cnt[b & 0xF] += 1
                    if b >> 4: cnt[b >> 4] += 1
        cand = [v for v, n in cnt.items() if n >= 8] or list(cnt)
        fi = max(cand, key=lambda v: luma(pal[v]))
        oi = min(cand, key=lambda v: luma(pal[v]))
        # 한글 마스크 — 굴림은 10px 이하 렌더 결손 → 최소 11px 유지
        # NPS(소형, 캔버스 8px)는 크롭 시 글자 상단 잘림 → 슈퍼샘플 축소 방식
        if small:
            mk = make_masks_scaled(kor, W, H)
            if mk is None: raise ValueError('마스크 없음')
            fill, outl, mw, mh = mk
        else:
            px, bold, thr = (12 if len(kor) <= 3 else 11), True, 110
            mk = make_masks(kor, px, bold, thr)
            if mk is None: raise ValueError('마스크 없음')
            fill, outl, mw, mh = mk
            if mw > W and px > 11:
                mk = make_masks(kor, 11, bold, thr)
                fill, outl, mw, mh = mk
            if mw > W and bold:
                mk = make_masks(kor, px, False, thr)
                fill, outl, mw, mh = mk
            if mw > W:
                # 그래도 초과 → 크롭 대신 축소 (획 잘림 방지)
                mk = make_masks_scaled(kor, W, H)
                fill, outl, mw, mh = mk
        x0 = (W - mw)//2
        y0 = max(0, (H - mh)//2)
        # 캔버스 = 전부 투명에서 드로잉
        canvas = [[0]*W for _ in range(H)]
        for (x, y) in outl:
            X, Y = x0+x, y0+y
            if 0 <= X < W and 0 <= Y < H: canvas[Y][X] = oi
        for (x, y) in fill:
            X, Y = x0+x, y0+y
            if 0 <= X < W and 0 <= Y < H: canvas[Y][X] = fi
        # 타일 재기록
        for a0, a1, a2 in cell['oams']:
            sh=(a0>>14)&3; szv=(a1>>14)&3
            w,hh = cncp.OBJ_SIZES[(sh,szv)]
            x=cncp.sgn(a1&0x1FF,9)-xs; y=cncp.sgn(a0&0xFF,8)-ys
            t=a2&0x3FF
            for ty in range(hh//8):
                for tx in range(w//8):
                    tofs = cell['gfxBase'] + (t+ty*(w//8)+tx)*32
                    for yy in range(8):
                        for xx in range(0, 8, 2):
                            lo = canvas[y+ty*8+yy][x+tx*8+xx]&0xF
                            hi = canvas[y+ty*8+yy][x+tx*8+xx+1]&0xF
                            g[tofs+yy*4+xx//2] = lo|(hi<<4)
        new = rebuild_np(orig, g)
        chk = scmimg.decode(new)
        assert chk['gfx'] == bytes(g), '왕복 불일치'
        open(os.path.join(OUT, nm), 'wb').write(new)
        done += 1
    except Exception as e:
        fails.append((nm, kor, str(e)))
print(f'완료 {done}, 실패 {len(fails)}')
for nm, kor, e in fails[:10]:
    print(' 실패:', nm, kor, e)
