# -*- coding: utf-8 -*-
# ST_FONT.SCM.dec 구조 분석: 코드 테이블/글리프 탐색
import os, sys, struct, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"
d = open(os.path.join(WORK, "ST_FONT.SCM.dec"), "rb").read()
print(f"size={len(d)} (0x{len(d):x})")

# 증가하는 u16 시퀀스 찾기 (SJIS 코드 테이블)
best = []
i = 0
while i < len(d) - 4:
    j = i
    prev = None
    cnt = 0
    while j < len(d) - 2:
        v, = struct.unpack_from("<H", d, j)
        if prev is not None and not (0 < v - prev <= 0x60):
            break
        if not (0x8100 <= v <= 0xFCFF or 0x20 <= v <= 0xFF):
            break
        prev = v; cnt += 1; j += 2
    if cnt >= 30:
        best.append((i, cnt, struct.unpack_from("<H", d, i)[0]))
        i = j
    else:
        i += 2 if cnt else 1  # hmm slow; step 1 needed for alignment
print("increasing u16 runs (>=30):")
for off, cnt, first in best[:20]:
    vals = struct.unpack_from(f"<{min(cnt,8)}H", d, off)
    print(f"  0x{off:x}: n={cnt} first={[hex(v) for v in vals]}")

# 값 분포: 0x00 비율로 데이터 영역 추정 (글리프 비트맵은 밀도 있음)
zeros = collections.Counter()
CH = 0x1000
for base in range(0, len(d), CH):
    blk = d[base:base+CH]
    zeros[base] = blk.count(0) / len(blk)
print("\nzero-ratio per 4KB block (first 40):")
print(" ".join(f"{zeros[b]:.2f}" for b in sorted(zeros)[:40]))
