# -*- coding: utf-8 -*-
# ST_FONT/STS_FONT 해제 데이터를 다양한 포맷으로 시각화
import os, sys
from PIL import Image
WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"

def render(data, name, bpp, gw, gh, start=0, count=256, cols=16):
    gsize = gw * gh * bpp // 8
    rows = (count + cols - 1) // cols
    img = Image.new("L", (cols * (gw + 1), rows * (gh + 1)), 255)
    px = img.load()
    for gi in range(count):
        off = start + gi * gsize
        if off + gsize > len(data): break
        gx, gy = (gi % cols) * (gw + 1), (gi // cols) * (gh + 1)
        for y in range(gh):
            for x in range(gw):
                bit = y * gw + x
                if bpp == 1:
                    v = (data[off + bit // 8] >> (bit % 8)) & 1
                    c = 0 if v else 255
                elif bpp == 2:
                    b = data[off + bit // 4]
                    v = (b >> ((bit % 4) * 2)) & 3
                    c = 255 - v * 85
                else:  # 4bpp
                    b = data[off + bit // 2]
                    v = (b >> ((bit % 2) * 4)) & 0xF
                    c = 255 - v * 17
                px[gx + x, gy + y] = c
    img = img.resize((img.width * 3, img.height * 3), Image.NEAREST)
    img.save(os.path.join(WORK, f"viz_{name}.png"))
    print("saved", f"viz_{name}.png")

d = open(os.path.join(WORK, "ST_FONT.SCM.dec"), "rb").read()
ds = open(os.path.join(WORK, "STS_FONT.SCM.dec"), "rb").read()

# 뒤쪽(한자, 밀집) 영역과 앞쪽 모두
for bpp in (1, 2):
    for gw, gh in ((8, 8), (12, 12), (16, 16), (10, 10), (12, 11), (16, 12)):
        gsize = gw * gh * bpp // 8
        render(d, f"L_{bpp}bpp_{gw}x{gh}_tail", bpp, gw, gh, start=(len(d) // 2 // gsize) * gsize, count=128)
render(d, "L_2bpp_12x12_head", 2, 12, 12, start=0, count=256)
render(d, "L_1bpp_16x16_head", 1, 16, 16, start=0, count=256)
render(ds, "S_2bpp_12x12_tail", 2, 12, 12, start=(len(ds)//2//36)*36, count=128)
render(ds, "S_1bpp_8x16_tail", 1, 8, 16, start=len(ds)//2//16*16, count=128)
render(ds, "S_2bpp_8x8_tail", 2, 8, 8, start=len(ds)//2//16*16, count=128)
