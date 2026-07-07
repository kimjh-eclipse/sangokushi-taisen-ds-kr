# -*- coding: utf-8 -*-
# 세 폰트 공통 한자 슬롯 계산 + 글리프 메트릭 확인 + 한글 매핑 테이블 생성
import os, sys, json, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
from nftr import NFTR

WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"
fonts = {fn: NFTR(open(os.path.join(WORK, fn), "rb").read())
         for fn in ("ST_FONT.nftr", "STS_FONT.nftr", "OSAKA.NFT")}

# 한자 영역 (1급: 0x889F-0x9FFC, 2급: 0xE040-0xEAA4) 중 공통 코드
def kanji_codes(f):
    return {c for c in f.code2glyph
            if (0x889F <= c <= 0x9FFC or 0xE040 <= c <= 0xEAA4)
            and (c & 0xFF) >= 0x40 and (c & 0xFF) != 0x7F and (c & 0xFF) <= 0xFC}

common = None
for fn, f in fonts.items():
    ks = kanji_codes(f)
    print(f"{fn}: kanji-area codes={len(ks)}")
    common = ks if common is None else (common & ks)
print(f"common: {len(common)}")

# KS X 1001 완성형 한글 2350자 (cp949 B0A1-C8FE 영역)
hangul = []
for lead in range(0xB0, 0xC9):
    for trail in range(0xA1, 0xFF):
        try:
            ch = bytes([lead, trail]).decode("cp949")
            if "가" <= ch <= "힣":
                hangul.append(ch)
        except Exception:
            pass
print(f"KSX1001 hangul: {len(hangul)}")

ok = len(common) >= len(hangul)
print("slots sufficient:", ok)

# 매핑: 한글(가나다순=cp949 순) -> SJIS 코드(오름차순)
codes = sorted(common)[:len(hangul)]
mapping = {ch: code for ch, code in zip(hangul, codes)}
json.dump(mapping, open(os.path.join(WORK, "hangul_map.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("saved hangul_map.json; sample:", list(mapping.items())[:3], "...", list(mapping.items())[-2:])

# 기존 한자 글리프 메트릭 (정렬 참고): ST_FONT의 亜(0x889f)
f = fonts["ST_FONT.nftr"]
g = f.code2glyph[0x889F]
print("\nST_FONT 亜 width:", f.get_width(g))
bmp = f.get_glyph_bitmap(g)
for row in bmp:
    print("".join("#" if v else "." for v in row))
f2 = fonts["OSAKA.NFT"]
g2 = f2.code2glyph[0x889F]
print("OSAKA 亜 width:", f2.get_width(g2))
for row in f2.get_glyph_bitmap(g2):
    print("".join(".#*@"[min(v,3)] for v in row))
