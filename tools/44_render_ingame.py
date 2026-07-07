# -*- coding: utf-8 -*-
# 주입된 ST_FONT.kr 글리프를 그대로 꺼내 튜토리얼 대사를 "게임과 동일하게" 렌더
# (게임은 이 글리프를 그대로 blit하므로 결과가 화면과 픽셀 동일)
import os, sys
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import Image
from nftr import NFTR
import korean

WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"
f = NFTR(open(os.path.join(WORK, "ST_FONT.kr.nftr"), "rb").read())

def draw_text(lines, scale=3, pad=4, line_gap=3):
    cw, ch = f.cellW, f.cellH
    maxchars = max(len(l) for l in lines)
    W = pad * 2 + maxchars * cw
    Hh = pad * 2 + len(lines) * (ch + line_gap)
    img = Image.new("RGB", (W, Hh), (245, 240, 225))
    px = img.load()
    for li, line in enumerate(lines):
        # 한국어 문자열을 게임 코드로 변환 후, 코드→글리프로 렌더
        enc = korean.encode(line)
        # 2바이트/1바이트 파싱
        codes = []
        i = 0
        while i < len(enc):
            if enc[i] < 0x80:
                codes.append(enc[i]); i += 1
            else:
                codes.append((enc[i] << 8) | enc[i+1]); i += 2
        x0 = pad
        y0 = pad + li * (ch + line_gap)
        for code in codes:
            g = f.code2glyph.get(code)
            if g is None:
                x0 += cw; continue
            bmp = f.get_glyph_bitmap(g)
            for y in range(ch):
                for x in range(cw):
                    if bmp[y][x]:
                        px[x0 + x, y0 + y] = (30, 20, 15)
            x0 += cw
    img = img.resize((W * scale, Hh * scale), Image.NEAREST)
    return img

# 튜토리얼 대사 (38_build_poc.py의 TUTORIAL과 동일)
lines = [
    "군사", "주군니이이이임!", "기다리고 있었습니다",
    "단도직입적으로, 주군께서는", "이 삼국지대전DS",
    "즐기는 법을 알고", "계십니까?",
    "만약 즐기는 법이나 규칙을", "모르시겠다면,",
    "튜토리얼로 와 주십시오.",
    "불초하오나 소인이 차근차근", "기초 중의 기초부터",
    "가르쳐 드리겠습니다.",
]
img = draw_text(lines)
img.save(os.path.join(WORK, "ingame_render.png"))
print("saved ingame_render.png", img.size)
