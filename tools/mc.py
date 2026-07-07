# -*- coding: utf-8 -*-
# MC(SCM) 컨테이너 코덱
#   구조: 0x20B 헤더 + BIOS 압축 스트림(허프만(타입2) 안에 LZ10 헤더포함 스트림, 체인)
#   decode: 허프만 → LZ10 → payload
#   encode: LZ10(BIOS 헤더 포함) 스트림을 타입1로 직접 저장 (게임이 타입 디스패치한다는 가설)
#           또는 encode_huff로 허프만 체인 재현
import struct
import ndspy.lz10

def huff_decompress(data, pos):
    hdr, = struct.unpack_from("<I", data, pos)
    bits = hdr & 0xF
    ctype = (hdr >> 4) & 0xF
    outsize = hdr >> 8
    assert ctype == 2, f"not huffman type: {ctype}"
    p = pos + 4
    treesize = (data[p] + 1) * 2
    tree_root = p + 1
    wp = p + treesize
    out = bytearray()
    node = tree_root
    bitpos = 0
    word = 0
    nib = None
    while len(out) < outsize:
        if bitpos == 0:
            word, = struct.unpack_from("<I", data, wp)
            wp += 4
            bitpos = 32
        b = (word >> 31) & 1
        word = (word << 1) & 0xFFFFFFFF
        bitpos -= 1
        nd = data[node]
        nxt = (node & ~1) + (nd & 0x3F) * 2 + 2 + b
        if (b == 0 and (nd & 0x80)) or (b == 1 and (nd & 0x40)):
            val = data[nxt]
            if bits == 8:
                out.append(val)
            else:
                if nib is None: nib = val
                else: out.append(nib | (val << 4)); nib = None
            node = tree_root
        else:
            node = nxt
    return bytes(out), wp

def decode(d):
    """MC 파일 → (header32B, payload). 폰트형(u16[3]==0x20)만 지원."""
    assert d[:2] == b"MC"
    flags = struct.unpack_from("<H", d, 6)[0]
    hdr = bytes(d[:0x20])
    t = (d[0x20] >> 4) & 0xF
    if t == 2:
        mid, _ = huff_decompress(d, 0x20)
        assert mid[0] == 0x10, "expected LZ10 after huffman"
        return hdr, ndspy.lz10.decompress(mid)
    elif t == 1 and d[0x20] == 0x10:
        return hdr, ndspy.lz10.decompress(bytes(d[0x20:]))
    else:
        raise ValueError(f"unknown stream type {t}")

def encode_lz(hdr, payload):
    """타입1: BIOS 헤더 포함 LZ10 스트림을 0x20에 직접 배치. MC u32[0] 갱신."""
    comp = ndspy.lz10.compress(payload)          # b'\x10' + size24 + stream
    h = bytearray(hdr)
    struct.pack_into("<I", h, 0x10, len(payload))
    out = bytes(h) + comp
    if len(out) % 4: out += b"\0" * (4 - len(out) % 4)
    return out

# ---- BIOS 호환 허프만 인코더 (8bit) ----
def _build_tree(freq):
    import heapq
    heap = []
    for s, f in enumerate(freq):
        if f: heap.append((f, 1, ("leaf", s)))
    if len(heap) == 1:
        s = heap[0][2][1]
        other = (s + 1) & 0xFF
        heap.append((0, 1, ("leaf", other)))
    heapq.heapify(heap)
    cnt = 0
    while len(heap) > 1:
        f1, d1, n1 = heapq.heappop(heap)
        f2, d2, n2 = heapq.heappop(heap)
        cnt += 1
        heapq.heappush(heap, (f1 + f2, max(d1, d2) + 1, ("node", n1, n2)))
    return heap[0][2]

