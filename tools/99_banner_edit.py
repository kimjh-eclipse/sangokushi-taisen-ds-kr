# -*- coding: utf-8 -*-
# 모드선택 배너 한글 식자 2단계: 상태별 화면(인덱스) 편집 → 미리보기 (쓰기 전 검수용)
#  rest(state1): 텍스트{49,51,54} → 56 소거 후 한글(채움49, AA51)
#  popped(state2-6): 텍스트{62,63}+외곽{49,50,51,54} → raw열별 배경 모드로 소거 후 한글(채움63, 외곽49)
import sys, os, json
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Emul\Switch\패치유틸.xdeltaUI\work')
from PIL import Image, ImageFont, ImageDraw, ImageFilter

WORK = r'C:\Emul\Switch\패치유틸.xdeltaUI\work'
OUT = os.path.join(WORK, 'banner')
pal = json.load(open(os.path.join(OUT, 'pal.json')))

# 배너 정의: (상태, 이름, 한글, raw x0, x1)  — rest는 전부 state1
REST = [('튜토리얼', 28, 54), ('군의', 72, 106), ('통신의 장', 110, 140),
        ('단련의 장', 146, 176), ('삼국영걸전', 186, 216)]
POP = {2: ('삼국영걸전', 184, 220), 3: ('단련의 장', 144, 180),
       4: ('통신의 장', 108, 142), 5: ('군의', 60, 108), 6: ('튜토리얼', 24, 60)}

TXT_REST = {49, 51, 54}
NUDGE = {}
BLOCK_CELLS = set()   # 공유타일 셀: 드로잉 금지(1px 열 손실)   # 공유타일 셀 회피
TXT_POP = {62, 63, 49, 50, 51, 54}
# 팝업 수동 슬롯 (state: [(py, px0)×글자]) — 편집가능 지도 기반, 공유타일 회피
POP_OVERRIDE = {3: [(42,157),(58,157),(90,157),(106,157)],
                6: [(74,37),(120,37),(136,37),(152,37)]}

def mask_h(s, px, bold=True, thr=128):
    """가로 텍스트 이진 마스크 → ROTATE_270(raw 세로 방향) (fill, outline, W, H)"""
    font = ImageFont.truetype(r'C:\Windows\Fonts\gulim.ttc', px)
    img = Image.new('L', (px*len(s)*2+12, px*3), 0)
    dr = ImageDraw.Draw(img)
    dr.text((6, 6), s, fill=255, font=font)
    if bold: dr.text((7, 6), s, fill=255, font=font)
    img = img.point(lambda v: 255 if v >= thr else 0)
    bb = img.getbbox()
    img = img.crop(bb).transpose(Image.ROTATE_270)
    dil = img.filter(ImageFilter.MaxFilter(3))
    W, H = img.size
    fill = {(x, y) for y in range(H) for x in range(W) if img.getpixel((x, y))}
    outl = {(x, y) for y in range(H) for x in range(W)
            if dil.getpixel((x, y)) and (x, y) not in fill}
    return fill, outl, W, H

