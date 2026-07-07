# -*- coding: utf-8 -*-
# NFTR(RTFN) 폰트 편집 라이브러리: SJIS cmap 파싱, 글리프 교체, 폭 설정
import struct

class NFTR:
    def __init__(self, data):
        self.data = bytearray(data)
        magic, bom, ver, filesize, hdrsize, nblocks = struct.unpack_from("<4sHHIHH", data, 0)
        assert magic == b"RTFN"
        pos = hdrsize
        self.cmap_blocks = []
        while pos < len(data) - 8:
            btag, bsize = struct.unpack_from("<4sI", data, pos)
            tag = btag[::-1].decode("ascii", "replace")
            if tag == "FINF":
                self.finf = pos
                (self.fontType, self.lineFeed, self.altCharIdx, dw0, dw1, dw2,
                 self.encoding, self.offCGLP, self.offCWDH, self.offCMAP) = struct.unpack_from("<BBHbBbB3I", data, pos + 8)
            elif tag == "CGLP":
                self.cglp = pos
                (self.cellW, self.cellH, self.tileSize, self.baseline,
                 self.maxWidth, self.bpp, self.flags) = struct.unpack_from("<BBHbBBB", data, pos + 8)
                self.glyphOfs = pos + 0x10
                self.nGlyphs = (bsize - 0x10) // self.tileSize
            elif tag == "CWDH":
                self.cwdh = pos
                self.wFirst, self.wLast, wnext = struct.unpack_from("<HHI", data, pos + 8)
                self.widthOfs = pos + 0x10   # 3바이트/글리프 (left, glyphW, charW)
            elif tag == "CMAP":
                first, last, mtype, _, nxt = struct.unpack_from("<HHHHI", data, pos + 8)
                self.cmap_blocks.append((pos, first, last, mtype))
            if bsize == 0:
                break
            pos += bsize
        # 코드→글리프 매핑 구축
        self.code2glyph = {}
        d = self.data
        for pos, first, last, mtype in self.cmap_blocks:
            if mtype == 0:
                base, = struct.unpack_from("<H", d, pos + 0x14)
                for i, c in enumerate(range(first, last + 1)):
                    self.code2glyph[c] = base + i
            elif mtype == 1:
                for i, c in enumerate(range(first, last + 1)):
                    g, = struct.unpack_from("<H", d, pos + 0x14 + i * 2)
                    if g != 0xFFFF:
                        self.code2glyph[c] = g
            elif mtype == 2:
                cnt, = struct.unpack_from("<H", d, pos + 0x14)
                for i in range(cnt):
                    c, g = struct.unpack_from("<HH", d, pos + 0x16 + i * 4)
                    self.code2glyph[c] = g

    def get_glyph_bitmap(self, gidx):
        """1bpp/2bpp 타일 → [[val,...],...] (cellH x cellW)"""
        off = self.glyphOfs + gidx * self.tileSize
        raw = self.data[off:off + self.tileSize]
        out = []
        bit = 0
        for y in range(self.cellH):
            row = []
            for x in range(self.cellW):
                if self.bpp == 1:
                    v = (raw[bit // 8] >> (7 - bit % 8)) & 1
                    bit += 1
                else:
                    v = (raw[bit // 8] >> (8 - self.bpp - bit % 8)) & ((1 << self.bpp) - 1)
                    bit += self.bpp
                row.append(v)
            out.append(row)
        return out

    def set_glyph_bitmap(self, gidx, bmp):
        """bmp: cellH x cellW 값 배열 (0..(2^bpp -1))"""
        raw = bytearray(self.tileSize)
        bit = 0
        for y in range(self.cellH):
            for x in range(self.cellW):
                v = bmp[y][x] & ((1 << self.bpp) - 1)
                raw[bit // 8] |= v << (8 - self.bpp - (bit % self.bpp if False else bit % 8))
                bit += self.bpp
        # 위 시프트 계산 일반화 실패 방지: bpp1/2 전용 재구현
        raw = bytearray(self.tileSize)
        bit = 0
        for y in range(self.cellH):
            for x in range(self.cellW):
                v = bmp[y][x] & ((1 << self.bpp) - 1)
                sh = 8 - self.bpp - (bit % 8)
                raw[bit // 8] |= v << sh
                bit += self.bpp
        off = self.glyphOfs + gidx * self.tileSize
        self.data[off:off + self.tileSize] = raw

    def get_width(self, gidx):
        o = self.widthOfs + gidx * 3
        return struct.unpack_from("<bBB", self.data, o)  # left, glyphW, charW

    def set_width(self, gidx, left, glyphW, charW):
        o = self.widthOfs + gidx * 3
        struct.pack_into("<bBB", self.data, o, left, glyphW, charW)

    def bytes(self):
        return bytes(self.data)

if __name__ == "__main__":
    import sys, os
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"
    for fn in ("ST_FONT.nftr", "STS_FONT.nftr", "OSAKA.NFT"):
        f = NFTR(open(os.path.join(WORK, fn), "rb").read())
        print(f"{fn}: cell={f.cellW}x{f.cellH} bpp={f.bpp} tile={f.tileSize} glyphs={f.nGlyphs} "
              f"lineFeed={f.lineFeed} baseline={f.baseline} maxW={f.maxWidth} codes={len(f.code2glyph)}")
        # 한글 슬롯 후보: 0xE040-0xEAA4 매핑 확인
        slots = [c for c in f.code2glyph if 0xE040 <= c <= 0xEAA4]
        print(f"  level-2 kanji slots: {len(slots)}")
        # 왕복 검증: 글리프 하나 읽고 다시 쓰기
        g = f.code2glyph.get(0x8140, 0)
        bmp = f.get_glyph_bitmap(10)
        before = bytes(f.data)
        f.set_glyph_bitmap(10, bmp)
        print(f"  glyph rw roundtrip: {'OK' if bytes(f.data) == before else 'FAIL'}")
