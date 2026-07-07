# -*- coding: utf-8 -*-
# 폰트 2종을 무변조 재인코딩(허프만 체인)한 ROM 빌드
import os, sys
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
import ndspy.rom
import nfp, mc

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
WORK = os.path.join(BASE, "work")

rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))
fid = rom.filenames.idOf("SANGOKU.NFP")
hdr, files = nfp.unpack(bytes(rom.files[fid]))
newfiles = []
for name, d in files:
    if name in ("ST_FONT.SCM", "STS_FONT.SCM"):
        h, payload = mc.decode(d)
        d = mc.encode_huff(h, payload)
        print(f"re-encoded {name}: {len(d)}")
    newfiles.append((name, d))
rom.files[fid] = nfp.repack(hdr, newfiles)
rom.saveToFile(os.path.join(WORK, "test_reenc.nds"))
print("saved test_reenc.nds")
