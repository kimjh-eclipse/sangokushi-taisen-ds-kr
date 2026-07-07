# -*- coding: utf-8 -*-
# 변형 A: ST_FONT 해제→무변조 재압축 (압축기 호환성 검증)
# 변형 B: ST_FONT 해제→뒤쪽 절반만 XOR→재압축 (글리프 데이터만 손상)
import os, sys, struct
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
import ndspy.rom, ndspy.lz10
import nfp

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
WORK = os.path.join(BASE, "work")

def build(variant, outname):
    rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))
    fid = rom.filenames.idOf("SANGOKU.NFP")
    hdr, files = nfp.unpack(bytes(rom.files[fid]))
    newfiles = []
    for name, d in files:
        if name == "ST_FONT.SCM":
            decsize, = struct.unpack_from("<I", d, 0x10)
            blob = bytes([0x10, decsize & 0xff, (decsize >> 8) & 0xff, (decsize >> 16) & 0xff]) + d[0x20:]
            dec = bytearray(ndspy.lz10.decompress(blob))
            if variant == "B":
                for i in range(len(dec) // 2, len(dec)):
                    dec[i] ^= 0xFF
            comp = ndspy.lz10.compress(bytes(dec))[4:]
            if len(comp) % 4: comp += b"\0" * (4 - len(comp) % 4)
            d = d[:0x20] + comp
            print(f"{outname}: dec={decsize} comp={len(comp)} (orig {len(files[[f[0] for f in files].index(name)][1])-0x20})")
        newfiles.append((name, d))
    rom.files[fid] = nfp.repack(hdr, newfiles)
    rom.saveToFile(os.path.join(WORK, outname))
    print("saved", outname)

build("A", "test_recomp.nds")
build("B", "test_tailxor.nds")