def _layout(root):
    """GBATEK 트리 테이블 배치. 각 내부노드의 자식쌍 위치가 (pos&~1)+2+ofs*2, ofs<=63."""
    table = bytearray([0])  # [0]=treesize placeholder, root node at index 1
    # 노드 배치: 큐 기반, 슬롯 부족 시 대기 최소화 (DSDecmp 방식 근사)
    pending = [(1, root)]   # (table_index, node)
    table.append(0)         # root slot
    del table[1:]           # redo: table[0] placeholder only
    table = bytearray([0, 0])  # [0] size, [1] root
    q = [(1, root)]
    while q:
        # 다음 자식쌍 배치 위치
        pos, node = q.pop(0)
        if node[0] == "leaf":
            table[pos] = node[1]
            continue
        # 자식쌍을 테이블 끝에 배치
        cpos = len(table)
        if cpos % 2: table.append(0); cpos += 1
        ofs = (cpos - (pos & ~1) - 2) // 2
        if ofs > 0x3F:
            raise ValueError(f"offset overflow {ofs}")
        flags = 0
        if node[1][0] == "leaf": flags |= 0x80
        if node[2][0] == "leaf": flags |= 0x40
        table[pos] = flags | ofs
        table.extend((0, 0))
        q.append((cpos, node[1]))
        q.append((cpos + 1, node[2]))
    if len(table) % 2: table.append(0)
    table[0] = len(table) // 2 - 1
    return bytes(table)

def _codes(root):
    codes = {}
    def rec(n, bits, ln):
        if n[0] == "leaf":
            codes[n[1]] = (bits, ln)
        else:
            rec(n[1], bits << 1, ln + 1)
            rec(n[2], (bits << 1) | 1, ln + 1)
    rec(root, 0, 0)
    return codes

def huff_compress(data, bits=8):
    if bits == 8:
        freq = [0] * 256
        for b in data: freq[b] += 1
        syms = list(data)
    else:  # 4bit: 낮은 니블 먼저
        freq = [0] * 16
        syms = []
        for b in data:
            syms.append(b & 0xF); syms.append(b >> 4)
        for s in syms: freq[s] += 1
    root = _build_tree(freq)
    table = _layout(root)
    codes = _codes(root)
    out = bytearray(struct.pack("<I", (len(data) << 8) | 0x20 | bits))
    out += table
    acc, nbits = 0, 0
    words = []
    for s in syms:
        c, ln = codes[s]
        acc = (acc << ln) | c
        nbits += ln
        while nbits >= 32:
            words.append((acc >> (nbits - 32)) & 0xFFFFFFFF)
            nbits -= 32
    if nbits:
        words.append((acc << (32 - nbits)) & 0xFFFFFFFF)
    for w in words:
        out += struct.pack("<I", w)
    return bytes(out)

def encode_huff(hdr, payload, bits=None):
    """원본과 동일한 허프만(LZ10(payload)) 체인. 8bit 배치 실패시 4bit 폴백."""
    lz = ndspy.lz10.compress(payload)
    if bits is None:
        try:
            comp = huff_compress(lz, 8)
        except ValueError:
            comp = huff_compress(lz, 4)
    else:
        comp = huff_compress(lz, bits)
    h = bytearray(hdr)
    struct.pack_into("<I", h, 0x10, len(payload))
    out = bytes(h) + comp
    if len(out) % 4: out += b"\0" * (4 - len(out) % 4)
    return out

if __name__ == "__main__":
    import os, sys, json
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import ndspy.rom
    BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
    WORK = os.path.join(BASE, "work")
    rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))
    sang = bytes(rom.files[rom.filenames.idOf("SANGOKU.NFP")])
    toc = json.load(open(os.path.join(WORK, "sangoku_toc.json"), encoding="utf-8"))
    files = {name: (off, sz) for name, off, sz in toc}
    for nm in ("ST_FONT.SCM", "STS_FONT.SCM"):
        off, sz = files[nm]
        d = sang[off:off+sz]
        hdr, payload = decode(d)
        print(f"{nm}: payload={len(payload)} magic={payload[:4]}")
        # 허프만 인코더 왕복 검증
        enc = encode_huff(hdr, payload)
        hdr2, payload2 = decode(enc)
        print(f"  huff roundtrip: {'OK' if payload2 == payload else 'FAIL'} encsize={len(enc)} (orig {sz})")
        open(os.path.join(WORK, nm.replace(".SCM", ".nftr")), "wb").write(payload)
