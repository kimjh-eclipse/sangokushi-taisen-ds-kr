# -*- coding: utf-8 -*-
# 한글 2350자 글리프를 ST/STS/OSAKA 폰트에 주입
import os, sys, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
from PIL import Image, ImageFont, ImageDraw
from nftr import NFTR

WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"
MAP = json.load(open(os.path.join(WORK, "hangul_map.json"), encoding="utf-8"))

def render_glyph(font, ch, cw, chh):
    img = Image.new("L", (cw + 8, chh + 8), 0)
    d = ImageDraw.Draw(img)
    d.text((2, 2), ch, fill=255, font=font)
    bbox = img.getbbox()
    if not bbox: return None
    return img, bbox

def build_bitmap(img, bbox, cw, chh, levels):
    """(2,2)이 펜 원점. 원점 기준으로 잘라 cw x chh 격자 생성. top이 3(=pen+1)이면 1px 올림."""
    px = img.load()
    top_ink = bbox[1]
    shift_y = 1 if top_ink >= 3 else 0     # 굴림 12px은 잉크가 pen+1부터 → 1px 올려 한자와 정렬
    grid = [[0] * cw for _ in range(chh)]
    for y in range(chh):
        for x in range(cw):
            v = px[2 + x, 2 + y + shift_y]
            if levels == 1:
                grid[y][x] = 1 if v > 100 else 0
            else:
                grid[y][x] = 3 if v > 100 else 0
    return grid

def inject(nftr_path, out_path, fontsize, cw, chh, bpp, width_tuple):
    f = NFTR(open(os.path.join(WORK, nftr_path), "rb").read())
    gfont = ImageFont.truetype(r"C:\Windows\Fonts\gulim.ttc", fontsize, index=0)
    missing, done = 0, 0
    for ch, code in MAP.items():
        g = f.code2glyph.get(code)
        if g is None:
            missing += 1; continue
        r = render_glyph(gfont, ch, cw, chh)
        if r is None:
            missing += 1; continue
        img, bbox = r
        grid = build_bitmap(img, bbox, cw, chh, 1 if bpp == 1 else 2)
        f.set_glyph_bitmap(g, grid)
        f.set_width(g, *width_tuple)
        done += 1
    open(os.path.join(WORK, out_path), "wb").write(f.bytes())
    print(f"{nftr_path} -> {out_path}: injected={done} missing={missing}")

inject("ST_FONT.nftr", "ST_FONT.kr.nftr", 12, 12, 12, 1, (0, 12, 12))
inject("STS_FONT.nftr", "STS_FONT.kr.nftr", 12, 12, 12, 1, (0, 12, 12))
inject("OSAKA.NFT", "OSAKA.kr.NFT", 11, 10, 11, 2, (0, 10, 10))

# 검증: 주입된 글리프 몇 개 ASCII 출력
from nftr import NFTR as N2
f = N2(open(os.path.join(WORK, "ST_FONT.kr.nftr"), "rb").read())
for ch in ("가", "한", "국", "뷁"):
    code = MAP.get(ch)
    if code is None: print(ch, "not in map"); continue
    g = f.code2glyph[code]
    print(f"\n{ch} (0x{code:x}) glyph {g}:")
    for row in f.get_glyph_bitmap(g):
        print("".join("#" if v else "." for v in row))
