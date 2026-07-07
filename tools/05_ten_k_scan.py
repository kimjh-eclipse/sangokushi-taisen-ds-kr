# -*- coding: utf-8 -*-
# 천(K)의 변경 NFP에서 한글 텍스트 인코딩 방식 탐색
import ndspy.rom, os, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
romJ = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen Ten (J).nds"))
romK = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen Ten (K).nds"))

CHANGED = ["battle.NFP","btlnameplate.NFP","cardname_l.NFP","cardname_s.NFP",
           "commonfile.NFP","scenario.NFP","senryakumode.NFP","SPC.NFP",
           "sysmenu.NFP","trickname.NFP"]

def get(rom, p):
    return bytes(rom.files[rom.filenames.idOf(p)])

# 인코딩 후보별 한글 검출기
def scan_encoding(d, label):
    res = {}
    # CP949 (EUC-KR 확장): 리드 0x81-0xC8, 완성형 0xB0A1-0xC8FE 중심
    cp949 = re.compile(rb"(?:[\xb0-\xc8][\xa1-\xfe]){2,}")
    hits = cp949.findall(d)
    ok = []
    for h in hits[:2000]:
        try:
            s = h.decode("cp949")
            if all("가" <= c <= "힣" for c in s): ok.append(s)
        except: pass
    res["cp949"] = ok
    # UTF-16LE 한글
    u16 = re.compile(rb"(?:[\x00-\xff][\xac-\xd7]){2,}")
    hits = u16.findall(d)
    ok = []
    for h in hits[:2000]:
        try:
            s = h.decode("utf-16le")
            if all("가" <= c <= "힣" for c in s): ok.append(s)
        except: pass
    res["utf16"] = ok
    # UTF-8 한글
    u8 = re.compile(rb"(?:\xea[\xb0-\xbf][\x80-\xbf]|\xeb[\x80-\xbf][\x80-\xbf]|\xec[\x80-\x9f][\x80-\xbf]){2,}")
    hits = u8.findall(d)
    ok = []
    for h in hits[:2000]:
        try: ok.append(h.decode("utf-8"))
        except: pass
    res["utf8"] = ok
    for enc, lst in res.items():
        if lst:
            print(f"  [{label}] {enc}: {len(lst)} hits  e.g. {lst[:6]}")
    return res

for p in CHANGED:
    dK = get(romK, p)
    dJ = get(romJ, p)
    print(f"=== {p} (J={len(dJ)} K={len(dK)}) ===")
    scan_encoding(dK, "K")
    # RTFN(폰트) 매직 검색
    for tag in (b"RTFN", b"NFTR"):
        idxs = [m.start() for m in re.finditer(re.escape(tag), dK)]
        if idxs: print(f"  font magic {tag} in K at {[hex(i) for i in idxs[:5]]}")
        idxsJ = [m.start() for m in re.finditer(re.escape(tag), dJ)]
        if idxsJ: print(f"  font magic {tag} in J at {[hex(i) for i in idxsJ[:5]]}")
