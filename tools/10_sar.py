# -*- coding: utf-8 -*-
# scenario.sar 구조 분석
import struct, os, sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import ndspy.rom

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))
sar = bytes(rom.files[rom.filenames.idOf("scenario.sar")])

# 테이블: (offset, size) 쌍 반복으로 추정. 첫 데이터 시작 = 0x370
pairs = []
p = 0
while p + 8 <= len(sar):
    off, sz = struct.unpack_from("<II", sar, p)
    if off == 0x370 and p == 0:
        pass
    pairs.append((off, sz))
    p += 8
    if off + sz > len(sar) or (pairs and p >= pairs[0][0]):
        break
# 첫 엔트리 off=0x370이므로 테이블은 0x370/8 = 110개
n = pairs[0][0] // 8
pairs = pairs[:n]
print(f"entries={n}")
ok = all(off + sz <= len(sar) for off, sz in pairs)
print(f"bounds ok: {ok}")
# 연속성 확인
for i in range(1, min(n, 8)):
    print(f"  e{i-1}: off=0x{pairs[i-1][0]:x} sz=0x{pairs[i-1][1]:x} end=0x{pairs[i-1][0]+pairs[i-1][1]:x} next=0x{pairs[i][0]:x}")

def hexdump(data, off=0, nb=0x100, base=0):
    for i in range(off, min(off+nb, len(data)), 16):
        row = data[i:i+16]
        hexs = " ".join(f"{b:02x}" for b in row)
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in row)
        print(f"{base+i:08x}  {hexs:<48}  {asc}")

# 엔트리 0 (튜토리얼 텍스트 포함, 0x370+0x366) 전체 구조 보기
e0 = sar[pairs[0][0]:pairs[0][0]+pairs[0][1]]
print(f"\n=== entry0 (0x{pairs[0][1]:x}B) ===")
hexdump(e0, 0, 0x120, base=pairs[0][0])
print("...")
hexdump(e0, 0x150, 0xb0, base=pairs[0][0])
