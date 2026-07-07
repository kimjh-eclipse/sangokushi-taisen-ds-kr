# -*- coding: utf-8 -*-
# 최종 빌드: 폰트 한글화 + 카드 DAT(.kr) 교체 + scenario.sar 번역 → ROM
import os, sys, json, glob
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
sys.stdout.reconfigure(encoding="utf-8")
import ndspy.rom, ndspy.code
import nfp, mc, sar, korean, arm9text

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
WORK = os.path.join(BASE, "work")
outname = sys.argv[1] if len(sys.argv) > 1 else "San Goku Shi Taisen (K).nds"

# 스토리 번역 취합
story = {}
for f in glob.glob(os.path.join(WORK, "tl_out", "e*.json")):
    ei = int(os.path.basename(f)[1:4])
    m = json.load(open(f, encoding="utf-8"))
    story[ei] = {int(off): ko for off, ko in m.items()}
print(f"스토리: {len(story)}엔트리 {sum(len(v) for v in story.values())}문자열")

rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))

# arm9 인플레이스 시스템 텍스트 (ml 다줄 기준 통합)
mlp = os.path.join(WORK, "arm9_ml.json")
if os.path.exists(mlp):
    def _noise(s):
        return sum(1 for c in s if '一' <= c <= '鿿' or '぀' <= c <= 'ん' or 'ァ' <= c <= 'ヴ') < 3
    ml = json.load(open(mlp, encoding="utf-8"))
    oldsrc = {it["off"]: it["jp"] for it in json.load(open(os.path.join(WORK, "arm9_src.json"), encoding="utf-8"))}
    oldko = {o["off"]: o["ko"] for o in json.load(open(os.path.join(WORK, "arm9_out.json"), encoding="utf-8"))}
    newko = {}
    np = os.path.join(WORK, "arm9_new_out.json")
    if os.path.exists(np):
        newko = {o["off"]: o["ko"] for o in json.load(open(np, encoding="utf-8"))}
    patches = []
    for it in ml:
        off = it["off"]
        if _noise(it["jp"]):
            continue
        if off in newko:
            ko = newko[off]
        elif off in oldsrc and oldsrc[off] == it["jp"] and off in oldko:
            ko = oldko[off]
        else:
            ko = ""
        if ko.strip():
            patches.append({"off": off, "nbytes": it["nbytes"], "ko": ko})
    # ml에서 누락된 명시 번역(newko)도 원문 NUL길이로 강제 적용 (추출조건 변경으로 off 이동 대비)
    a9raw = bytes(rom.arm9)
    covered = {p["off"] for p in patches}
    for off, ko in newko.items():
        if off in covered or not ko.strip():
            continue
        end = a9raw.find(b"\x00", off)
        if end < 0:
            continue
        patches.append({"off": off, "nbytes": end - off, "ko": ko})
    new_a9, errs = arm9text.apply(bytes(rom.arm9), patches, korean.encode, allow_nl=True)
    rom.arm9 = new_a9
    print(f"arm9: {len(patches)}개 치환, 오류 {len(errs)}")
    for e in errs[:10]:
        print("  arm9 오류:", e)

# overlay 인플레이스 시스템 텍스트 (있으면)
ovp = os.path.join(WORK, "ov_out.json")
ovsrcp = os.path.join(WORK, "ov_src.json")
if os.path.exists(ovp) and os.path.exists(ovsrcp):
    ovsrc = json.load(open(ovsrcp, encoding="utf-8"))
    fileIDs = {int(k): v for k, v in ovsrc["fileIDs"].items()}
    nbmap = {}  # (oid,off)->nbytes
    for oid, items in ovsrc["items"].items():
        for it in items:
            nbmap[(int(oid), it["off"])] = it["nbytes"]
    ovtl = json.load(open(ovp, encoding="utf-8"))
    ov_total = ov_err = 0
    for oid_s, items in ovtl.items():
        oid = int(oid_s); fid = fileIDs[oid]
        patches = [{"off": o["off"], "nbytes": o.get("nbytes", nbmap.get((oid, o["off"]))), "ko": o["ko"]}
                   for o in items if o["ko"].strip() and (o.get("nbytes") or (oid, o["off"]) in nbmap)]
        new_ov, errs = arm9text.apply(bytes(rom.files[fid]), patches, korean.encode, allow_nl=True)
        rom.files[fid] = new_ov
        ov_total += len(patches); ov_err += len(errs)
        for e in errs: print("  ov 오류:", oid, e)
    print(f"overlay: {ov_total}개 치환, 오류 {ov_err}")

# SANGOKU.NFP: 폰트 + DAT 교체
fid = rom.filenames.idOf("SANGOKU.NFP")
hdr, files = nfp.unpack(bytes(rom.files[fid]))
st = open(os.path.join(WORK, "ST_FONT.kr.nftr"), "rb").read()
sts = open(os.path.join(WORK, "STS_FONT.kr.nftr"), "rb").read()
osaka = open(os.path.join(WORK, "OSAKA.kr.NFT"), "rb").read()
# 번역된 DAT 로드
dat_kr = {}
for p in glob.glob(os.path.join(WORK, "*.DAT.kr")):
    name = os.path.basename(p)[:-3]
    dat_kr[name] = open(p, "rb").read()
print(f"DAT 교체: {list(dat_kr)}")
# 식자된 그래픽 SCM 로드 (work/<NAME>.SCM.kr)
gfx_kr = {}
for p in glob.glob(os.path.join(WORK, "*.SCM.kr")):
    name = os.path.basename(p)[:-3]
    gfx_kr[name] = open(p, "rb").read()
print(f"그래픽 교체: {list(gfx_kr)}")
# 무장명 명판 일괄 (work/np_kr/*.SCM — 파일명 = NFP 엔트리명)
np_cnt = 0
for p in glob.glob(os.path.join(WORK, "np_kr", "*.SCM")):
    gfx_kr[os.path.basename(p)] = open(p, "rb").read()
    np_cnt += 1
print(f"명판 교체: {np_cnt}개")

nf = []
cnt_dat = cnt_gfx = 0
for name, d in files:
    if name == "ST_FONT.SCM": h,_ = mc.decode(d); d = mc.encode_huff(h, st)
    elif name == "STS_FONT.SCM": h,_ = mc.decode(d); d = mc.encode_huff(h, sts)
    elif name == "OSAKA.NFT": d = osaka
    elif name in dat_kr: d = dat_kr[name]; cnt_dat += 1
    elif name in gfx_kr: d = gfx_kr[name]; cnt_gfx += 1
    nf.append((name, d))
rom.files[fid] = nfp.repack(hdr, nf)
print(f"NFP 재빌드: DAT {cnt_dat}개, 그래픽 {cnt_gfx}개 교체")

# scenario.sar
sid = rom.filenames.idOf("scenario.sar")
rom.files[sid] = sar.rebuild(bytes(rom.files[sid]), story, korean.encode)

out = os.path.join(BASE, outname)
rom.saveToFile(out)
print("saved", out)
