# -*- coding: utf-8 -*-
# GBATEK BIOS Huffman 해제 → 결과가 LZ10인지 확인 (MC = Huffman+LZ 체인 가설)
import os, sys, struct, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import ndspy.rom

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
WORK = os.path.join(BASE, "work")

def huff_decompress(data, pos):
    """data[pos:]가 BIOS Huffman(헤더 포함) 스트림. (out, consumed_end) 반환"""
    hdr, = struct.unpack_from("<I", data, pos)
    bits = hdr & 0xF
    ctype = (hdr >> 4) & 0xF
    outsize = hdr >> 8
    assert ctype == 2, f"not huffman: {ctype}"
    p = pos + 4
    treesize = (data[p] + 1) * 2
    tree_root = p + 1
    p_bit = p + treesize          # 비트스트림 시작 (32bit 워드 단위)
    out = bytearray()
    node = tree_root
    bitpos = 0
    word = 0
    wp = p_bit
    nibble_buf = None
    while len(out) < outsize:
        if bitpos == 0:
            word, = struct.unpack_from("<I", data, wp)
            wp += 4
            bitpos = 32
        b = (word >> 31) & 1
        word = (word << 1) & 0xFFFFFFFF
        bitpos -= 1
        nd = data[node]
        ofs = nd & 0x3F
        leaf = (nd >> (6 - b)) & 1   # bit6=node1 leaf flag? GBATEK: bit6 = node1 end, bit7 = node0 end
        # 다음 노드 주소: (현재주소 & ~1) + ofs*2 + 2 (+1 if b)
        nxt = (node & ~1) + ofs * 2 + 2 + b
        if (b == 0 and (nd & 0x80)) or (b == 1 and (nd & 0x40)):
            # leaf: 데이터 바이트
            val = data[nxt]
            if bits == 8:
                out.append(val)
            else:  # 4bit
                if nibble_buf is None:
                    nibble_buf = val
                else:
                    out.append(nibble_buf | (val << 4))
                    nibble_buf = None
            node = tree_root
        else:
            node = nxt
    return bytes(out), wp

rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))
sang = bytes(rom.files[rom.filenames.idOf("SANGOKU.NFP")])
toc = json.load(open(os.path.join(WORK, "sangoku_toc.json"), encoding="utf-8"))
files = {name: (off, sz) for name, off, sz in toc}

for nm in ("ST_FONT.SCM",):
    off, sz = files[nm]
    d = sang[off:off+sz]
    expected, = struct.unpack_from("<I", d, 0x10)
    out, end = huff_decompress(d, 0x20)
    print(f"{nm}: huffman out={len(out)}B consumed to 0x{end-off if end>off else end:x} (file sz={sz})")
    print("first bytes:", out[:16].hex())
    if out[0] == 0x10:
        lzsize, = struct.unpack_from("<I", out, 0)
        print(f"LZ10 header inside! size={lzsize>>8} (expected {expected})")
    open(os.path.join(WORK, nm + ".huf"), "wb").write(out)
