# -*- coding: utf-8 -*-
# SANGOKU.NFP 헤더 구조 확인 + 천의 NFP와 비교
import ndspy.rom, struct, os

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"

def get_file(romfn, path):
    rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, romfn))
    fid = rom.filenames.idOf(path)
    return bytes(rom.files[fid])

def hexdump(data, off=0, n=0x100):
    for i in range(off, off + n, 16):
        row = data[i:i+16]
        hexs = " ".join(f"{b:02x}" for b in row)
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in row)
        print(f"{i:08x}  {hexs:<48}  {asc}")

sang = get_file("San Goku Shi Taisen (J).nds", "SANGOKU.NFP")
print(f"SANGOKU.NFP size={len(sang)}")
hexdump(sang, 0, 0x120)

print("\n--- Ten(J) cardname_l.NFP for comparison ---")
ten = get_file("San Goku Shi Taisen Ten (J).nds", "cardname_l.NFP")
hexdump(ten, 0, 0x80)

# 헤더 필드 해석 시도 (Ten 기준: 0x34=count, 0x38=table start, 0x3c=data start)
for name, d in (("SANGOKU", sang), ("ten_cardname_l", ten)):
    cnt, tbl, dat = struct.unpack_from("<III", d, 0x34)
    print(f"\n{name}: 0x34(count?)={cnt}  0x38(tbl?)=0x{tbl:x}  0x3c(data?)=0x{dat:x}")
    # 테이블 첫 엔트리들
    hexdump(d, tbl if tbl < len(d) else 0x50, 0x60)