def edit_rest(idx, editable):
    """state1 (5개 배너). 소거=열별 최빈 복원, 드로잉·소거 모두 편집가능 셀만."""
    changed = set()
    for label, x0, x1 in REST:
        pts = [(x, y) for y in range(256) for x in range(x0, x1)
               if idx[y][x] in TXT_REST]
        if not pts:
            print(f'rest {label}: 텍스트 없음?!'); continue
        ys = [p[1] for p in pts]
        ymin, ymax = min(ys), max(ys)
        # 열별 최빈 배경 (스트립 전체 길이 기준)
        colbg = {}
        for x in range(x0, x1):
            cnt = Counter(idx[y][x] for y in range(256) if idx[y][x])
            colbg[x] = cnt.most_common(1)[0][0] if cnt else 0
        clipped_e = 0
        for y in range(ymin, ymax+1):
            for x in range(x0, x1):
                if idx[y][x] in (49, 50, 51, 54) and colbg[x]:
                    ci = (y//8)*32 + x//8
                    if ci not in editable:
                        clipped_e += 1; continue
                    idx[y][x] = colbg[x]
                    changed.add(ci)
        body_x = [x for x in range(x0, x1) if colbg.get(x) == 56]
        bx0, bx1 = min(body_x), max(body_x)
        clipped_d = drawn = 0
        if label == '튜토리얼':
            # 편집가능(유니크 타일) 행에 수동 슬롯 배치: px0=40(셀 x5-6), y13·17·19행 회피
            SLOT_Y = [121, 145, 157, 169]
            parts = []
            for i, chs in enumerate(label):
                f1, o1, w1, h1 = mask_h(chs, 12, bold=True)
                parts.append((f1, w1, h1, SLOT_Y[i]))
            mw = max(w1 for _, w1, _, _ in parts)
            px0 = 40
            for f1, w1, h1, py in parts:
                dx = (mw - w1) // 2
                for (x, y) in f1:
                    X, Y = px0 + dx + x, py + y
                    if not (0 <= X < 256 and 0 <= Y < 256): continue
                    ci = (Y//8)*32 + X//8
                    if ci in BLOCK_CELLS:
                        clipped_d += 1; continue
                    if idx[Y][X] in (56, 60):
                        idx[Y][X] = 49
                        changed.add(ci); drawn += 1
            print(f'rest {label}: 글자별 슬롯 y{ymin}-{ymax} 드로잉{drawn} 클립{clipped_d}')
            continue
        fill, outl, mw, mh = mask_h(label, 12, bold=True)
        px0 = bx0 + (bx1 - bx0 + 1 - mw)//2 + NUDGE.get(label, 0)
        py0 = ymin + (1 if ymin % 8 >= 6 else 0)
        for (x, y) in fill:
            X, Y = px0 + x, py0 + y
            if not (0 <= X < 256 and 0 <= Y < 256): continue
            ci = (Y//8)*32 + X//8
            if ci not in editable or ci in BLOCK_CELLS:
                clipped_d += 1; continue
            if idx[Y][X] in (56, 60):
                idx[Y][X] = 49
                changed.add(ci); drawn += 1
        print(f'rest {label}: y{ymin}-{ymax} 마스크 {mw}x{mh} @({px0},{py0}) '
              f'드로잉{drawn} 클립(소거{clipped_e}/드로잉{clipped_d})')
    return changed

def edit_pop(idx, label, x0, x1, editable, state=None):
    """플레이트=가로 밴드(raw 열별 상수). 열별 최빈값(colbg)과 다른 픽셀 = 텍스트/장식.
    한글은 글자별로 원문 글자 슬롯 위치에 배치하고, 편집가능(비공유 타일) 셀에만 드로잉."""
    changed = set()
    ys_nz = [y for y in range(256) if any(idx[y][x] for x in range(x0, x1))]
    yb0, yb1 = min(ys_nz), max(ys_nz)
    xs_nz = [x for x in range(x0, x1) if any(idx[y][x] for y in range(yb0, yb1+1))]
    bx0, bx1 = min(xs_nz), max(xs_nz)
    colbg = {}
    for x in range(bx0, bx1+1):
        cnt = Counter(idx[y][x] for y in range(yb0, yb1+1) if idx[y][x])
        colbg[x] = cnt.most_common(1)[0][0] if cnt else 0
    ty0, ty1 = yb0 + 13, yb1 - 7
    # 글자 슬롯: 흰색(62/63) 픽셀 행 클러스터 (끝단 장식은 흰색 아님 → 제외됨)
    wrow = [y for y in range(ty0, ty1+1)
            if sum(1 for x in range(bx0, bx1+1) if idx[y][x] in (62, 63)) >= 2]
    clusters = []
    for y in wrow:
        if clusters and y - clusters[-1][1] <= 4: clusters[-1][1] = y
        else: clusters.append([y, y])
    ts0, ts1 = wrow[0], wrow[-1]
    # 소거: 텍스트 스팬 ±3 내, 편집가능 셀만
    clipped_e = 0
    for y in range(max(ty0, ts0-3), min(ty1, ts1+3)+1):
        for x in range(bx0, bx1+1):
            if idx[y][x] and colbg[x] and idx[y][x] != colbg[x]:
                ci = (y//8)*32 + x//8
                if ci not in editable:
                    clipped_e += 1; continue
                idx[y][x] = colbg[x]
                changed.add(ci)
    # 글자별 슬롯 배치 (원문 스팬을 글자 수로 균등 분할)
    body = [x for x in range(bx0, bx1+1) if colbg[x] and colbg[x] < 62]
    ix0, ix1 = min(body), max(body)
    chars = [c for c in label if c != ' ']
    n = len(chars)
    span = ts1 - ts0 + 1
    # 클러스터 수 == 글자 수면 1:1 슬롯, 아니면 스팬 균등 분할
    if len(clusters) == n:
        slots = [(a + b) // 2 for a, b in clusters]
    else:
        slots = [ts0 + int((i + 0.5) * span / n) for i in range(n)]
    clipped = drawn = 0
    ovr = POP_OVERRIDE.get(state)
    for i, chs in enumerate(chars):
        fill, outl, mw, mh = mask_h(chs, 16, bold=True)
        if ovr:
            py0, px0 = ovr[i]
        else:
            cy = slots[i]
            py0 = max(ty0, cy - mh // 2)
            px0 = ix0 + (ix1 - ix0 + 1 - mw) // 2
        for pts, col in ((outl, 49), (fill, 63)):
            for (x, y) in pts:
                X, Y = px0 + x, py0 + y
                if not (ix0 <= X <= ix1 and ty0 <= Y <= ty1):
                    continue
                ci = (Y//8)*32 + X//8
                if ci not in editable:
                    clipped += 1
                    continue
                idx[Y][X] = col
                changed.add(ci)
                drawn += 1
    print(f'pop {label}: bbox x{bx0}-{bx1}, 텍스트스팬 y{ts0}-{ts1}, 드로잉 {drawn}px 클립 {clipped}px')
    return changed

def render(idx, path):
    img = Image.new('RGB', (256, 256), (255, 0, 255))
    px = img.load()
    for y in range(256):
        for x in range(256):
            v = idx[y][x]
            if v: px[x, y] = tuple(pal[v])
    img.transpose(Image.ROTATE_90).resize((512, 512), Image.NEAREST).save(path)

if __name__ == '__main__':
    cellmaps = json.load(open(os.path.join(OUT, 'cellmaps.json')))
    # 타일 → 등장 셀 집합 (전 상태) → 비공유(단일 위치) 타일의 셀만 편집 가능
    occ = {}
    for k in map(str, range(1, 7)):
        for ci, (t, hf, vf, p) in cellmaps[k].items():
            occ.setdefault(t, set()).add(int(ci))
    editable_by_state = {}
    for k in map(str, range(1, 7)):
        editable_by_state[k] = {int(ci) for ci, (t, hf, vf, p) in cellmaps[k].items()
                                if occ[t] == {int(ci)}}
        print(f'state{k}: 편집가능 셀 {len(editable_by_state[k])}/{len(cellmaps[k])}')
    all_changed = {}
    idx1 = json.load(open(os.path.join(OUT, 'state1_idx.json')))
    ch = edit_rest(idx1, set(range(1024)))  # rest는 위상정렬로 공유타일 일관 → 클립 불필요
    render(idx1, os.path.join(OUT, 'edit1.png'))
    json.dump(idx1, open(os.path.join(OUT, 'edit1_idx.json'), 'w'))
    all_changed['1'] = sorted(ch)
    for k, (label, x0, x1) in POP.items():
        idxk = json.load(open(os.path.join(OUT, f'state{k}_idx.json')))
        ch = edit_pop(idxk, label, x0, x1, editable_by_state[str(k)], state=k)
        render(idxk, os.path.join(OUT, f'edit{k}.png'))
        json.dump(idxk, open(os.path.join(OUT, f'edit{k}_idx.json'), 'w'))
        all_changed[str(k)] = sorted(ch)
    json.dump(all_changed, open(os.path.join(OUT, 'changed_cells.json'), 'w'))
    print('미리보기 저장: edit1-6.png')
