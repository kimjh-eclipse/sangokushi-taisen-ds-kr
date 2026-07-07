# -*- coding: utf-8 -*-
# 1) 천 J vs K: arm9/overlay/banner diff
# 2) 천 K NFP 내부 LZ10 해제 후 한글/RTFN 스캔
import ndspy.rom, ndspy.lz10, os, re, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
romJ = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen Ten (J).nds"))
romK = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen Ten (K).nds"))

def md5(b): return hashlib.md5(b).hexdigest()[:8]

print("=== code/banner diff ===")
for attr in ("arm9", "arm7", "iconBanner"):
    j, k = bytes(getattr(romJ, attr)), bytes(getattr(romK, attr))
    print(f"{attr}: J={len(j)} K={len(k)} {'SAME' if j==k else 'DIFF'}")
for i, (oj, ok) in enumerate(zip(romJ.arm9OverlayTable and [romJ.files[o.fileID] for o in ndspy.code.loadOverlayTable(romJ.arm9OverlayTable, lambda i,s: romJ.files[i]).values()] or [], [])):
    pass  # overlay handling below

import ndspy.code
ovJ = ndspy.code.loadOverlayTable(romJ.arm9OverlayTable, lambda i, s: romJ.files[i])
ovK = ndspy.code.loadOverlayTable(romK.arm9OverlayTable, lambda i, s: romK.files[i])
print(f"overlays: J={len(ovJ)} K={len(ovK)}")
for oid in sorted(ovJ):
    dj = bytes(ovJ[oid].data); dk = bytes(ovK[oid].data) if oid in ovK else b""
    if dj != dk:
        print(f"  overlay {oid}: J={len(dj)} K={len(dk)} DIFF")

# 한글 검출 (CP949 완성형, 3자 이상 & 자주 쓰는 음절 포함해 노이즈 억제)
def find_korean(d):
    out = []
    pat = re.compile(rb"(?:[\xb0-\xc8][\xa1-\xfe]){3,}")
    for m in pat.finditer(d):
        try:
            s = m.group().decode("cp949")
        except: continue
        if all("가" <= c <= "힣" for c in s):
            out.append(s)
    return out

def find_utf16_korean(d):
    out = []
    pat = re.compile(rb"(?:[\x00-\xff][\xac-\xd7]){3,}")
    for m in pat.finditer(d):
        if m.start() % 2: continue
        try: s = m.group().decode("utf-16le")
        except: continue
        if all("가" <= c <= "힣" for c in s): out.append(s)
    return out

# arm9에서 한글 스캔 (비압축 가정; DS arm9는 보통 비압축)
print("\n=== arm9(K) Korean scan ===")
a9 = bytes(romK.arm9)
print("cp949:", find_korean(a9)[:20])
print("utf16:", find_utf16_korean(a9)[:20])

# NFP 내부 LZ10 스트림 해제 스캔
CHANGED = ["battle.NFP","btlnameplate.NFP","commonfile.NFP","scenario.NFP",
           "senryakumode.NFP","SPC.NFP","sysmenu.NFP"]
def lz10_scan(d, label):
    found_kr, found_font = 0, 0
    samples = []
    i = 0
    n = len(d)
    while i < n - 8:
        if d[i] == 0x10:
            size = d[i+1] | (d[i+2] << 8) | (d[i+3] << 16)
            if 0x20 <= size <= 0x200000:
                try:
                    dec = ndspy.lz10.decompress(d[i:i+min(n-i, size*2+64)])
                except Exception:
                    dec = None
                if dec and len(dec) == size:
                    kr = find_korean(bytes(dec))
                    if kr:
                        found_kr += len(kr)
                        samples.extend(kr[:4])
                    if b"RTFN" in dec or b"NFTR" in dec:
                        found_font += 1
                        print(f"  [{label}] FONT in LZ10 at 0x{i:x}!")
                    i += size // 4  # 대충 스킵
                    continue
        i += 1
    if found_kr:
        print(f"  [{label}] Korean in LZ10: {found_kr} strs  e.g. {samples[:10]}")

for p in CHANGED:
    dK = bytes(romK.files[romK.filenames.idOf(p)])
    print(f"--- {p} ---")
    lz10_scan(dK, p)
