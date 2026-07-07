# -*- coding: utf-8 -*-
# scenario.sar / arm9 / 작은 SCM 분석
import struct, os, json, sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import ndspy.rom

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))

def hexdump(data, off=0, n=0x100, base=0):
    for i in range(off, min(off+n, len(data)), 16):
        row = data[i:i+16]
        hexs = " ".join(f"{b:02x}" for b in row)
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in row)
        print(f"{base+i:08x}  {hexs:<48}  {asc}")

def sjis_dialogue(d, minlen=4):
    pat = re.compile(rb"(?:[\x81-\x9f\xe0-\xef][\x40-\xfc]){%d,}" % minlen)
    out = []
    for m in pat.finditer(d):
        try: s = m.group().decode("shift_jis")
        except: continue
        if any("ぁ" <= c <= "ん" for c in s):
            out.append((m.start(), s))
    return out

# 1) scenario.sar
sar = bytes(rom.files[rom.filenames.idOf("scenario.sar")])
print(f"=== scenario.sar ({len(sar)}B) ===")
hexdump(sar, 0, 0x80)
dia = sjis_dialogue(sar)
print(f"dialogue strings: {len(dia)}")
for o, s in dia[:15]: print(f"  0x{o:x}: {s[:70]}")

# 2) arm9
a9 = bytes(rom.arm9)
print(f"\n=== arm9 ({len(a9)}B) ===")
dia = sjis_dialogue(a9, 3)
print(f"dialogue strings: {len(dia)}")
for o, s in dia[:30]: print(f"  0x{o:x}: {s[:70]}")

# 3) 작은 SCM들 덤프
sang = bytes(rom.files[rom.filenames.idOf("SANGOKU.NFP")])
toc = json.load(open(os.path.join(BASE, "work", "sangoku_toc.json"), encoding="utf-8"))
for tgt in ("000.SCM",):
    for name, off, sz in toc:
        if name == tgt:
            print(f"\n=== {name} ({sz}B) ===")
            hexdump(sang[off:off+sz], 0, 0xc0)

# 4) M04_P001.SCM 등 스토리 후보 헤더 비교
hdrs = {}
for name, off, sz in toc:
    if name.endswith(".SCM"):
        h = sang[off:off+4]
        hdrs.setdefault(h, [0, name])[0] = hdrs.get(h, [0])[0] + 1 if h in hdrs else 1
import collections
c = collections.Counter(sang[off:off+2].hex() for name, off, sz in toc if name.endswith(".SCM"))
print("\nSCM first-2-bytes distribution:", dict(c.most_common(10)))
c4 = collections.Counter(sang[off+2:off+4].hex() for name, off, sz in toc if name.endswith(".SCM"))
print("SCM bytes[2:4] distribution:", dict(c4.most_common(10)))
