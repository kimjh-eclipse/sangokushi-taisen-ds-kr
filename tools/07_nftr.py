# -*- coding: utf-8 -*-
# OSAKA.NFT (NFTR) 폰트 구조 분석: cmap 인코딩 방식 확인
import ndspy.rom, struct, os, json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))
sang = bytes(rom.files[rom.filenames.idOf("SANGOKU.NFP")])
toc = json.load(open(os.path.join(BASE, "work", "sangoku_toc.json"), encoding="utf-8"))
files = {name: (off, sz) for name, off, sz in toc}
off, sz = files["OSAKA.NFT"]
d = sang[off:off+sz]
open(os.path.join(BASE, "work", "OSAKA.NFT"), "wb").write(d)

# NFTR 헤더
magic, bom, ver, filesize, hdrsize, nblocks = struct.unpack_from("<4sHHIHH", d, 0)
print(f"magic={magic} bom=0x{bom:04x} ver=0x{ver:04x} size={filesize} hdr={hdrsize} blocks={nblocks}")

# 블록 순회
pos = hdrsize
glyph_info = {}
cmaps = []
while pos < len(d) - 8:
    btag, bsize = struct.unpack_from("<4sI", d, pos)
    tag = btag[::-1].decode("ascii", "replace")
    print(f"block {tag} at 0x{pos:x} size={bsize}")
    if tag == "FINF":
        (fontType, lineFeed, altCharIdx, defW_l, defW_gw, defW_cw, encoding,
         offCGLP, offCWDH, offCMAP) = struct.unpack_from("<BBHbBbB3I", d, pos + 8)
        print(f"  encoding={encoding} (0=UTF8,1=UTF16,2=SJIS,3=CP1252)  altCharIdx={altCharIdx}")
        print(f"  lineFeed={lineFeed} CGLP@0x{offCGLP:x} CWDH@0x{offCWDH:x} CMAP@0x{offCMAP:x}")
        if bsize >= 0x20:
            ht, wd, asc = struct.unpack_from("<BBB", d, pos + 8 + 20)
            print(f"  height={ht} width={wd} ascent={asc}")
    elif tag == "CGLP":
        cw, ch, tilesz, _, bpp, _ = struct.unpack_from("<BBHBBH", d, pos + 8)
        nglyph = (bsize - 0x10) // tilesz
        print(f"  cellW={cw} cellH={ch} tileSize={tilesz} bpp={bpp} glyphs~={nglyph}")
    elif tag == "CMAP":
        first, last, mtype, _, nextofs = struct.unpack_from("<HHHHI", d, pos + 8)
        print(f"  range U+{first:04X}-U+{last:04X} type={mtype} next=0x{nextofs:x}")
        cmaps.append((pos, first, last, mtype))
        if mtype == 2:
            cnt, = struct.unpack_from("<H", d, pos + 0x14)
            pairs = [struct.unpack_from("<HH", d, pos + 0x16 + i*4) for i in range(min(cnt, 10))]
            print(f"    scan count={cnt} first pairs={[(hex(c),g) for c,g in pairs]}")
    if bsize == 0: break
    pos += bsize
