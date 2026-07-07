# -*- coding: utf-8 -*-
# ARM9에서 'MC' (0x434D) 상수 참조 및 헤더 파싱 코드 탐색
import os, sys, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import ndspy.rom
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))
a9 = bytes(rom.arm9)
ram = rom.arm9RamAddress

# 리터럴 풀에서 0x434D 검색
hits = []
for i in range(0, len(a9) - 3, 4):
    v, = struct.unpack_from("<I", a9, i)
    if v == 0x434D or v == 0x4D43 or v == 0x0110434D:
        hits.append((i, v))
print("literal 0x434D hits:", [(hex(i), hex(v)) for i, v in hits])

# mov rX, #0x4D00 / cmp 패턴: ARM에서 0x434D는 두 인스트럭션 (mov+orr / movw)
# ARMv5에는 movw 없음 → ldr pc-relative가 일반적. 또는 개별 바이트 비교('M'=0x4D, 'C'=0x43)
# cmp rX, #0x4D  : e35?004d
cnt = 0
md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
for i, v in hits:
    # 이 리터럴을 참조하는 ldr 찾기
    for j in range(max(0, i - 0x1000), i, 4):
        w, = struct.unpack_from("<I", a9, j)
        if (w & 0x0FFF0000) == 0x059F0000:
            ofs = w & 0xFFF
            tgt = j + 8 + ofs if (w >> 23) & 1 else j + 8 - ofs
            if tgt == i:
                print(f"\nldr at 0x{ram+j:x} loads 0x{v:x}; disasm:")
                code = a9[j-0x40:j+0x100]
                for ins in md.disasm(code, ram + j - 0x40):
                    mark = " <<<" if ins.address == ram + j else ""
                    print(f"  {ins.address:08x}  {ins.mnemonic:<8} {ins.op_str}{mark}")
                cnt += 1
                if cnt > 4: break
