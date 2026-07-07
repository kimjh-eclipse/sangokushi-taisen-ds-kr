# -*- coding: utf-8 -*-
# 세 ROM의 파일시스템 목록화 + 천(J) vs 천(K) diff
import ndspy.rom, hashlib, os, json

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
ROMS = {
    "ten_j": "San Goku Shi Taisen Ten (J).nds",
    "ten_k": "San Goku Shi Taisen Ten (K).nds",
    "sgst_j": "San Goku Shi Taisen (J).nds",
}

def walk(rom):
    out = {}
    def rec(folder, prefix):
        for fname in folder.files:
            fid = folder.firstID + folder.files.index(fname)
            yield prefix + fname, fid
        for sub_name, sub in folder.folders:
            yield from rec(sub, prefix + sub_name + "/")
    for path, fid in rec(rom.filenames, ""):
        data = rom.files[fid]
        out[path] = (len(data), hashlib.md5(data).hexdigest())
    return out

info = {}
for key, fn in ROMS.items():
    rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, fn))
    fs = walk(rom)
    info[key] = fs
    print(f"[{key}] title={rom.name!r} code={rom.idCode!r} files={len(fs)}")

# 천 J vs K diff
tj, tk = info["ten_j"], info["ten_k"]
changed = [p for p in tj if p in tk and tj[p][1] != tk[p][1]]
same    = [p for p in tj if p in tk and tj[p][1] == tk[p][1]]
only_j  = [p for p in tj if p not in tk]
only_k  = [p for p in tk if p not in tj]
print(f"\n=== Ten J vs K: changed={len(changed)} same={len(same)} onlyJ={len(only_j)} onlyK={len(only_k)}")
for p in changed:
    print(f"  CHANGED {p}  J={tj[p][0]}  K={tk[p][0]}")

# 전작 파일 목록
print(f"\n=== SGST(J) files: {len(info['sgst_j'])}")
for p, (sz, h) in sorted(info["sgst_j"].items()):
    print(f"  {p}  {sz}")

# 전작과 천(J)의 동일 파일(해시 일치)
tenj_by_hash = {}
for p, (sz, h) in tj.items():
    tenj_by_hash.setdefault(h, []).append(p)
print("\n=== SGST(J) files identical to Ten(J):")
for p, (sz, h) in sorted(info["sgst_j"].items()):
    if h in tenj_by_hash:
        print(f"  {p} == Ten:{tenj_by_hash[h]}")

with open(os.path.join(BASE, "work", "fs_info.json"), "w", encoding="utf-8") as f:
    json.dump(info, f, ensure_ascii=False, indent=1)
