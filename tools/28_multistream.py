# -*- coding: utf-8 -*-
# LZ10 소비량 추적 디코더로 SCM 다중 스트림 구조 규명
import os, sys, struct, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
import ndspy.rom

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
WORK = os.path.join(BASE, "work")

def lz10_dec(src, pos, decsize):
    """raw LZ10 stream (헤더 없음) 해제. returns (data, consumed_end_pos)"""
    out = bytearray()
    n = len(src)
    while len(out) < decsize:
        if pos >= n: raise ValueError("EOF")
        flags = src[pos]; pos += 1
        for bit in range(8):
            if len(out) >= decsize: break
            if flags & (0x80 >> bit):
                if pos + 2 > n: raise ValueError("EOF ref")
                b1, b2 = src[pos], src[pos+1]; pos += 2
                ln = (b1 >> 4) + 3
                disp = ((b1 & 0xF) << 8 | b2) + 1
                for _ in range(ln):
                    out.append(out[-disp])
            else:
                out.append(src[pos]); pos += 1
    return bytes(out), pos

rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))
sang = bytes(rom.files[rom.filenames.idOf("SANGOKU.NFP")])
toc = json.load(open(os.path.join(WORK, "sangoku_toc.json"), encoding="utf-8"))
files = {name: (off, sz) for name, off, sz in toc}

for nm in ("ST_FONT.SCM", "STS_FONT.SCM"):
    off, sz = files[nm]
    d = sang[off:off+sz]
    u32s = struct.unpack_from("<IIII", d, 0x10)
    print(f"\n=== {nm} sz={sz} u32s={[hex(x) for x in u32s]}")
    pos = 0x20
    si = 0
    sizes = [u32s[0], u32s[3]]
    while pos < len(d) - 4 and si < 6:
        decsize = sizes[si] if si < len(sizes) else None
        if not decsize: break
        try:
            dec, newpos = lz10_dec(d, pos, decsize)
        except ValueError as e:
            print(f"  stream{si} at 0x{pos:x} FAILED: {e}")
            break
        print(f"  stream{si}: in=0x{pos:x}..0x{newpos:x} ({newpos-pos}B) -> out {len(dec)}B")
        open(os.path.join(WORK, f"{nm}.s{si}"), "wb").write(dec)
        # 다음 스트림: 4바이트 정렬 시도
        pos = newpos
        if pos % 4: pos += 4 - pos % 4
        si += 1
        # 남은 바이트
    print(f"  remaining after streams: {len(d)-pos}B")
