# -*- coding: utf-8 -*-
# 후보 폰트별 12px 한글 렌더 품질 비교 (ASCII 아트)
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import Image, ImageFont, ImageDraw

CANDS = [
    (r"C:\Windows\Fonts\gulim.ttc", 0, "Gulim"),
    (r"C:\Windows\Fonts\gulim.ttc", 1, "GulimChe"),
    (r"C:\Windows\Fonts\gulim.ttc", 2, "Dotum"),
    (r"C:\Windows\Fonts\batang.ttc", 0, "Batang"),
    (r"C:\Windows\Fonts\malgun.ttf", 0, "Malgun"),
]

def render(fontpath, idx, ch, size, cw=12, chh=12, thresh=128):
    try:
        font = ImageFont.truetype(fontpath, size, index=idx)
    except Exception as e:
        return None, str(e)
    img = Image.new("L", (cw * 2, chh * 2), 0)
    d = ImageDraw.Draw(img)
    d.text((0, 0), ch, fill=255, font=font)
    bbox = img.getbbox()
    if not bbox: return None, "empty"
    g = img.crop(bbox)
    return g, f"bbox={bbox} size={g.size}"

for path, idx, name in CANDS:
    for sz in (12, 11):
        g, info = render(path, idx, "한", sz)
        if g is None:
            print(f"{name}@{sz}: {info}"); continue
        print(f"\n=== {name}@{sz} {info}")
        w, h = g.size
        px = g.load()
        for y in range(min(h, 14)):
            print("".join("#" if px[x, y] > 128 else ("+" if px[x, y] > 40 else ".") for x in range(min(w, 14))))
