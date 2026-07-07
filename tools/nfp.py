# -*- coding: utf-8 -*-
# NFP2.0 (NOBORI) 언팩/리팩 라이브러리 + 왕복 검증
import struct, os

def parse(data):
    """returns (header_bytes, [(name, offset, size), ...])"""
    assert data[:4] == b"NFP2", "not NFP2.0"
    cnt, tbl, dat = struct.unpack_from("<III", data, 0x34)
    entries = []
    for i in range(cnt):
        off = tbl + i * 16
        name = data[off:off+12].split(b"\0")[0].decode("ascii")
        foff, = struct.unpack_from("<I", data, off + 12)
        entries.append([name, foff])
    out = []
    for i, (name, foff) in enumerate(entries):
        end = entries[i+1][1] if i + 1 < cnt else len(data)
        out.append((name, foff, end - foff))
    return data[:tbl], out

def unpack(data):
    hdr, ents = parse(data)
    return hdr, [(name, bytes(data[off:off+sz])) for name, off, sz in ents]

def repack(header, files):
    """files: [(name, bytes), ...] — 순서 유지. 헤더의 count/table/data 필드 갱신."""
    cnt = len(files)
    tbl = 0x40
    tblsize = cnt * 16
    datstart = tbl + tblsize
    # 원본 데이터 시작이 정렬돼 있었다면 유지 (0x10 정렬)
    datstart = (datstart + 0xF) & ~0xF
    hdr = bytearray(header[:tbl].ljust(tbl, b"\0"))
    struct.pack_into("<III", hdr, 0x34, cnt, tbl, datstart)
    table = bytearray()
    blob = bytearray()
    pos = datstart
    for name, d in files:
        nb = name.encode("ascii")
        assert len(nb) <= 12
        table += nb.ljust(12, b"\0") + struct.pack("<I", pos)
        blob += d
        pos += len(d)
    out = bytes(hdr[:tbl]) + bytes(table) + b"\0" * (datstart - tbl - len(table)) + bytes(blob)
    return out

if __name__ == "__main__":
    import ndspy.rom, hashlib, sys
    BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
    rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))
    sang = bytes(rom.files[rom.filenames.idOf("SANGOKU.NFP")])
    hdr, files = unpack(sang)
    out = repack(hdr, files)
    print("roundtrip identical:", out == sang)
    if out != sang:
        # 어디부터 다른지
        for i in range(min(len(out), len(sang))):
            if out[i] != sang[i]:
                print(f"first diff at 0x{i:x}: orig={sang[i]:02x} new={out[i]:02x}")
                break
        print(f"len orig={len(sang)} new={len(out)}")
