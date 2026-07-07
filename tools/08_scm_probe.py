# -*- coding: utf-8 -*-
# SCM 포맷 분석: 큰 SCM 목록 + 헥스덤프 + 문자열 섹션 탐색
import struct, os, json, sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
import ndspy.rom
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))
sang = bytes(rom.files[rom.filenames.idOf("SANGOKU.NFP")])
toc = json.load(open(os.path.join(BASE, "work", "sangoku_toc.json"), encoding="utf-8"))

scms = [(name, off, sz) for name, off, sz in toc if name.endswith(".SCM")]
scms_sorted = sorted(scms, key=lambda x: -x[2])
print("largest SCMs:")
for name, off, sz in scms_sorted[:15]:
    print(f"  {name}  {sz:,}")

# 이름 패턴 분포
import collections
pref = collections.Counter(re.match(r"[A-Za-z_]*", n).group() for n, _, _ in scms)
print("\nname prefixes:", dict(pref.most_common(30)))

def hexdump(data, off=0, n=0x100, base=0):
    for i in range(off, min(off+n, len(data)), 16):
        row = data[i:i+16]
        hexs = " ".join(f"{b:02x}" for b in row)
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in row)
        print(f"{base+i:08x}  {hexs:<48}  {asc}")

# 대표 SCM 하나 분석 (스토리로 보이는 것)
for target in ("ST_SCN01.SCM", scms_sorted[0][0]):
    for name, off, sz in scms:
        if name == target:
            d = sang[off:off+sz]
            print(f"\n=== {name} ({sz}B) header ===")
            hexdump(d, 0, 0x80)
            # SJIS 가나 포함 문자열 찾기 (실제 대사 판별: 히라가나 필수)
            pat = re.compile(rb"(?:[\x81-\x9f\xe0-\xef][\x40-\xfc]|[\xa1-\xdf]){2,}")
            good = []
            for m in pat.finditer(d):
                try: s = m.group().decode("shift_jis")
                except: continue
                if any("ぁ" <= c <= "ん" for c in s):
                    good.append((m.start(), s))
            print(f"strings w/ hiragana: {len(good)}")
            for o, s in good[:10]:
                print(f"  0x{o:x}: {s[:60]}")
            break
