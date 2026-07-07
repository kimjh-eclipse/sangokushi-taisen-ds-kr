# -*- coding: utf-8 -*-
# arm9에서 폰트/파일명 참조 검색 + ST_FONT.SCM 구조 확인
import os, sys, re, json, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import ndspy.rom

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))
a9 = bytes(rom.arm9)

for kw in (b"OSAKA", b"FONT", b".NFT", b".SCM", b".DAT", b".sar", b"SANGOKU"):
    hits = [m.start() for m in re.finditer(re.escape(kw), a9)]
    print(f"{kw}: {len(hits)} hits", [hex(h) for h in hits[:10]])
    for h in hits[:6]:
        s = a9[max(0,h-24):h+24]
        print("   ", "".join(chr(b) if 32 <= b < 127 else "." for b in s))

# overlay에서도
import ndspy.code
ov = ndspy.code.loadOverlayTable(rom.arm9OverlayTable, lambda i, s: rom.files[i])
for oid, o in ov.items():
    d = bytes(o.data)
    for kw in (b"OSAKA", b"FONT"):
        hits = [m.start() for m in re.finditer(re.escape(kw), d)]
        if hits:
            print(f"overlay{oid} {kw}: {len(hits)}")
            for h in hits[:6]:
                s = d[max(0,h-24):h+24]
                print("   ", "".join(chr(b) if 32 <= b < 127 else "." for b in s))
