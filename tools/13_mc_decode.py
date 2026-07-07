# -*- coding: utf-8 -*-
# SCM "MC" 컨테이너: LZ10 스트림 가설 검증
import os, sys, json, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import ndspy.rom, ndspy.lz10

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
WORK = os.path.join(BASE, "work")
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))
sang = bytes(rom.files[rom.filenames.idOf("SANGOKU.NFP")])
toc = json.load(open(os.path.join(WORK, "sangoku_toc.json"), encoding="utf-8"))
files = {name: (off, sz) for name, off, sz in toc}

def try_decode(name):
    off, sz = files[name]
    d = sang[off:off+sz]
    hdr = d[:0x20]
    fields = struct.unpack_from("<HHHHHHHH", d, 0)
    u32s = struct.unpack_from("<IIII", d, 0x10)
    print(f"{name}: sz={sz} u16s={[hex(x) for x in fields]} u32s@0x10={[hex(x) for x in u32s]}")
    # 가설: 0x20부터 LZ10 raw 스트림, 해제크기 = u32s[0]
    for start, size in ((0x20, u32s[0]), (0x20, u32s[3]), (0x10, u32s[0])):
        if not (0 < size < 0x400000): continue
        blob = bytes([0x10, size & 0xff, (size >> 8) & 0xff, (size >> 16) & 0xff]) + d[start:]
        try:
            dec = ndspy.lz10.decompress(blob)
            print(f"  OK! stream@0x{start:x} decSize={size} -> got {len(dec)}")
            return bytes(dec)
        except Exception as e:
            print(f"  fail stream@0x{start:x} size={size}: {str(e)[:60]}")
    return None

for nm in ("000.SCM", "ST_FONT.SCM", "STS_FONT.SCM", "SUMI.SCM"):
    dec = try_decode(nm)
    if dec:
        open(os.path.join(WORK, nm + ".dec"), "wb").write(dec)
        # 미리보기
        for i in range(0, 0x60, 16):
            row = dec[i:i+16]
            print("   ", " ".join(f"{b:02x}" for b in row), " ", "".join(chr(b) if 32 <= b < 127 else "." for b in row))
    print()
