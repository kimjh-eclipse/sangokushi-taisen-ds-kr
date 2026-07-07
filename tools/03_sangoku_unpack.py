# -*- coding: utf-8 -*-
# SANGOKU.NFP (NFP2.0) 테이블 파싱 + 확장자별 분류
import ndspy.rom, struct, os, collections, json

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))
sang = bytes(rom.files[rom.filenames.idOf("SANGOKU.NFP")])

cnt, tbl, dat = struct.unpack_from("<III", sang, 0x34)
entries = []
for i in range(cnt):
    off = tbl + i * 16
    name = sang[off:off+12].split(b"\0")[0].decode("ascii", "replace")
    foff, = struct.unpack_from("<I", sang, off + 12)
    entries.append([name, foff])
# 크기 = 다음 오프셋 - 현재 오프셋 (마지막은 파일 끝)
for i, e in enumerate(entries):
    end = entries[i+1][1] if i + 1 < cnt else len(sang)
    e.append(end - e[1])

# 확장자별 통계
by_ext = collections.Counter()
size_by_ext = collections.Counter()
for name, off, sz in entries:
    ext = name.rsplit(".", 1)[-1] if "." in name else "(none)"
    by_ext[ext] += 1
    size_by_ext[ext] += sz
print("ext        count   total_bytes")
for ext, c in by_ext.most_common():
    print(f"{ext:<10} {c:>5}   {size_by_ext[ext]:>12,}")

# 테이블 저장
with open(os.path.join(BASE, "work", "sangoku_toc.json"), "w", encoding="utf-8") as f:
    json.dump(entries, f, ensure_ascii=False)

# 오프셋 단조증가 검증
bad = [i for i in range(1, cnt) if entries[i][1] < entries[i-1][1]]
print(f"\nnon-monotonic offsets: {len(bad)}")
print(f"first entry: {entries[0]}, last: {entries[-1]}")
print(f"data start check: table says 0x{dat:x}, first file off 0x{entries[0][1]:x}")

# 텍스트 후보 확장자 미리보기: 각 확장자 첫 파일의 헤더 16바이트
seen = set()
print("\n--- first file per ext, magic ---")
for name, off, sz in entries:
    ext = name.rsplit(".", 1)[-1]
    if ext in seen: continue
    seen.add(ext)
    print(f"{name:<14} sz={sz:>9,}  head={sang[off:off+16].hex()}  ascii={''.join(chr(b) if 32<=b<127 else '.' for b in sang[off:off+16])}")
