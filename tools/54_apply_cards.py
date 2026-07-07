# -*- coding: utf-8 -*-
# cd_out/*.json 카드 번역을 각 DAT에 적용 → work/에 {DAT}.kr 생성
# ITEM.DAT col31(독음: 정렬용 추정)은 제외.
import os, sys, json, glob
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import dat, korean

WORK = r"C:\Emul\Switch\패치유틸.xdeltaUI\work"
EXCLUDE = {("ITEM.DAT", 31)}   # 독음 필드 제외(오십음 정렬 보호)

# 파일별 번역 맵 수집
per_file = {}
for f in glob.glob(os.path.join(WORK, "cd_out", "*.json")):
    base = os.path.basename(f)               # 예 CARDS2.DAT.name.json
    datname = base.split(".DAT")[0] + ".DAT"
    m = json.load(open(f, encoding="utf-8"))
    d = per_file.setdefault(datname, {})
    for key, ko in m.items():
        r, c = key.split("_")
        r, c = int(r), int(c)
        if (datname, c) in EXCLUDE:
            continue
        d[(r, c)] = ko

for datname, tmap in per_file.items():
    src = os.path.join(WORK, datname)
    outp = os.path.join(WORK, datname + ".kr")
    try:
        n = dat.apply_map(src, outp, tmap, encode_fn=korean.encode)
        raw = open(outp, "rb").read()
        print(f"{datname}: {n}셀 적용 -> {datname}.kr ({len(raw)}B)")
    except Exception as e:
        print(f"{datname}: 오류 {e}")
