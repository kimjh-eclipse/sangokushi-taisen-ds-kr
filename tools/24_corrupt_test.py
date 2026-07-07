# -*- coding: utf-8 -*-
# 폰트 손상 실험: 지정 서브파일을 변조한 ROM 빌드
#   usage: 24_corrupt_test.py ST_FONT.SCM out.nds
#   - LZ10 서브파일(폰트)은 해제→비트반전→재압축(원시 스트림)
import os, sys, json, struct
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
import ndspy.rom, ndspy.lz10
import nfp

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
WORK = os.path.join(BASE, "work")

target = sys.argv[1]
outname = sys.argv[2]

rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))
fid = rom.filenames.idOf("SANGOKU.NFP")
hdr, files = nfp.unpack(bytes(rom.files[fid]))

newfiles = []
for name, d in files:
    if name == target:
        if name.endswith(".NFT"):
            # NFTR: CGLP 글리프 비트맵 반전 (0x34부터 CWDH 전까지)
            nd = bytearray(d)
            for i in range(0x40, 0x30afc):
                nd[i] ^= 0xFF
            d = bytes(nd)
            print(f"corrupted NFT glyphs")
        else:
            decsize, = struct.unpack_from("<I", d, 0x10)
            blob = bytes([0x10, decsize & 0xff, (decsize >> 8) & 0xff, (decsize >> 16) & 0xff]) + d[0x20:]
            dec = bytearray(ndspy.lz10.decompress(blob))
            for i in range(len(dec)):
                dec[i] ^= 0xFF
            comp = ndspy.lz10.compress(bytes(dec))[4:]  # 표준 4바이트 헤더 제거
            d = d[:0x20] + comp
            print(f"corrupted {name}: dec={decsize} recompressed={len(comp)}")
        newfiles.append((name, d))
    else:
        newfiles.append((name, d))

rom.files[fid] = nfp.repack(hdr, newfiles)
out = os.path.join(WORK, outname)
rom.saveToFile(out)
print("saved", out)
