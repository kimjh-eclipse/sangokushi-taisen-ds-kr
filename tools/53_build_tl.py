# -*- coding: utf-8 -*-
# tl_out/*.json 번역을 scenario.sar에 반영 + 폰트 한글화 → ROM 빌드
import os, sys, json, glob
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
sys.stdout.reconfigure(encoding="utf-8")
import ndspy.rom
import nfp, mc, sar, korean

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
WORK = os.path.join(BASE, "work")
outname = sys.argv[1] if len(sys.argv) > 1 else "test_tl.nds"

# 번역 취합
all_tl = {}
for f in glob.glob(os.path.join(WORK, "tl_out", "e*.json")):
    ei = int(os.path.basename(f)[1:4])
    m = json.load(open(f, encoding="utf-8"))
    all_tl[ei] = {int(off): ko for off, ko in m.items()}
print(f"번역 반영 엔트리 {len(all_tl)}개, 문자열 {sum(len(v) for v in all_tl.values())}개")

rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))

# 폰트 한글화
fid = rom.filenames.idOf("SANGOKU.NFP")
hdr, files = nfp.unpack(bytes(rom.files[fid]))
st = open(os.path.join(WORK, "ST_FONT.kr.nftr"), "rb").read()
sts = open(os.path.join(WORK, "STS_FONT.kr.nftr"), "rb").read()
osaka = open(os.path.join(WORK, "OSAKA.kr.NFT"), "rb").read()
nf = []
for name, d in files:
    if name == "ST_FONT.SCM": h,_ = mc.decode(d); d = mc.encode_huff(h, st)
    elif name == "STS_FONT.SCM": h,_ = mc.decode(d); d = mc.encode_huff(h, sts)
    elif name == "OSAKA.NFT": d = osaka
    nf.append((name, d))
rom.files[fid] = nfp.repack(hdr, nf)

# scenario.sar
sid = rom.filenames.idOf("scenario.sar")
sar_data = bytes(rom.files[sid])
rom.files[sid] = sar.rebuild(sar_data, all_tl, korean.encode)

out = os.path.join(WORK, outname)
rom.saveToFile(out)
print("saved", out)
