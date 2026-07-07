# -*- coding: utf-8 -*-
# PoC ROM: 한글 폰트 + 튜토리얼(entry0) 한국어
import os, sys, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
import ndspy.rom
import nfp, mc, sar, korean

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
WORK = os.path.join(BASE, "work")

TUTORIAL = {
    0x3:   "군사",
    0x8:   "주군니이이이임!",
    0x1b:  "기다리고 있었습니다",
    0x32:  "단도직입적으로, 주군께서는",
    0x49:  "이 『삼국지대전DS』",
    0x60:  "즐기는 법을 알고",
    0x73:  "계십니까?",
    0x7e:  "만약 즐기는 법이나 규칙을",
    0x93:  "모르시겠다면,",
    0xaa:  "『튜토리얼』로 와",
    0xc3:  "주십시오.",
    0xce:  "불초하오나 소인이 차근차근",
    0xe9:  "기초 중의 기초부터 가르쳐",
    0x102: "드리겠습니다.",
    0x10d: "『튜토리얼』로 즐기는 법을",
    0x128: "이해하셨다면",
    0x137: "다음은 『삼국영걸전』을 추천",
    0x152: "합니다!",
    0x15b: "주군께서 실력에 자신 있다!",
    0x170: "하시겠다면",
    0x17d: "『단련의 장』에서 실력을",
    0x198: "시험하셔도 좋겠지요.",
    0x1ab: "그럼 주군, 힘내십시오.",
    0x1c6: "소인을 만나고 싶으시면",
    0x1d7: "『튜토리얼』입니다!",
}

rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))

# 1) 폰트 교체
fid = rom.filenames.idOf("SANGOKU.NFP")
hdr, files = nfp.unpack(bytes(rom.files[fid]))
st_kr = open(os.path.join(WORK, "ST_FONT.kr.nftr"), "rb").read()
sts_kr = open(os.path.join(WORK, "STS_FONT.kr.nftr"), "rb").read()
osaka_kr = open(os.path.join(WORK, "OSAKA.kr.NFT"), "rb").read()
newfiles = []
for name, d in files:
    if name == "ST_FONT.SCM":
        h, _ = mc.decode(d)
        d = mc.encode_huff(h, st_kr)
    elif name == "STS_FONT.SCM":
        h, _ = mc.decode(d)
        d = mc.encode_huff(h, sts_kr)
    elif name == "OSAKA.NFT":
        d = osaka_kr
    newfiles.append((name, d))
rom.files[fid] = nfp.repack(hdr, newfiles)
print("fonts injected")

# 2) scenario.sar entry0 번역
sid = rom.filenames.idOf("scenario.sar")
sar_data = bytes(rom.files[sid])
rom.files[sid] = sar.rebuild(sar_data, {0: TUTORIAL}, korean.encode)
print("sar rebuilt")

out = os.path.join(WORK, "test_poc.nds")
rom.saveToFile(out)
print("saved", out)
