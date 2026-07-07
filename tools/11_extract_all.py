# -*- coding: utf-8 -*-
# 번역 대상 전량 추출:
#  - scenario.sar: 엔트리별 문자열 풀 파싱 (구조 검증 포함)
#  - DAT: CARDS/CARDS2/ITEM/TACTICS/TRICKS 텍스트 필드
#  - arm9: SJIS 문자열 (오프셋 기록, 인플레이스 교체용)
import struct, os, sys, re, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import ndspy.rom

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
WORK = os.path.join(BASE, "work")
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))

# ---------- scenario.sar ----------
sar = bytes(rom.files[rom.filenames.idOf("scenario.sar")])
n = struct.unpack_from("<I", sar, 0)[0] // 8
entries = [struct.unpack_from("<II", sar, i*8) for i in range(n)]

sar_data = []
total_strs = 0
for ei, (off, sz) in enumerate(entries):
    if sz == 0:
        sar_data.append(None); continue
    scriptSz, textSz = struct.unpack_from("<II", sar, off)
    assert scriptSz + textSz == sz, (ei, hex(scriptSz), hex(textSz), hex(sz))
    script = sar[off+8 : off+scriptSz]          # scriptSz는 8바이트 헤더 포함
    pool   = sar[off+scriptSz : off+scriptSz+textSz]
    # 풀에서 NUL 종단 문자열 추출
    strs = []
    p = 0
    while p < len(pool):
        q = pool.find(b"\0", p)
        if q < 0: q = len(pool)
        raw = pool[p:q]
        strs.append((p, raw))
        p = q + 1
    # 스크립트에서 0x81 플래그 포인터 수집
    ptrs = set()
    for i in range(0, len(script) - 3):
        v, = struct.unpack_from("<I", script, i)
        if (v >> 24) == 0x81 and (v & 0xFFFFFF) < textSz:
            ptrs.add(v & 0xFFFFFF)
    starts = {s[0] for s in strs}
    orphan = ptrs - starts   # 문자열 시작이 아닌 곳을 가리키는 포인터(정렬문제 확인용)
    sar_data.append({
        "entry": ei, "off": off, "scriptSz": scriptSz, "textSz": textSz,
        "strings": [(p, raw.decode("shift_jis", "replace")) for p, raw in strs],
        "ptr_hits": len(ptrs & starts), "orphan_ptrs": sorted(orphan)[:10],
    })
    total_strs += len(strs)

valid = [e for e in sar_data if e]
print(f"sar entries={n} non-empty={len(valid)} total strings={total_strs}")
print("orphan ptr entries:", [(e['entry'], len(e['orphan_ptrs'])) for e in valid if e['orphan_ptrs']][:20])
print("sample entry0 strings:")
for p, s in valid[0]["strings"][:6]:
    print(f"  @0x{p:x}: {s}")

json.dump(sar_data, open(os.path.join(WORK, "sar_strings.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)

# ---------- DAT ----------
sang = bytes(rom.files[rom.filenames.idOf("SANGOKU.NFP")])
toc = json.load(open(os.path.join(WORK, "sangoku_toc.json"), encoding="utf-8"))
files = {name: (off, sz) for name, off, sz in toc}
for datname in ("CARDS.DAT", "CARDS2.DAT", "ITEM.DAT", "TACTICS.DAT", "TRICKS.DAT", "SLGTYPES.DAT"):
    off, sz = files[datname]
    open(os.path.join(WORK, datname), "wb").write(sang[off:off+sz])
    print(f"dumped {datname} {sz}B")

# ---------- arm9 ----------
a9 = bytes(rom.arm9)
pat = re.compile(rb"(?:[\x81-\x9f\xe0-\xef][\x40-\xfc]|[\x20-\x7e]|[\xa1-\xdf]){2,}")
arm9_strs = []
for m in pat.finditer(a9):
    raw = m.group()
    try: s = raw.decode("shift_jis")
    except: continue
    # 일본어 문자 포함 문자열만
    if any("぀" <= c <= "ヿ" or "一" <= c <= "鿿" or c in "、。！？「」『』・ー" for c in s):
        # NUL 종단 확인
        end = m.end()
        arm9_strs.append({"off": m.start(), "len": len(raw),
                          "nul": end < len(a9) and a9[end] == 0, "text": s})
print(f"\narm9 JP strings: {len(arm9_strs)}")
json.dump(arm9_strs, open(os.path.join(WORK, "arm9_strings.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
# 미리보기: 진짜 텍스트로 보이는 것 (가나 포함, 길이 4+)
real = [x for x in arm9_strs if len(x["text"]) >= 4 and any("ぁ" <= c <= "ヿ" for c in x["text"])]
print(f"arm9 likely-real (kana, len>=4): {len(real)}")
for x in real[:15]: print(f"  0x{x['off']:x}: {x['text'][:60]}")
