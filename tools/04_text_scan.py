# -*- coding: utf-8 -*-
# 텍스트 보유 파일 탐색: DAT/TXT 내용 확인 + SCM 내 Shift-JIS 문자열 스캔
import ndspy.rom, struct, os, json, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = r"C:\Emul\Switch\패치유틸.xdeltaUI"
rom = ndspy.rom.NintendoDSRom.fromFile(os.path.join(BASE, "San Goku Shi Taisen (J).nds"))
sang = bytes(rom.files[rom.filenames.idOf("SANGOKU.NFP")])
toc = json.load(open(os.path.join(BASE, "work", "sangoku_toc.json"), encoding="utf-8"))
files = {name: (off, sz) for name, off, sz in toc}

def get(name):
    off, sz = files[name]
    return sang[off:off+sz]

# 1) DAT/TXT 파일 목록과 첫 줄들
for name, off, sz in toc:
    if name.endswith((".DAT", ".TXT")):
        d = sang[off:off+sz]
        try:
            txt = d.decode("shift_jis", "replace")
        except Exception:
            txt = "(decode fail)"
        lines = txt.splitlines()
        print(f"=== {name} ({sz}B, {len(lines)} lines) ===")
        for l in lines[:8]:
            print("   ", l[:110])
        print()

# 2) SCM 파일에서 Shift-JIS 한자/가나 문자열 스캔 (샘플 몇 개 + 전체 통계)
sjis_run = re.compile(rb"(?:[\x81-\x9f\xe0-\xef][\x40-\xfc]){3,}")
total_hits = 0
scm_with_text = []
for name, off, sz in toc:
    if not name.endswith(".SCM"): continue
    d = sang[off:off+sz]
    hits = sjis_run.findall(d)
    good = []
    for h in hits:
        try:
            s = h.decode("shift_jis")
            if any("぀" <= c <= "ヿ" or "一" <= c <= "鿿" for c in s):
                good.append(s)
        except Exception:
            pass
    if good:
        scm_with_text.append((name, len(good), good[:3]))
        total_hits += len(good)

print(f"SCM files with SJIS text: {len(scm_with_text)}, total strings: {total_hits}")
for name, n, samples in scm_with_text[:25]:
    print(f"  {name}: {n} strs  e.g. {samples}")
