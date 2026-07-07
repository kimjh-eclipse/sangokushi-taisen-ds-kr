# -*- coding: utf-8 -*-
# "ST_FONT.SCM" 문자열 참조 코드 추적
# arm9 로드 주소 확인 후, 문자열 주소를 리터럴 풀에서 찾아 참조 함수 디스어셈블
import os, sys, struct, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import ndspy.rom
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))
a9 = bytes(rom.arm9)
ram = rom.arm9RamAddress
print(f"arm9 RAM base=0x{ram:x} entry=0x{rom.arm9EntryAddress:x} len={len(a9)}")

# 문자열 "ST_FONT.SCM" 위치 (파일 오프셋 0x1369ff 부근에서 정확히)
soff = a9.find(b"ST_FONT.SCM\0")
print(f"ST_FONT.SCM str at file+0x{soff:x} = RAM 0x{ram+soff:x}")
target = ram + soff

# 리터럴 풀에서 이 주소를 담은 워드 검색
refs = []
for i in range(0, len(a9) - 3, 4):
    v, = struct.unpack_from("<I", a9, i)
    if v == target:
        refs.append(i)
print("literal refs:", [hex(r) for r in refs], [hex(ram+r) for r in refs])

# STS_FONT도
soff2 = a9.find(b"STS_FONT.SCM\0")
if soff2 >= 0:
    t2 = ram + soff2
    refs2 = [i for i in range(0, len(a9)-3, 4) if struct.unpack_from("<I", a9, i)[0] == t2]
    print(f"STS_FONT str at 0x{soff2:x}, refs:", [hex(r) for r in refs2])

md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
md.detail = False

def disasm_around(foff, before=0x60, after=0x40, label=""):
    start = (foff - before) & ~3
    code = a9[start:foff+after]
    print(f"\n--- {label} disasm around file+0x{foff:x} (RAM 0x{ram+foff:x}) ---")
    for ins in md.disasm(code, ram + start):
        mark = " <<<" if ins.address == ram + foff else ""
        print(f"  {ins.address:08x}  {ins.mnemonic:<8} {ins.op_str}{mark}")

# 각 리터럴 참조에 대해: 이 리터럴을 ldr로 읽는 코드 검색 (pc-relative)
for r in refs:
    lit_ram = ram + r
    # ldr rX, [pc, #imm] : imm = lit - (pc+8),  검색 범위: 리터럴 앞 0x1000
    for i in range(max(0, r - 0x1000), r, 4):
        w, = struct.unpack_from("<I", a9, i)
        # ARM: cond 01 I P U B W L, ldr rd, [pc, #ofs] => 0xE59Fxxxx
        if (w & 0x0FFF0000) == 0x059F0000:
            ofs = w & 0xFFF
            if (w >> 23) & 1:  # U bit
                tgt = i + 8 + ofs
            else:
                tgt = i + 8 - ofs
            if tgt == r:
                print(f"  ldr at file+0x{i:x} RAM 0x{ram+i:x} loads &'ST_FONT.SCM'")
                disasm_around(i, 0x80, 0x80, "font-name user")
