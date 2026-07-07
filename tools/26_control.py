# -*- coding: utf-8 -*-
# 대조군 1: ndspy 로드→저장만 (무수정)
# 대조군 2: NFP 언팩→리팩만 (무수정, 왕복 동일 확인됐지만 ROM 경유 검증)
import os, sys
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
import ndspy.rom
import nfp

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
WORK = os.path.join(BASE, "work")

rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))
rom.saveToFile(os.path.join(WORK, "test_resave.nds"))
print("saved test_resave.nds")

rom2 = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))
fid = rom2.filenames.idOf("SANGOKU.NFP")
hdr, files = nfp.unpack(bytes(rom2.files[fid]))
rom2.files[fid] = nfp.repack(hdr, files)
rom2.saveToFile(os.path.join(WORK, "test_nfproundtrip.nds"))
print("saved test_nfproundtrip.nds")
