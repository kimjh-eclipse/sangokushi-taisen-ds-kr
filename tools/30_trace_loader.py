# -*- coding: utf-8 -*-
# 0x2065ca4 (NFP 파일 로드) 함수 + 콜리 재귀 디스어셈블
import os, sys, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import ndspy.rom
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))
a9 = bytes(rom.arm9)
ram = rom.arm9RamAddress
md = Cs(CS_ARCH_ARM, CS_MODE_ARM)

def disasm_func(addr, maxlen=0x200):
    """pop pc / bx lr까지 디스어셈블. (텍스트, 콜리목록) 반환"""
    foff = addr - ram
    code = a9[foff:foff+maxlen]
    lines = []
    callees = []
    for ins in md.disasm(code, addr):
        lines.append(f"  {ins.address:08x}  {ins.mnemonic:<8} {ins.op_str}")
        if ins.mnemonic == "bl":
            try: callees.append(int(ins.op_str.strip("#"), 16))
            except: pass
        # ldr rX, [pc, #..] 리터럴 값 주석
        if ins.mnemonic == "ldr" and "[pc" in ins.op_str:
            try:
                imm = int(ins.op_str.split("#")[1].rstrip("]"), 16)
                lit = ins.address + 8 + imm
                v, = struct.unpack_from("<I", a9, lit - ram)
                lines[-1] += f"   ; =0x{v:x}"
            except Exception: pass
        if ins.mnemonic in ("pop", "bx") and ("pc" in ins.op_str or ins.op_str == "lr"):
            break
    return "\n".join(lines), callees

seen = set()
def walk(addr, depth=0, maxdepth=2):
    if addr in seen or depth > maxdepth: return
    seen.add(addr)
    txt, callees = disasm_func(addr)
    print(f"\n===== func 0x{addr:x} (depth {depth}) =====")
    print(txt)
    for c in callees:
        walk(c, depth + 1, maxdepth)

walk(0x2065ca4, 0, 1)
