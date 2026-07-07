# -*- coding: utf-8 -*-
# arm9 세력명 테이블 덤프 → 번역 항목 생성
import sys, json, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import ndspy.rom

BASE = r'C:\Emul\Switch\패치유틸.xdeltaUI'
WORK = os.path.join(BASE, 'work')
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, 'San Goku Shi Taisen (J).nds'))
a9 = bytes(rom.arm9)
base = 0x139ef0
for i in range(0, 0xa0, 16):
    off = base + i
    seg = a9[off:off+16]
    txt = seg.decode('cp932', errors='replace')
    print(f'{off:#x}: {seg.hex(" ")}  |{txt}|')
